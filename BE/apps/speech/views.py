import base64
import re
from collections import Counter, defaultdict
from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.vocab.models import ExampleSentence, ReviewStatus, WordTranslation
from apps.vocab.services import resolve_target, visible_translations_q

from . import recognizer
from .models import PronunciationAttempt
from .tasks import assess_recording

MAX_AUDIO_BYTES = 2 * 1024 * 1024  # ~60 s of 16 kHz mono WAV; the scorer keeps 12 s
MAX_SENTENCE = 120
# Vietnamese is off: the recogniser saw little Vietnamese in training and scored native speakers 27-90 on single
# words (AI/report/speech/README.md) – learners of Vietnamese keep the device speech check.
LANGUAGES = ("en", "zh-Hans", "zh-Hant")


def _err(detail: str, status: int, code: str = ""):
    return Response({"detail": detail, "code": code, "errors": {}}, status=status)


def _pinyin_of(language: str, translation=None, sentence=None) -> list[str] | None:
    if not language.startswith("zh"):
        return None
    if translation is not None:
        return (translation.pinyin_numbered or translation.pinyin).split()
    return [p for tok in (sentence.tokens or []) if not tok.get("x") for p in str(tok.get("p", "")).split()]


class SpeechStatusView(APIView):
    @extend_schema(tags=["speech"], responses={200: dict})
    def get(self, request):
        return Response({"enabled": recognizer.available(), "languages": list(LANGUAGES), "tones_experimental": True})


class AssessView(APIView):
    """POST multipart: audio (WAV, 16 kHz mono preferred) + translation_id (a word) or sentence_id (an example
    sentence). Scores phone by phone in the Celery worker and keeps the result (not the recording)."""

    parser_classes = [MultiPartParser, FormParser]
    throttle_scope = "speech"

    @extend_schema(tags=["speech"], request=None, responses={200: dict})
    def post(self, request):
        audio = request.FILES.get("audio")
        if not audio:
            return _err("Thiếu file ghi âm", 400, "no_audio")
        if audio.size > MAX_AUDIO_BYTES:
            return _err("File ghi âm quá dài", 400, "too_long")
        translation = sentence = None
        if request.data.get("translation_id"):
            translation = get_object_or_404(
                WordTranslation.objects.filter(visible_translations_q(request.user)), pk=request.data["translation_id"]
            )
            language, text, kind = translation.language_id, translation.text, PronunciationAttempt.Kind.WORD
        elif request.data.get("sentence_id"):
            qs = ExampleSentence.objects.all()
            if not getattr(request.user, "is_staff_role", False):
                qs = qs.filter(Q(status=ReviewStatus.VERIFIED) | Q(word__created_by=request.user))
            sentence = get_object_or_404(qs, pk=request.data["sentence_id"])
            language, text, kind = sentence.language_id, sentence.text, PronunciationAttempt.Kind.SENTENCE
            if len(text) > MAX_SENTENCE:
                return _err("Câu quá dài để chấm", 400, "too_long")
        else:
            return _err("Cần translation_id hoặc sentence_id", 400, "no_item")
        if language not in LANGUAGES:
            return _err("Chưa chấm chi tiết được ngôn ngữ này", 400, "language")
        if not recognizer.available():
            return _err("Server chưa bật chấm phát âm chi tiết", 503, "disabled")

        pinyin = _pinyin_of(language, translation, sentence)
        job = assess_recording.delay(base64.b64encode(audio.read()).decode(), text, language, pinyin)
        try:
            result = job.get(timeout=settings.SPEECH_TIMEOUT)
        except Exception as e:  # noqa: BLE001 - timeout, worker down, model or espeak missing
            if "Timeout" in type(e).__name__:
                return _err("Máy chấm đang bận, thử lại sau ít giây", 503, "busy")
            return _err("Chưa chấm được phát âm lúc này", 503, "unavailable")
        if "problem" in result:
            return _err(result["detail"], 422, result["problem"])

        attempt = PronunciationAttempt.objects.create(
            user=request.user,
            language=language,
            kind=kind,
            translation=translation,
            sentence=sentence,
            text=text,
            score=result["score"],
            phone_score=result["phone_score"],
            tone_score=result["tone_score"],
            completeness=result["completeness"],
            heard_ipa=result["heard_ipa"][:500],
            error_codes=sorted({e["code"] for e in result["errors"]}),
            result=result,
            ms=result["ms"],
        )
        return Response({"id": attempt.id, "text": text, "language": language, **result})


class ProgressView(APIView):
    """Score per day, the sounds most often wrong, the last attempts – for one learning language."""

    @extend_schema(tags=["speech"], responses={200: dict})
    def get(self, request):
        target = resolve_target(request)
        since = timezone.now() - timedelta(days=60)
        qs = PronunciationAttempt.objects.filter(user=request.user, language=target.code, created_at__gte=since)
        attempts = list(qs.only("id", "text", "score", "created_at", "result", "kind")[:500])
        by_day = defaultdict(list)
        for a in attempts:
            by_day[timezone.localdate(a.created_at).isoformat()].append(a.score)
        errors, example = Counter(), {}
        for a in attempts:
            for e in a.result.get("errors", []):
                key = e["code"] if not e["code"].endswith((".SUBST", ".MISSING")) else f"{e['code']}:{e['expected']}"
                errors[key] += 1
                example.setdefault(key, e)
        week = [a.score for a in attempts if a.created_at >= timezone.now() - timedelta(days=7)]
        return Response(
            {
                "language": target.code,
                "attempts": len(attempts),
                "average_7d": round(sum(week) / len(week)) if week else None,
                "by_day": [
                    {"date": d, "average": round(sum(v) / len(v)), "count": len(v)} for d, v in sorted(by_day.items())
                ],
                "weak_sounds": [
                    {
                        "code": re.sub(r":.*", "", k),
                        "count": n,
                        "expected": example[k]["expected"],
                        "heard": example[k]["heard"],
                        "tip": example[k]["tip"],
                    }
                    for k, n in errors.most_common(5)
                ],
                "recent": [
                    {"id": a.id, "text": a.text, "kind": a.kind, "score": a.score, "created_at": a.created_at}
                    for a in attempts[:10]
                ],
            }
        )
