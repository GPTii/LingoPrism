from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.detection.models import Detection, DetectionItem
from apps.vocab.models import Word
from apps.vocab.services import resolve_target, tts_locale, words_for_target

from . import generator, translator
from .models import PhotoDialogue

MAX_WORDS = 6


def photo_words(request, detection: Detection, target) -> list[dict]:
    """The verified words of a photo: the objects the learner kept (or all of them), corrected labels first."""
    items = list(detection.items.all())
    kept = [i for i in items if i.selected] or items
    labels = []
    for it in kept:
        if it.feedback == DetectionItem.Feedback.WRONG and not it.corrected_label:
            continue  # "this is not an object"
        label = it.corrected_label or it.label
        if label not in labels:
            labels.append(label)
    words = {
        w.yolo_label: w for w in words_for_target(Word.objects.filter(yolo_label__in=labels), request.user, target)
    }
    out = []
    for label in labels:
        w = words.get(label)
        tr = (
            next((t for t in getattr(w, "visible_translations", []) if t.language_id == target.code), None)
            if w
            else None
        )
        vi = next((t for t in getattr(w, "visible_translations", []) if t.language_id == "vi"), None) if w else None
        if tr:
            out.append(
                {
                    "word_id": w.id,
                    "text": tr.text,
                    "meaning_vi": (vi.text if vi else tr.meaning_vi),
                    "level": (w.levels or {}).get(target.learn) or 1,
                }
            )
    return out[:MAX_WORDS]


def _payload(d: PhotoDialogue) -> dict:
    return {
        "id": d.id,
        "detection": d.detection_id,
        "language": d.language,
        "title_vi": d.title_vi,
        "words": d.words,
        "lines": d.lines,
        "ai_generated": True,
        "model": d.model_name,
        "created_at": d.created_at,
    }


class AiStatusView(APIView):
    @extend_schema(tags=["ai"], responses={200: dict})
    def get(self, request):
        return Response({"dialogue": generator.enabled(), "translate": generator.enabled()})


class PhotoDialogueView(APIView):
    """GET: the dialogue already written for this photo (404 if none). POST: write it (once per language)."""

    throttle_scope = "ai_dialogue"

    def get_throttles(self):
        return super().get_throttles() if self.request.method == "POST" else []

    def _detection(self, request, pk):
        return get_object_or_404(Detection, pk=pk, user=request.user)

    @extend_schema(tags=["ai"], responses={200: dict})
    def get(self, request, pk):
        det = self._detection(request, pk)
        d = PhotoDialogue.objects.filter(detection=det, language=resolve_target(request).code).first()
        if not d:
            return Response({"detail": "Chưa có hội thoại cho ảnh này", "errors": {}}, status=404)
        return Response(_payload(d))

    @extend_schema(tags=["ai"], request=None, responses={200: dict})
    def post(self, request, pk):
        det = self._detection(request, pk)
        target = resolve_target(request)
        existing = PhotoDialogue.objects.filter(detection=det, language=target.code).first()
        if existing:
            return Response(_payload(existing))
        words = photo_words(request, det, target)
        if not words:
            return Response(
                {"detail": "Ảnh này chưa có từ nào đã kiểm duyệt để tạo hội thoại", "errors": {}}, status=400
            )
        try:
            out = generator.generate(words, target.code, max(w["level"] for w in words))
        except generator.AiUnavailable as e:
            return Response({"detail": str(e), "errors": {}}, status=503)
        d, _ = PhotoDialogue.objects.get_or_create(
            detection=det,
            language=target.code,
            defaults={
                "user": request.user,
                "words": words,
                "title_vi": out["title_vi"],
                "lines": out["lines"],
                "model_name": out["model"],
            },
        )
        return Response(_payload(d))


class TranslateView(APIView):
    """POST {text, source, target}: a machine translation (not stored) + verified words found in it.
    source may be "auto" (chat composer): the model detects it."""

    throttle_scope = "translate"

    @extend_schema(tags=["ai"], request=dict, responses={200: dict})
    def post(self, request):
        text = str(request.data.get("text", "")).strip()
        source, target = request.data.get("source"), request.data.get("target")
        langs = translator.LANGUAGES
        if source not in (*langs, translator.AUTO) or target not in langs or source == target:
            return Response({"detail": "Cặp ngôn ngữ không hợp lệ", "errors": {}}, status=400)
        if {source, target} == {"zh-Hans", "zh-Hant"} or (
            source == translator.AUTO and translator.wrong_script(text, target)
        ):
            # giản ↔ phồn is not a translation: the words themselves differ by region (土豆 / 馬鈴薯)
            return Response({"detail": "Không chuyển trực tiếp giữa giản thể và phồn thể", "errors": {}}, status=400)
        if not text:
            return Response({"detail": "Chưa có nội dung để dịch", "errors": {}}, status=400)
        if len(text) > translator.MAX_CHARS:
            return Response({"detail": f"Tối đa {translator.MAX_CHARS} ký tự mỗi lần dịch", "errors": {}}, status=400)
        try:
            out = translator.translate(text, source, target)
        except generator.AiUnavailable as e:
            return Response({"detail": str(e), "errors": {}}, status=503)
        return Response(
            {
                "text": text,
                "source": source,
                "target": target,
                **out,
                "machine_translated": True,
                "source_tts": tts_locale(source) if source != translator.AUTO else "",
                "target_tts": tts_locale(target),
                "words": translator.verified_words({source: text, target: out["translation"]}, request.user),
            }
        )
