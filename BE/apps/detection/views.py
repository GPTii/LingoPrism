from django.db import transaction
from django.db.models import Avg, Count, Q
from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from PIL import Image
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsStaffRole
from apps.gamification import services as game
from apps.learning.models import PersonalWord
from apps.vocab.models import Topic, Word
from apps.vocab.services import card, personal_map, resolve_target, words_for_target
from apps.core.throttles import ActionThrottleMixin

from . import memory
from .inference import Box, DetectorUnavailable, get_detector
from .models import CorrectionMemory, Detection, DetectionItem, ModelVersion, Photo

MAX_UPLOAD_MB = 10
UNSURE_BELOW = 0.6  # below this the learner is asked "is it: A / B / C?" instead of being told one word
# a label learners often mark wrong is always asked about, whatever the confidence (per-class threshold from feedback)
OFTEN_WRONG_MIN_FEEDBACK, OFTEN_WRONG_RATE = 5, 0.3


def _often_wrong(labels) -> set[str]:
    rows = DetectionItem.objects.filter(label__in=labels).exclude(feedback="unknown").values("label").annotate(
        n=Count("id"), wrong=Count("id", filter=Q(feedback="wrong")))
    return {r["label"] for r in rows if r["n"] >= OFTEN_WRONG_MIN_FEEDBACK and r["wrong"] / r["n"] >= OFTEN_WRONG_RATE}


def _items_payload(request, detection: Detection):
    target = resolve_target(request)
    items = list(detection.items.all())
    labels = {i.label for i in items} | {t["label"] for i in items for t in (i.top_k or [])}
    labels |= {i.corrected_label for i in items if i.corrected_label}
    words = {w.yolo_label: w for w in words_for_target(Word.objects.filter(yolo_label__in=labels), request.user, target)}
    personal = personal_map(request.user, [w.id for w in words.values()], target)
    often_wrong = _often_wrong({i.label for i in items})
    out = []
    for it in items:
        w = words.get(it.label)
        alternatives = []
        for t in it.top_k or []:
            aw = words.get(t["label"])
            if t["label"] != it.label and aw and t["label"] not in {a["label"] for a in alternatives}:
                alternatives.append({"label": t["label"], "confidence": t["confidence"],
                                     "card": card(aw, target, personal.get(aw.id), request)})
        cw = words.get(it.corrected_label) if it.corrected_label else None
        out.append({
            "id": it.id, "label": it.label, "confidence": round(it.confidence, 4), "bbox": it.bbox, "top_k": it.top_k,
            "selected": it.selected, "feedback": it.feedback, "corrected_label": it.corrected_label,
            "uncertain": (it.confidence < UNSURE_BELOW and bool(alternatives)) or it.label in often_wrong,
            "learned": it.learned_from_id is not None,  # relabelled from an earlier learner's error report
            "not_object": it.feedback == "wrong" and not it.corrected_label and hasattr(it, "report"),
            "card": card(w, target, personal.get(w.id), request) if w else None,
            "alternatives": alternatives,
            "corrected_card": card(cw, target, personal.get(cw.id), request) if cw else None,
        })
    return {
        "id": detection.id, "model": detection.model_name, "device": detection.device, "inference_ms": detection.inference_ms,
        "image": request.build_absolute_uri(detection.photo.image.url) if detection.photo and detection.photo.image else None,
        "created_at": detection.created_at, "confirmed": detection.confirmed, "items": out,
    }


def _link_words(detection: Detection):
    labels = set(detection.items.values_list("label", flat=True))
    by_label = dict(Word.objects.filter(yolo_label__in=labels).values_list("yolo_label", "id"))
    for it in detection.items.all():
        if it.label in by_label:
            it.word_id = by_label[it.label]
            it.save(update_fields=["word"])


class DetectUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()
    source = serializers.ChoiceField(choices=Photo.Source.choices, default="camera")


class DetectView(APIView):
    """Upload a photo → YOLOv10 on the server → objects + vocabulary cards."""

    parser_classes = [MultiPartParser, FormParser]
    throttle_scope = "detect"

    @extend_schema(tags=["detection"], request={"multipart/form-data": DetectUploadSerializer}, responses={200: dict})
    def post(self, request):
        ser = DetectUploadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        upload = ser.validated_data["image"]
        if upload.size > MAX_UPLOAD_MB * 1024 * 1024:
            return Response({"detail": f"Ảnh tối đa {MAX_UPLOAD_MB} MB", "errors": {}}, status=400)
        try:
            detector = get_detector()
        except DetectorUnavailable as e:
            return Response({"detail": str(e), "errors": {}}, status=503)
        img = Image.open(upload)
        boxes, ms = detector.predict(img)
        boxes = memory.apply(request.user, img, boxes)
        upload.seek(0)
        with transaction.atomic():
            photo = Photo.objects.create(user=request.user, image=upload, width=img.width, height=img.height,
                                         source=ser.validated_data["source"])
            det = Detection.objects.create(user=request.user, photo=photo, model_name=detector.name,
                                           model_version=ModelVersion.objects.filter(is_active=True).first(),
                                           device=Detection.Device.SERVER, inference_ms=ms)
            DetectionItem.objects.bulk_create([
                DetectionItem(detection=det, label=b.label, confidence=b.confidence, bbox=b.bbox, top_k=b.top_k,
                              learned_from_id=b.memory_id)
                for b in boxes
            ])
            _link_words(det)
        return Response(_items_payload(request, det))


class LogItemSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=60)
    confidence = serializers.FloatField(min_value=0, max_value=1)
    bbox = serializers.ListField(child=serializers.FloatField(), min_length=4, max_length=4)
    top_k = serializers.ListField(child=serializers.DictField(), required=False)


class LogDetectionSerializer(serializers.Serializer):
    model_name = serializers.CharField(max_length=60)
    inference_ms = serializers.IntegerField(required=False, min_value=0)
    items = LogItemSerializer(many=True)


class ConfirmItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    selected = serializers.BooleanField(default=False)
    feedback = serializers.ChoiceField(choices=DetectionItem.Feedback.choices, default="unknown")
    corrected_label = serializers.CharField(required=False, allow_blank=True, max_length=60)
    not_object = serializers.BooleanField(default=False, help_text="Báo lỗi: chỗ này không phải đồ vật nào")


class ConfirmSerializer(serializers.Serializer):
    items = ConfirmItemSerializer(many=True)
    topic = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all(), required=False, allow_null=True)


@extend_schema(tags=["detection"])
class DetectionViewSet(ActionThrottleMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    throttle_scopes = {"log": "detect"}
    serializer_class = LogDetectionSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Detection.objects.none()
        return Detection.objects.filter(user=self.request.user).select_related("photo").prefetch_related("items")

    def list(self, request, *args, **kwargs):
        """The learner's photos, newest first. `?confirmed=1` only the ones they saved words from, `0` the others."""
        qs = self.get_queryset()
        if request.query_params.get("confirmed") in ("0", "1"):
            qs = qs.filter(confirmed=request.query_params["confirmed"] == "1")
        page = self.paginate_queryset(qs)
        return self.get_paginated_response([_items_payload(request, d) for d in page])

    def retrieve(self, request, *args, **kwargs):
        return Response(_items_payload(request, self.get_object()))

    @action(detail=False, methods=["get"])
    def labels(self, request):
        """Every object the detector knows, with its word card – the list for "it is something else"."""
        target = resolve_target(request)
        words = words_for_target(Word.objects.exclude(yolo_label="").exclude(yolo_label__isnull=True), request.user, target)
        return Response(sorted(({"label": w.yolo_label, "card": card(w, target, None, request)} for w in words),
                               key=lambda r: r["card"].get("meaning_vi") or r["label"]))

    @extend_schema(request=LogDetectionSerializer)
    @action(detail=False, methods=["post"])
    def log(self, request):
        """Store a result computed on the phone (TFLite) so it also feeds statistics and VIP."""
        ser = LogDetectionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        with transaction.atomic():
            photo = None
            boxes = [Box(i["label"], i["confidence"], i["bbox"],
                         i.get("top_k") or [{"label": i["label"], "confidence": i["confidence"]}]) for i in d["items"]]
            if request.FILES.get("image"):
                img = Image.open(request.FILES["image"])
                boxes = memory.apply(request.user, img, boxes)
                request.FILES["image"].seek(0)
                photo = Photo.objects.create(user=request.user, image=request.FILES["image"], width=img.width, height=img.height)
            det = Detection.objects.create(user=request.user, photo=photo, model_name=d["model_name"],
                                           device=Detection.Device.ON_DEVICE, inference_ms=d.get("inference_ms"))
            DetectionItem.objects.bulk_create([
                DetectionItem(detection=det, label=b.label, confidence=b.confidence, bbox=b.bbox, top_k=b.top_k,
                              learned_from_id=b.memory_id)
                for b in boxes
            ])
            _link_words(det)
        return Response(_items_payload(request, det), status=201)

    @extend_schema(request=ConfirmSerializer)
    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """User picks the words to save and tells us which detections were right or wrong."""
        det = self.get_object()
        ser = ConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        target = resolve_target(request)
        saved = reported = 0
        items = {i.id: i for i in det.items.all()}  # the prefetched instances: the response reads them back
        corrected = {c.get("corrected_label") for c in ser.validated_data["items"]} - {None, ""}
        word_by_label = dict(Word.objects.filter(yolo_label__in=corrected).values_list("yolo_label", "id"))
        with transaction.atomic():
            for c in ser.validated_data["items"]:
                it = items.get(c["id"])
                if it is None:
                    continue
                was_wrong = it.feedback == DetectionItem.Feedback.WRONG
                it.selected, it.feedback = c["selected"], c["feedback"]
                it.corrected_label = c.get("corrected_label", "")
                if c["not_object"]:  # error report: there is no such object here
                    it.corrected_label, it.feedback, it.selected = "", DetectionItem.Feedback.WRONG, False
                elif it.corrected_label == it.label:  # learner confirmed the model's own answer
                    it.corrected_label, it.feedback = "", DetectionItem.Feedback.CORRECT
                elif it.corrected_label:  # learner picked another object: the model was wrong, save that word
                    it.feedback = DetectionItem.Feedback.WRONG
                it.save(update_fields=["selected", "feedback", "corrected_label"])
                if it.feedback == DetectionItem.Feedback.WRONG and (it.corrected_label or c["not_object"]):
                    reported += memory.remember(it, request.user)
                    if it.learned_from_id and not was_wrong:
                        memory.dispute(it.learned_from)
                word_id = word_by_label.get(it.corrected_label) if it.corrected_label else (
                    it.word_id if it.feedback != "wrong" else None)
                if it.selected and word_id:
                    _, created = PersonalWord.objects.get_or_create(
                        user=request.user, word_id=word_id, language=target.learn,
                        defaults={"source": PersonalWord.Source.CAMERA, "source_ref": str(det.id),
                                  "topic": ser.validated_data.get("topic")})
                    saved += created
            first_time = not det.confirmed
            det.confirmed = True
            det.save(update_fields=["confirmed"])
        if first_time:
            game.bump_stat(request.user, "detections")
            game.mark_activity(request.user)
            game.award_xp(request.user, "camera", 5 + 2 * saved, source_id=str(det.id), note="Nhận diện ảnh")
        return Response({"saved": saved, "reported": reported, **_items_payload(request, det)})


# ------------------------------------------------------------------ admin

class ModelVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelVersion
        fields = "__all__"


@extend_schema(tags=["admin-detection"])
class AdminModelVersionViewSet(viewsets.ModelViewSet):
    serializer_class = ModelVersionSerializer
    permission_classes = [IsStaffRole]
    queryset = ModelVersion.objects.order_by("-created_at")

    def perform_save(self, serializer):
        mv = serializer.save()
        if mv.is_active:
            ModelVersion.objects.exclude(pk=mv.pk).update(is_active=False)

    perform_create = perform_save
    perform_update = perform_save


@extend_schema(tags=["admin-detection"])
class AdminDetectionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ModelVersionSerializer
    permission_classes = [IsStaffRole]
    queryset = Detection.objects.select_related("user", "photo").prefetch_related("items").order_by("-created_at")
    filterset_fields = ["device", "model_name", "confirmed"]

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        return self.get_paginated_response([
            {"id": d.id, "user": d.user.email, "model": d.model_name, "device": d.device, "inference_ms": d.inference_ms,
             "image": request.build_absolute_uri(d.photo.image.url) if d.photo and d.photo.image else None,
             "created_at": d.created_at,
             "items": [{"label": i.label, "confidence": round(i.confidence, 3), "feedback": i.feedback,
                        "corrected_label": i.corrected_label} for i in d.items.all()]}
            for d in page
        ])

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Per-label statistics + confusion pairs (detected label → label corrected by the user). Input for VIP."""
        per_label = DetectionItem.objects.values("label").annotate(
            count=Count("id"), avg_confidence=Avg("confidence"),
            wrong=Count("id", filter=Q(feedback="wrong")), correct=Count("id", filter=Q(feedback="correct")),
        ).order_by("-count")
        confusion = DetectionItem.objects.filter(feedback="wrong").exclude(corrected_label="").values(
            "label", "corrected_label").annotate(count=Count("id")).order_by("-count")[:50]
        by_device = Detection.objects.values("device").annotate(count=Count("id"), avg_ms=Avg("inference_ms"))
        return Response({"per_label": list(per_label), "confusion": list(confusion), "by_device": list(by_device)})


# ------------------------------------------------------------------ admin: error reports

def _report_row(request, m: CorrectionMemory, same: dict):
    return {
        "id": m.id, "user": m.user.email, "wrong_label": m.wrong_label, "correct_label": m.correct_label,
        "status": m.status, "disputes": m.disputes, "applied": m.applied.count(),
        "same_reports": same.get((m.wrong_label, m.correct_label), 1),
        "crop": request.build_absolute_uri(m.crop.url) if m.crop else None,
        "photo": request.build_absolute_uri(m.item.detection.photo.image.url)
        if m.item.detection.photo and m.item.detection.photo.image else None,
        "reviewed_by": m.reviewed_by.email if m.reviewed_by else None, "exported_at": m.exported_at,
        "created_at": m.created_at,
    }


@extend_schema(tags=["admin-detection"])
class AdminCorrectionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Learners' detection error reports (correction memory): review, then export as training data."""

    serializer_class = ModelVersionSerializer
    permission_classes = [IsStaffRole]
    queryset = CorrectionMemory.objects.select_related("user", "reviewed_by", "item__detection__photo").order_by(
        "-created_at")
    filterset_fields = ["status", "wrong_label", "correct_label"]

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        same = {(r["wrong_label"], r["correct_label"]): r["n"] for r in CorrectionMemory.objects.exclude(
            status="rejected").values("wrong_label", "correct_label").annotate(n=Count("user", distinct=True))}
        return self.get_paginated_response([_report_row(request, m, same) for m in page])

    def _review(self, request, status):
        m = self.get_object()
        m.status, m.reviewed_by, m.reviewed_at = status, request.user, timezone.now()
        m.save(update_fields=["status", "reviewed_by", "reviewed_at"])
        return Response({"id": m.id, "status": m.status})

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._review(request, CorrectionMemory.Status.APPROVED)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._review(request, CorrectionMemory.Status.REJECTED)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        qs = CorrectionMemory.objects
        return Response({
            "pending": qs.filter(status="pending").count(), "approved": qs.filter(status="approved").count(),
            "rejected": qs.filter(status="rejected").count(),
            "approved_not_exported": qs.filter(status="approved", exported_at__isnull=True).count(),
            "applied": DetectionItem.objects.filter(learned_from__isnull=False).count(),
            "memory_enabled": memory.available(), "consensus_users": memory.CONSENSUS_USERS,
        })

    @action(detail=False, methods=["get"])
    def export(self, request):
        """Approved reports → zip in YOLO format (merge into the next training run: AI/scripts/merge_feedback.py)."""
        from .training_export import build_feedback_zip

        data, n_photos = build_feedback_zip()
        if not n_photos:
            return Response({"detail": "Chưa có báo lỗi nào được duyệt", "errors": {}}, status=400)
        CorrectionMemory.objects.filter(status="approved", exported_at__isnull=True).update(exported_at=timezone.now())
        resp = HttpResponse(data, content_type="application/zip")
        resp["Content-Disposition"] = f'attachment; filename="lingoprism_feedback_{timezone.now():%Y%m%d}.zip"'
        return resp
