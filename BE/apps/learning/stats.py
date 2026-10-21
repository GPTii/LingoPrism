"""Thống kê học tập của chính người học (FEATURES 12.1–12.3): theo ngày, theo chủ đề, theo dạng câu hỏi
và những từ hay sai – cho ngôn ngữ đang học."""
from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.vocab.models import Word
from apps.vocab.services import card, resolve_target, words_for_target
from apps.vocab.views import LANG_PARAMS

from .models import PersonalWord, ReviewLog

QUESTION_LABELS = {
    "flashcard": "Thẻ ghi nhớ",
    "choose_target": "Chọn từ đúng",
    "choose_meaning": "Chọn nghĩa đúng",
    "choose_pinyin": "Chọn pinyin",
    "type_target": "Gõ lại từ",
    "listen_type": "Nghe rồi gõ",
}


def _rate(correct: int, total: int) -> float | None:
    return round(correct / total, 4) if total else None


@extend_schema(tags=["learning"])
class LearningStatsView(APIView):
    """Số liệu học của tôi trong `days` ngày gần nhất (mặc định 30, tối đa 365)."""

    @extend_schema(parameters=[*LANG_PARAMS, OpenApiParameter("days", int, description="Số ngày gần nhất (7–365)")])
    def get(self, request):
        target = resolve_target(request)
        try:
            days = min(365, max(7, int(request.query_params.get("days", 30))))
        except ValueError:
            days = 30
        now = timezone.now()
        since = now - timedelta(days=days)
        words = PersonalWord.objects.filter(user=request.user, language=target.learn)
        logs = ReviewLog.objects.filter(user=request.user, language=target.learn, created_at__gte=since)
        if target.script:
            logs = logs.filter(Q(script=target.script) | Q(script=""))

        status = dict(words.values_list("status").annotate(n=Count("id")).values_list("status", "n"))
        agg = logs.aggregate(total=Count("id"), ok=Count("id", filter=Q(correct=True)),
                             first=Count("id", filter=Q(first_try=True)),
                             first_ok=Count("id", filter=Q(first_try=True, correct=True)))

        # one row per day, empty days included, so the chart keeps its shape
        per_day = {
            r["day"]: r for r in logs.annotate(day=TruncDate("created_at")).values("day")
            .annotate(total=Count("id"), ok=Count("id", filter=Q(correct=True)))
        }
        today = timezone.localdate()
        daily = []
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            r = per_day.get(d, {})
            daily.append({"date": d.isoformat(), "answers": r.get("total", 0), "correct": r.get("ok", 0)})

        by_type = [
            {"type": r["question_type"], "label": QUESTION_LABELS.get(r["question_type"], r["question_type"]),
             "answers": r["total"], "accuracy": _rate(r["ok"], r["total"])}
            for r in logs.values("question_type").annotate(total=Count("id"), ok=Count("id", filter=Q(correct=True)))
            .order_by("-total")
        ]

        topic_rows = (
            words.exclude(topic=None).values("topic_id", "topic__name_vi", "topic__icon")
            .annotate(total=Count("id"), mastered=Count("id", filter=Q(status=PersonalWord.Status.MASTERED)))
            .order_by("-total")[:12]
        )
        topic_acc = {
            r["personal_word__topic_id"]: r for r in logs.exclude(personal_word__topic=None)
            .values("personal_word__topic_id").annotate(total=Count("id"), ok=Count("id", filter=Q(correct=True)))
        }
        by_topic = []
        for r in topic_rows:
            a = topic_acc.get(r["topic_id"], {})
            by_topic.append({"id": r["topic_id"], "name": r["topic__name_vi"], "icon": r["topic__icon"],
                             "words": r["total"], "mastered": r["mastered"],
                             "answers": a.get("total", 0), "accuracy": _rate(a.get("ok", 0), a.get("total", 0))})

        # words answered wrong most often (at least 2 answers in the period)
        hard_rows = list(
            logs.values("personal_word_id", "personal_word__word_id")
            .annotate(total=Count("id"), wrong=Count("id", filter=Q(correct=False)))
            .filter(total__gte=2, wrong__gte=1).order_by("-wrong", "total")[:8]
        )
        cards = {}
        if hard_rows:
            ws = words_for_target(Word.objects.filter(id__in=[r["personal_word__word_id"] for r in hard_rows]), request.user, target)
            cards = {w.id: card(w, target, None, request) for w in ws}
        hardest = [
            {"card": cards[r["personal_word__word_id"]], "answers": r["total"], "wrong": r["wrong"]}
            for r in hard_rows if r["personal_word__word_id"] in cards
        ]

        return Response({
            "language": target.code,
            "days": days,
            "words": {"total": sum(status.values()), "new": status.get("new", 0),
                      "learning": status.get("learning", 0), "mastered": status.get("mastered", 0)},
            "answers": agg["total"],
            "accuracy": _rate(agg["ok"], agg["total"]),
            "first_try_accuracy": _rate(agg["first_ok"], agg["first"]),
            "active_days": sum(1 for d in daily if d["answers"]),
            "daily": daily,
            "by_question_type": by_type,
            "by_topic": by_topic,
            "hardest": hardest,
        })
