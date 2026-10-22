from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.gamification.models import XpTransaction
from apps.gamification.services import award_xp, mark_activity

from . import curriculum as cur
from . import exercises as ex
from .models import LiteracyAttempt, LiteracyProgress

PASS_PERCENT = 60  # unlocks the next lesson
XP_PER_CORRECT = 2


def _stars(percent: int) -> int:
    return 3 if percent >= 90 else 2 if percent >= 75 else 1 if percent >= PASS_PERCENT else 0


def _unlocked(user, progress: dict) -> int:
    """Highest lesson the user may open (staff can open everything to review the content)."""
    if getattr(user, "is_staff_role", False):
        return len(cur.LESSONS)
    n = 1
    while n < len(cur.LESSONS) and progress.get(n) and progress[n].best_percent >= PASS_PERCENT:
        n += 1
    return n


@extend_schema(tags=["literacy"])
class LessonListView(APIView):
    """Lộ trình học đọc – viết tiếng Việt (cho trẻ em)."""

    def get(self, request):
        progress = {p.lesson: p for p in LiteracyProgress.objects.filter(user=request.user)}
        unlocked = _unlocked(request.user, progress)
        out = []
        for lesson in cur.LESSONS:
            p = progress.get(lesson["n"])
            done = bool(p and p.best_percent >= PASS_PERCENT)
            out.append({
                "n": lesson["n"], "title": lesson["title"], "review": bool(lesson.get("review")),
                "units": [u.payload() for u in lesson["units"]],
                "status": "done" if done else "open" if lesson["n"] <= unlocked else "locked",
                "stars": p.stars if p else 0, "best_percent": p.best_percent if p else 0,
            })
        return Response({"lessons": out, "pass_percent": PASS_PERCENT})


@extend_schema(tags=["literacy"])
class LessonView(APIView):
    def get(self, request, n: int):
        if not cur.lesson(n):
            return Response({"detail": "Không có bài học này"}, status=404)
        progress = {p.lesson: p for p in LiteracyProgress.objects.filter(user=request.user)}
        if n > _unlocked(request.user, progress):
            return Response({"detail": f"Hãy hoàn thành bài {n - 1} trước nhé!"}, status=403)
        lesson = ex.build_lesson(n)
        for item in [w for i in lesson["intro"] for w in i["words"]] + lesson["exercises"]:
            if (item.get("image") or "").startswith("/"):
                item["image"] = request.build_absolute_uri(item["image"])
        return Response(lesson)


class CheckSerializer(serializers.Serializer):
    token = serializers.CharField()
    answer = serializers.JSONField(help_text="Chuỗi; với bài ghép tiếng: {onset, rhyme, tone}")
    response_ms = serializers.IntegerField(min_value=0, required=False)


@extend_schema(tags=["literacy"], request=CheckSerializer)
class CheckView(APIView):
    def post(self, request):
        ser = CheckSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            data = ex.unsign(ser.validated_data["token"])
        except Exception:
            return Response({"detail": "Bài tập đã hết hạn, hãy mở lại bài học"}, status=400)
        answer = ser.validated_data["answer"]
        correct, extra = ex.check(data, answer)
        first = not LiteracyAttempt.objects.filter(user=request.user, session=data["s"], index=data["i"]).exists()
        LiteracyAttempt.objects.create(
            user=request.user, session=data["s"], lesson=data["l"], unit=data["u"], exercise=data["t"], index=data["i"],
            correct=correct, expected=str(data["a"])[:200], answer=str(answer)[:200],
            response_ms=ser.validated_data.get("response_ms"),
        )
        xp = 0
        if correct and first:
            xp = award_xp(request.user, XpTransaction.Source.LEARN, XP_PER_CORRECT,
                          source_id=f"literacy:{data['s']}:{data['i']}")
        return Response({"correct": correct, "xp": xp, **extra})


class FinishSerializer(serializers.Serializer):
    session = serializers.CharField(max_length=16)
    total = serializers.IntegerField(min_value=1, max_value=50)


@extend_schema(tags=["literacy"], request=FinishSerializer)
class FinishView(APIView):
    @transaction.atomic
    def post(self, request, n: int):
        ser = FinishSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if not cur.lesson(n):
            return Response({"detail": "Không có bài học này"}, status=404)
        attempts = LiteracyAttempt.objects.filter(user=request.user, session=ser.validated_data["session"], lesson=n)
        first_try: dict[int, bool] = {}
        for a in attempts.order_by("created_at"):
            first_try.setdefault(a.index, a.correct)
        total = max(ser.validated_data["total"], len(first_try))
        correct = sum(first_try.values())
        percent = min(100, round(100 * correct / total))
        p, _ = LiteracyProgress.objects.select_for_update().get_or_create(user=request.user, lesson=n)
        p.times_completed += 1
        if percent > p.best_percent:
            p.best_percent, p.stars = percent, _stars(percent)
        if percent >= PASS_PERCENT and not p.completed_at:
            p.completed_at = timezone.now()
        p.save()
        mark_activity(request.user)
        return Response({"correct_first_try": correct, "total": total, "percent": percent, "stars": _stars(percent),
                         "passed": percent >= PASS_PERCENT, "best_percent": p.best_percent,
                         "next_unlocked": percent >= PASS_PERCENT and n < len(cur.LESSONS)})
