from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsStaffRole

from . import benchmark, experiments, vision, yolo_report
from .models import AlgorithmConfig

RUNNERS = {"benchmark": lambda: benchmark.run(apply=False), "benchmark_apply": lambda: benchmark.run(apply=True),
           "yolo": yolo_report.run, "vision": lambda: vision.build(), "srs": experiments.srs, "ga": experiments.run_ga, "vip": experiments.vip,
           "distractor": experiments.distractor, "proximity": experiments.proximity}


class ConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlgorithmConfig
        fields = ["scheduler", "review_priority", "distractor", "proximity", "desired_retention", "fsrs_weights",
                  "vip_weights", "updated_at"]
        read_only_fields = ["updated_at"]


def _choices():
    return {f: [{"value": v, "label": l} for v, l in getattr(AlgorithmConfig, c).choices]
            for f, c in (("scheduler", "Scheduler"), ("review_priority", "Priority"), ("distractor", "Distractor"),
                         ("proximity", "Proximity"))}


@extend_schema(tags=["admin-algorithms"])
class AlgorithmsView(APIView):
    """Cấu hình thuật toán đang dùng + kết quả thực nghiệm mới nhất. PATCH để đổi cấu hình."""

    permission_classes = [IsStaffRole]

    def get(self, request):
        return Response({"config": ConfigSerializer(AlgorithmConfig.get()).data, "choices": _choices(),
                         "experiments": experiments.latest()})

    def patch(self, request):
        ser = ConfigSerializer(AlgorithmConfig.get(), data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)


@extend_schema(tags=["admin-algorithms"])
class RunExperimentView(APIView):
    """Chạy lại một thực nghiệm: benchmark | yolo | vision | srs | ga | vip | distractor | proximity (benchmark không tự áp dụng)."""

    permission_classes = [IsStaffRole]

    def post(self, request, kind: str):
        if kind not in RUNNERS:
            return Response({"detail": "Không có thực nghiệm này"}, status=status.HTTP_404_NOT_FOUND)
        RUNNERS[kind]()
        return Response(experiments.latest().get(kind.removesuffix("_apply"), {}))


@extend_schema(tags=["admin-algorithms"])
class VipPreviewView(APIView):
    """Thứ tự ôn tập VIP của một học viên (các từ đến hạn) kèm từng thành phần điểm."""

    permission_classes = [IsStaffRole]

    def get(self, request):
        from apps.learning.models import PersonalWord
        from apps.vocab.models import WordTranslation

        from .vip import rank

        user_id = request.query_params.get("user")
        qs = PersonalWord.objects.filter(due_at__lte=timezone.now()).select_related("word", "user")
        if user_id:
            qs = qs.filter(user_id=user_id)
        pws = list(qs.order_by("due_at")[:300])
        vi = dict(WordTranslation.objects.filter(language_id="vi", word_id__in=[p.word_id for p in pws])
                  .values_list("word_id", "text"))
        ranked = rank(pws, AlgorithmConfig.get().vip_weights or None)
        due_order = {p.id: i + 1 for i, p in enumerate(pws)}
        return Response({"results": [
            {"word": vi.get(pw.word_id, pw.word.slug), "yolo_label": pw.word.yolo_label, "user": pw.user.display_name,
             "vip_rank": i + 1, "due_rank": due_order[pw.id], "score": s, "components": {k: round(v, 3) for k, v in c.items()}}
            for i, (pw, s, c) in enumerate(ranked[:40])]})


@extend_schema(tags=["admin-algorithms"])
class DistractorPreviewView(APIView):
    """Đáp án gây nhiễu cho một từ: ngẫu nhiên (baseline) vs Smart Distractor."""

    permission_classes = [IsStaffRole]

    def get(self, request):
        from apps.learning.questions import RandomSameTopicDistractors
        from apps.vocab.models import Word, WordTranslation
        from apps.vocab.services import Target

        from .distractor import SmartDistractors, rank_candidates

        q = (request.query_params.get("q") or "").strip()
        lang = request.query_params.get("lang", "en")
        code = {"zh": "zh-Hans"}.get(lang, lang)
        word = (Word.objects.filter(slug=q).first()
                or Word.objects.filter(translations__text__iexact=q).first())
        if not word:
            return Response({"detail": "Không tìm thấy từ"}, status=404)
        target = Target(lang if lang in ("vi", "en", "zh") else "en", code, "hans" if lang == "zh" else "")
        text = dict(WordTranslation.objects.filter(language_id=code).values_list("word_id", "text"))
        vi = dict(WordTranslation.objects.filter(language_id="vi").values_list("word_id", "text"))
        fmt = lambda w: {"text": text.get(w.id, w.slug), "vi": vi.get(w.id, "")}
        return Response({"word": fmt(word), "random": [fmt(w) for w in RandomSameTopicDistractors().pick(word, target, 3)],
                         "smart": [fmt(w) | {"score": s} for w, s in rank_candidates(word, code, 3)],
                         "smart_used": [fmt(w) for w in SmartDistractors().pick(word, target, 3)]})
