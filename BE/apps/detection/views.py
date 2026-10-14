from django.db import transaction
from django.db.models import Avg, Count, Q
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

from .inference import DetectorUnavailable, get_detector
from .models import Detection, DetectionItem, ModelVersion, Photo

MAX_UPLOAD_MB = 10


def _items_payload(request, detection: Detection):
    target = resolve_target(request)
    items = list(detection.items.all())
    labels = {i.label for i in items}
    words = {w.yolo_label: w for w in words_for_target(Word.objects.filter(yolo_label__in=labels), request.user, target)}
    personal = personal_map(request.user, [w.id for w in words.values()], target)
    out = []
    for it in items:
        w = words.get(it.label)
        out.append({
            "id": it.id, "label": it.label, "confidence": round(it.confidence, 4), "bbox": it.bbox, "top_k": it.top_k,
            "selected": it.selected, "feedback": it.feedback,
            "card": card(w, target, personal.get(w.id), request) if w else None,
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
        upload.seek(0)
        with transaction.atomic():
            photo = Photo.objects.create(user=request.user, image=upload, width=img.width, height=img.height,
                                         source=ser.validated_data["source"])
            det = Detection.objects.create(user=request.user, photo=photo, model_name=detector.name,
                                           model_version=ModelVersion.objects.filter(is_active=True).first(),
                                           device=Detection.Device.SERVER, inference_ms=ms)
            DetectionItem.objects.bulk_create([
                DetectionItem(detection=det, label=b.label, confidence=b.confidence, bbox=b.bbox, top_k=b.top_k)
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


class ConfirmSerializer(serializers.Serializer):
    items = ConfirmItemSerializer(many=True)
    topic = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all(), required=False, allow_null=True)


@extend_schema(tags=["detection"])
class DetectionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = LogDetectionSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Detection.objects.none()
        return Detection.objects.filter(user=self.request.user).select_related("photo").prefetch_related("items")

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        return self.get_paginated_response([_items_payload(request, d) for d in page])

    def retrieve(self, request, *args, **kwargs):
        return Response(_items_payload(request, self.get_object()))

    @extend_schema(request=LogDetectionSerializer)
    @action(detail=False, methods=["post"])
    def log(self, request):
        """Store a result computed on the phone (TFLite) so it also feeds statistics and VIP."""
        ser = LogDetectionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        with transaction.atomic():
            photo = None
            if request.FILES.get("image"):
                img = Image.open(request.FILES["image"])
                request.FILES["image"].seek(0)
                photo = Photo.objects.create(user=request.user, image=request.FILES["image"], width=img.width, height=img.height)
            det = Detection.objects.create(user=request.user, photo=photo, model_name=d["model_name"],
                                           device=Detection.Device.ON_DEVICE, inference_ms=d.get("inference_ms"))
            DetectionItem.objects.bulk_create([
                DetectionItem(detection=det, label=i["label"], confidence=i["confidence"], bbox=i["bbox"],
                              top_k=i.get("top_k") or [{"label": i["label"], "confidence": i["confidence"]}])
                for i in d["items"]
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
        saved = 0
        items = {i.id: i for i in det.items.all()}
        with transaction.atomic():
            for c in ser.validated_data["items"]:
                it = items.get(c["id"])
                if it is None:
                    continue
                it.selected, it.feedback = c["selected"], c["feedback"]
                it.corrected_label = c.get("corrected_label", "")
                it.save(update_fields=["selected", "feedback", "corrected_label"])
                if it.selected and it.word_id and it.feedback != "wrong":
                    _, created = PersonalWord.objects.get_or_create(
                        user=request.user, word_id=it.word_id, language=target.learn,
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
        return Response({"saved": saved, **_items_payload(request, det)})


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
