from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.core.permissions import IsStaffRole
from apps.core.throttles import ActionThrottleMixin

from . import serializers as s
from .lang import checks
from .models import ErrorReport, ExampleSentence, Language, ReviewStatus, Topic, TopicWord, Word, WordTranslation
from .services import card, personal_map, resolve_target, words_for_target

LANG_PARAMS = [
    OpenApiParameter("lang", str, description="vi | en | zh (mặc định: ngôn ngữ đang học)"),
    OpenApiParameter("script", str, description="hans | hant (tiếng Trung)"),
]


@extend_schema(tags=["vocab"])
class LanguageViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = s.LanguageSerializer
    queryset = Language.objects.all()
    pagination_class = None
    permission_classes = [permissions.AllowAny]


def _paginated_cards(view, qs, target):
    page = view.paginate_queryset(qs)
    items = page if page is not None else list(qs)
    personal = personal_map(view.request.user, [w.id for w in items], target)
    data = [card(w, target, personal.get(w.id), view.request) for w in items]
    return view.get_paginated_response(data) if page is not None else Response(data)


@extend_schema(tags=["vocab"], parameters=LANG_PARAMS)
class TopicViewSet(viewsets.ModelViewSet):
    """System topics + the learner's own topics."""

    filterset_fields = ["audience"]
    search_fields = ["name_vi", "name_en", "name_zh_hans", "name_zh_hant"]

    def get_serializer_class(self):
        return s.TopicCreateSerializer if self.action in ("create", "update", "partial_update") else s.TopicSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Topic.objects.none()
        user = self.request.user
        target = resolve_target(self.request)
        vis = Q(owner__isnull=True, visibility=Topic.Visibility.PUBLIC) | Q(owner=user)
        visible_words = Q(words__translations__language_id=target.code) & (
            Q(words__translations__status=ReviewStatus.VERIFIED) | Q(words__created_by=user)
        )
        qs = Topic.objects.filter(vis).annotate(
            word_count=Count("words", filter=visible_words, distinct=True),
            learned_count=Count(
                "words__learners",
                filter=Q(words__learners__user=user, words__learners__language=target.learn)
                & ~Q(words__learners__status="new"),
                distinct=True,
            ),
            saved_count=Count(
                "words__learners",
                filter=Q(words__learners__user=user, words__learners__language=target.learn),
                distinct=True,
            ),
        )
        qs = qs.order_by("order", "name_vi")
        if self.request.query_params.get("mine") == "1":
            qs = qs.filter(owner=user)
        if user.learner_type == "kid" and not user.is_staff_role:
            qs = qs.filter(audience__in=["all", "kid"])
        return qs

    def perform_create(self, serializer):
        base = slugify(serializer.validated_data["name_vi"]) or "topic"
        serializer.save(owner=self.request.user, slug=f"u{self.request.user.id}-{base}-{timezone.now():%H%M%S%f}"[:60])

    def _check_owner(self, topic):
        if topic.owner_id != self.request.user.id:
            raise PermissionDenied("Chỉ sửa/xoá được chủ đề của bạn")

    def perform_update(self, serializer):
        self._check_owner(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_owner(instance)
        instance.delete()

    @action(detail=True, methods=["get"])
    def words(self, request, pk=None):
        topic = self.get_object()
        target = resolve_target(request)
        qs = words_for_target(Word.objects.filter(topics=topic).order_by("topicword__order", "id"), request.user, target)
        return _paginated_cards(self, qs, target)

    @action(detail=True, methods=["post"])
    def save(self, request, pk=None):
        """Add every (visible) word of the topic to the learner's library."""
        from apps.learning.models import PersonalWord

        topic = self.get_object()
        target = resolve_target(request)
        words = words_for_target(Word.objects.filter(topics=topic), request.user, target)
        created = 0
        with transaction.atomic():
            for w in words:
                _, was_created = PersonalWord.objects.get_or_create(
                    user=request.user, word=w, language=target.learn,
                    defaults={"source": PersonalWord.Source.TOPIC, "topic": topic},
                )
                created += was_created
        return Response({"added": created, "total": len(words)})

    @action(detail=True, methods=["post", "delete"], url_path=r"words/(?P<word_id>\d+)")
    def word(self, request, pk=None, word_id=None):
        """My own topic: put a checked word in it (POST, also saved to my library) or take it out (DELETE, it stays
        in my library). The word joins the topic itself, so it shows up even if it was already in my library."""
        from apps.learning.models import PersonalWord

        topic = self.get_object()
        self._check_owner(topic)
        word = get_object_or_404(Word, pk=word_id)
        if request.method == "DELETE":
            TopicWord.objects.filter(topic=topic, word=word).delete()
            PersonalWord.objects.filter(user=request.user, word=word, topic=topic).update(topic=None)
            return Response(status=204)
        target = resolve_target(request)
        if not words_for_target(Word.objects.filter(id=word.id), request.user, target).exists():
            return Response({"detail": "Từ này chưa có bản dịch đã kiểm tra cho ngôn ngữ đang học", "errors": {}}, status=400)
        last = TopicWord.objects.filter(topic=topic).order_by("-order").values_list("order", flat=True).first() or 0
        _, added = TopicWord.objects.get_or_create(topic=topic, word=word, defaults={"order": last + 1})
        PersonalWord.objects.get_or_create(user=request.user, word=word, language=target.learn,
                                           defaults={"source": PersonalWord.Source.MANUAL, "topic": topic})
        return Response({"added": added}, status=201 if added else 200)


@extend_schema(tags=["vocab"], parameters=LANG_PARAMS)
class WordViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = s.LanguageSerializer  # responses are word cards built in services.card()
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Word.objects.none()
        target = resolve_target(self.request)
        qs = Word.objects.all()
        params = self.request.query_params
        if params.get("topic"):
            qs = qs.filter(topics__id=params["topic"])
        if params.get("search"):
            term = params["search"].strip()
            qs = qs.filter(
                Q(slug__icontains=term)
                | Q(translations__text__icontains=term, translations__language_id__in=[target.code, "vi", "en"])
            ).distinct()
        if self.request.user.learner_type == "kid" and not self.request.user.is_staff_role:
            qs = qs.filter(audience__in=["all", "kid"])
        return words_for_target(qs.order_by("slug"), self.request.user, target)

    def list(self, request, *args, **kwargs):
        return _paginated_cards(self, self.get_queryset(), resolve_target(request))

    def retrieve(self, request, *args, **kwargs):
        target = resolve_target(request)
        word = self.get_object()
        personal = personal_map(request.user, [word.id], target).get(word.id)
        return Response(card(word, target, personal, request))

    @extend_schema(parameters=[OpenApiParameter("labels", str, description="Nhãn YOLO, phân tách bằng dấu phẩy")])
    @action(detail=False, methods=["get"], url_path="by-labels")
    def by_labels(self, request):
        labels = [x.strip() for x in request.query_params.get("labels", "").split(",") if x.strip()]
        target = resolve_target(request)
        qs = words_for_target(Word.objects.filter(yolo_label__in=labels), request.user, target)
        personal = personal_map(request.user, [w.id for w in qs], target)
        return Response({w.yolo_label: card(w, target, personal.get(w.id), request) for w in qs})


@extend_schema(tags=["vocab"])
class ErrorReportViewSet(ActionThrottleMixin, mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    throttle_scopes = {"create": "report"}
    serializer_class = s.ErrorReportSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ErrorReport.objects.none()
        return ErrorReport.objects.filter(user=self.request.user)

    FLAG_THRESHOLD = 3

    def perform_create(self, serializer):
        report = serializer.save(user=self.request.user)
        tr = report.translation
        if tr and tr.status == ReviewStatus.VERIFIED and tr.verified_method != "manual":
            open_reports = ErrorReport.objects.filter(translation=tr, status=ErrorReport.Status.OPEN).values("user").distinct().count()
            if open_reports >= self.FLAG_THRESHOLD:
                tr.issues = tr.issues + [{"level": "error", "message": f"{open_reports} học viên báo lỗi"}]
                tr.mark(ReviewStatus.FLAGGED)
                tr.save()


# ================================================================== admin


@extend_schema(tags=["admin-vocab"])
class AdminTopicViewSet(viewsets.ModelViewSet):
    serializer_class = s.TopicSerializer
    permission_classes = [IsStaffRole]
    search_fields = ["name_vi", "name_en", "slug"]
    filterset_fields = ["audience", "visibility"]

    def get_queryset(self):
        return Topic.objects.filter(owner__isnull=True).annotate(word_count=Count("words", distinct=True))

    def perform_create(self, serializer):
        serializer.save(slug=slugify(self.request.data.get("slug") or serializer.validated_data.get("name_en") or "topic"))


@extend_schema(tags=["admin-vocab"])
class AdminWordViewSet(viewsets.ModelViewSet):
    serializer_class = s.AdminWordSerializer
    permission_classes = [IsStaffRole]
    search_fields = ["slug", "yolo_label", "translations__text"]
    filterset_fields = ["audience", "part_of_speech", "topics"]

    def get_queryset(self):
        qs = Word.objects.filter(created_by__isnull=True).prefetch_related("translations", "topics").annotate(
            flagged_count=Count("translations", filter=Q(translations__status=ReviewStatus.FLAGGED), distinct=True)
        )
        if self.request.query_params.get("flagged") == "1":
            qs = qs.filter(flagged_count__gt=0)
        return qs.order_by("slug").distinct()


@extend_schema(tags=["admin-vocab"])
class AdminTranslationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                              mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Review queue: flagged items, manual verification, re-running the automated checks."""

    serializer_class = s.AdminTranslationSerializer
    permission_classes = [IsStaffRole]
    filterset_fields = ["language", "status", "regional_difference"]
    search_fields = ["text", "word__slug"]
    ordering_fields = ["updated_at", "text"]

    def get_queryset(self):
        return WordTranslation.objects.select_related("word").order_by("-updated_at")

    def perform_update(self, serializer):
        # Any manual edit must be re-verified explicitly.
        tr = serializer.save()
        if "status" not in self.request.data:
            tr.mark(ReviewStatus.FLAGGED)
            tr.issues = tr.issues + [{"level": "warning", "message": "Đã sửa thủ công – cần duyệt lại"}]
            tr.save()

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        tr = self.get_object()
        tr.mark(ReviewStatus.VERIFIED, method="manual", user=request.user)
        tr.save()
        ErrorReport.objects.filter(translation=tr, status=ErrorReport.Status.OPEN).update(
            status=ErrorReport.Status.RESOLVED, handled_by=request.user, handled_at=timezone.now()
        )
        return Response(self.get_serializer(tr).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        tr = self.get_object()
        tr.mark(ReviewStatus.REJECTED)
        tr.save()
        return Response(self.get_serializer(tr).data)

    @action(detail=True, methods=["post"])
    def recheck(self, request, pk=None):
        """Re-run the automated source cross-check on the current text."""
        tr = self.get_object()
        en = tr.word.translations.filter(language_id="en").first()
        terms = [en.text] if en else [tr.word.slug.replace("-", " ")]
        is_noun = tr.word.part_of_speech == "noun"
        if tr.language_id == "zh-Hans":
            data = checks.build_zh_hans(tr.text, terms, is_noun)
        elif tr.language_id == "zh-Hant":
            data = checks.build_zh_hant(tr.text, terms, is_noun)
        elif tr.language_id == "en":
            data = checks.build_en(tr.text)
        else:
            data = checks.build_vi(tr.text)
        for f in ("ipa", "pinyin", "pinyin_numbered", "zhuyin", "measure_word", "level"):
            if data.get(f):
                setattr(tr, f, data[f])
        tr.text = data["text"]
        tr.sources = data["sources"]
        tr.issues = [{"level": "error", "message": m} for m in data["errors"]] + [
            {"level": "warning", "message": m} for m in data["warnings"]
        ]
        tr.mark(ReviewStatus.FLAGGED if data["errors"] else ReviewStatus.VERIFIED, method="auto")
        tr.save()
        from .lang import sources

        sources.moedict().save()
        return Response(self.get_serializer(tr).data)


@extend_schema(tags=["admin-vocab"])
class AdminExampleViewSet(viewsets.ModelViewSet):
    serializer_class = s.AdminExampleSerializer
    permission_classes = [IsStaffRole]
    filterset_fields = ["language", "status", "word", "source"]
    search_fields = ["text", "translation_vi", "translation_en"]
    queryset = ExampleSentence.objects.select_related("word")

    def perform_update(self, serializer):
        before = serializer.instance.status
        ex = serializer.save()
        if ex.status != before:
            # keep who overrode the automatic checks, for the audit trail
            ex.checks = {**ex.checks, "manual": {"by": self.request.user.email, "status": ex.status,
                                                 "at": timezone.now().isoformat()}}
            ex.save(update_fields=["checks"])


@extend_schema(tags=["admin-vocab"])
class AdminErrorReportViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = s.AdminErrorReportSerializer
    permission_classes = [IsStaffRole]
    filterset_fields = ["status", "reason"]
    queryset = ErrorReport.objects.select_related("user", "word", "translation")

    def perform_update(self, serializer):
        serializer.save(handled_by=self.request.user, handled_at=timezone.now())


@extend_schema(tags=["admin-vocab"])
class AdminVocabStatsView(viewsets.ViewSet):
    permission_classes = [IsStaffRole]

    @extend_schema(responses={200: dict})
    def list(self, request):
        rows = WordTranslation.objects.values("language_id", "status").annotate(n=Count("id"))
        stats = {}
        for r in rows:
            stats.setdefault(r["language_id"], {})[r["status"]] = r["n"]
        return Response({
            "words": Word.objects.filter(created_by__isnull=True).count(),
            "topics": Topic.objects.filter(owner__isnull=True).count(),
            "translations": stats,
            "open_reports": ErrorReport.objects.filter(status=ErrorReport.Status.OPEN).count(),
        })

