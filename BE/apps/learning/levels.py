"""The 4-level learning path of each language.

Every word has a level per learning language (Word.levels, from seed/concepts/levels.csv – HSK for Chinese, Tatoeba
frequency otherwise). A learner starts at level 1; level n+1 opens when UNLOCK_PERCENT of the words of level n have
been started (learning or mastered), or right away by passing a short test on level n (PASS_SCORE of TEST_SIZE).
New words come from the learner's current level first; sentence practice uses only words up to that level.
"""
import random

from django.core import signing
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.vocab.models import ReviewStatus, Word, WordTranslation
from apps.vocab.services import resolve_target, translation_payload, words_for_target
from apps.vocab.views import LANG_PARAMS

from .models import LearnerLevel, PersonalWord

LEVELS = (
    (1, "Nhập môn", "Những từ gặp nhiều nhất trong đời sống hằng ngày"),
    (2, "Sơ cấp", "Mở rộng vốn từ quen thuộc: đồ vật, con vật, hoạt động"),
    (3, "Trung cấp", "Từ ít gặp hơn, chủ đề đa dạng"),
    (4, "Nâng cao", "Từ chuyên đề, ít dùng hằng ngày"),
)
MAX_LEVEL = len(LEVELS)
UNLOCK_PERCENT = 70
TEST_SIZE = 10
PASS_SCORE = 8
_SALT = "learning.level-test"
STARTED = (PersonalWord.Status.LEARNING, PersonalWord.Status.MASTERED)


def level_of(word: Word, learn: str) -> int:
    return int((word.levels or {}).get(learn) or MAX_LEVEL)


def level_words(user, target, level: int | None = None):
    """Words of the path for this learner (visible translation, children only see child-friendly words)."""
    qs = Word.objects.all()
    if level is not None:
        qs = qs.filter(**{f"levels__{target.learn}": level})
    if getattr(user, "learner_type", "") == "kid":
        qs = qs.filter(audience__in=["all", "kid"])
    return words_for_target(qs, user, target)


def _state(user, learn) -> LearnerLevel:
    return LearnerLevel.objects.get_or_create(user=user, language=learn)[0]


def progress(user, target) -> dict:
    state = _state(user, target.learn)
    started_ids = set(PersonalWord.objects.filter(user=user, language=target.learn, status__in=STARTED)
                      .values_list("word_id", flat=True))
    mastered_ids = set(PersonalWord.objects.filter(user=user, language=target.learn,
                                                   status=PersonalWord.Status.MASTERED).values_list("word_id", flat=True))
    rows, unlocked_prev = [], True
    for n, name, desc in LEVELS:
        ids = set(level_words(user, target, n).values_list("id", flat=True))
        started = len(ids & started_ids)
        percent = round(100 * started / len(ids)) if ids else 100
        unlocked = n == 1 or n <= state.passed_test or getattr(user, "is_staff_role", False) or unlocked_prev
        rows.append({"level": n, "name": name, "description": desc, "total": len(ids), "started": started,
                     "mastered": len(ids & mastered_ids), "percent": percent, "unlocked": unlocked,
                     "needed": max(0, -(-len(ids) * UNLOCK_PERCENT // 100) - started)})
        unlocked_prev = unlocked and percent >= UNLOCK_PERCENT
    top = max(r["level"] for r in rows if r["unlocked"])
    current = min(state.current, top)
    for r in rows:
        r["current"] = r["level"] == current
    return {"language": target.learn, "current": current, "unlock_percent": UNLOCK_PERCENT,
            "test": {"size": TEST_SIZE, "pass": PASS_SCORE}, "levels": rows}


def current_level(user, target) -> int:
    return progress(user, target)["current"]


def advance_if_done(user, target) -> int | None:
    """After a session: when the current level reached UNLOCK_PERCENT and the next one opened, move up to it."""
    p = progress(user, target)
    cur = p["current"]
    row = next(r for r in p["levels"] if r["level"] == cur)
    if cur < MAX_LEVEL and row["percent"] >= UNLOCK_PERCENT and p["levels"][cur]["unlocked"]:
        state = _state(user, target.learn)
        state.current = cur + 1
        state.save(update_fields=["current", "updated_at"])
        return cur + 1
    return None


# ------------------------------------------------------------------ test to skip a level

def build_test(user, target, level: int) -> dict | None:
    words = list(level_words(user, target, level).order_by("?")[:TEST_SIZE])
    if len(words) < 4:
        return None
    vi = {t.word_id: t.text for t in WordTranslation.objects.filter(
        word__in=level_words(user, target, level), language_id="vi", status=ReviewStatus.VERIFIED)}
    questions, answers = [], []
    for w in words:
        tr = next((t for t in w.visible_translations if t.language_id == target.code), None)
        if tr is None or w.id not in vi:
            continue
        if target.learn == "vi":  # children: listen, then pick the written word
            others = [v for wid, v in vi.items() if wid != w.id]
            opts = random.sample(others, 3) + [tr.text]
            prompt = {"audio": translation_payload(tr), "emoji": w.emoji}
            answer = tr.text
        else:
            others = [v for wid, v in vi.items() if wid != w.id and v != vi[w.id]]
            opts = random.sample(others, 3) + [vi[w.id]]
            prompt = {"word": translation_payload(tr)}
            answer = vi[w.id]
        random.shuffle(opts)
        questions.append({"index": len(questions), "prompt": prompt, "options": opts})
        answers.append(answer)
    token = signing.dumps({"u": user.id, "l": target.learn, "n": level, "a": answers}, salt=_SALT)
    return {"level": level, "pass": PASS_SCORE, "questions": questions, "token": token}


def grade_test(user, target, level: int, token: str, given: list) -> dict:
    data = signing.loads(token, salt=_SALT, max_age=3600)
    if data["u"] != user.id or data["l"] != target.learn or data["n"] != level:
        raise signing.BadSignature("token khác người học / cấp")
    answers = data["a"]
    score = sum(1 for a, g in zip(answers, given) if str(g).strip() == a)
    need = min(PASS_SCORE, len(answers))
    passed = score >= need
    if passed and level < MAX_LEVEL:
        state = _state(user, target.learn)
        state.passed_test = max(state.passed_test, level + 1)
        state.current = max(state.current, level + 1)
        state.save(update_fields=["passed_test", "current", "updated_at"])
    return {"score": score, "total": len(answers), "passed": passed, "answers": answers,
            "unlocked": level + 1 if passed and level < MAX_LEVEL else None}


# ------------------------------------------------------------------ API

class CurrentSerializer(serializers.Serializer):
    level = serializers.IntegerField(min_value=1, max_value=MAX_LEVEL)


class TestAnswerSerializer(serializers.Serializer):
    token = serializers.CharField()
    answers = serializers.ListField(child=serializers.CharField(allow_blank=True), max_length=TEST_SIZE)


@extend_schema(tags=["levels"], parameters=LANG_PARAMS)
class LevelsView(APIView):
    """Lộ trình 4 cấp độ của ngôn ngữ đang học. POST {"level": n} để chọn cấp đang học (trong các cấp đã mở)."""

    def get(self, request):
        return Response(progress(request.user, resolve_target(request)))

    def post(self, request):
        ser = CurrentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        target = resolve_target(request)
        p = progress(request.user, target)
        n = ser.validated_data["level"]
        if not next(r for r in p["levels"] if r["level"] == n)["unlocked"]:
            return Response({"detail": f"Cấp {n} chưa mở – học thêm cấp {n - 1} hoặc làm bài kiểm tra vượt cấp"},
                            status=status.HTTP_403_FORBIDDEN)
        state = _state(request.user, target.learn)
        state.current = n
        state.save(update_fields=["current", "updated_at"])
        return Response(progress(request.user, target))


@extend_schema(tags=["levels"], parameters=LANG_PARAMS)
class LevelTestView(APIView):
    """Kiểm tra vượt cấp: GET lấy đề (10 câu), POST {token, answers} – đúng từ 8 câu thì mở cấp tiếp theo."""

    def get(self, request, n: int):
        if not 1 <= n < MAX_LEVEL:
            return Response({"detail": "Không có bài kiểm tra cho cấp này"}, status=404)
        test = build_test(request.user, resolve_target(request), n)
        if test is None:
            return Response({"detail": "Cấp này chưa đủ từ để kiểm tra"}, status=404)
        return Response(test)

    def post(self, request, n: int):
        ser = TestAnswerSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            result = grade_test(request.user, resolve_target(request), n, ser.validated_data["token"],
                                ser.validated_data["answers"])
        except signing.BadSignature:
            return Response({"detail": "Bài kiểm tra không hợp lệ hoặc đã hết hạn"}, status=400)
        return Response(result | {"progress": progress(request.user, resolve_target(request))})
