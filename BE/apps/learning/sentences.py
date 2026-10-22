"""Sentence practice built from verified example sentences (Tatoeba) of the words a learner studies.

Exercise types
  arrange – translation shown, put the shuffled words in order
  listen  – sentence is read aloud (TTS), put the shuffled words in order
  fill    – one word of the sentence is blanked, choose it among 4 words (distractors: DistractorProvider)
  meaning – read the sentence, choose its translation among 4
Answers are checked on the server; every attempt is stored in SentenceAttempt.
"""
import random

from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.gamification.models import XpTransaction
from apps.gamification.services import award_xp, mark_activity
from apps.vocab.lang.sentences import normalize_answer
from apps.vocab.models import ExampleSentence, ReviewStatus, TopicWord, WordTranslation
from apps.vocab.services import resolve_target, tts_locale
from apps.vocab.views import LANG_PARAMS

from .models import PersonalWord, SentenceAttempt
from .questions import get_distractor_provider

TYPES = ("arrange", "fill", "meaning", "listen")
XP_CORRECT = 2
MAX_LESSON = 20


def _words(ex: ExampleSentence) -> list[str]:
    return [t["t"] for t in ex.tokens if not t.get("x")]


def _target_text(ex: ExampleSentence) -> str:
    sep = "" if ex.language_id.startswith("zh") else " "
    return sep.join(ex.tokens[i]["t"] for i in ex.target_tokens)


def _translation(ex: ExampleSentence) -> tuple[str, str]:
    """Translation shown to the (Vietnamese) learner: Vietnamese only – never an English gloss of a Chinese sentence.
    ("vi", "") when Tatoeba has no Vietnamese translation; exercises that need one are then skipped."""
    if ex.language_id != "vi" and ex.translation_vi:
        return "vi", ex.translation_vi
    return "vi", ""


def source_payload(ex: ExampleSentence) -> dict:
    return {"name": "Tatoeba", "id": ex.source_id, "license": ex.license,
            "url": f"https://tatoeba.org/sentences/show/{ex.source_id}"} if ex.source == "tatoeba" else {"name": ex.source}


def sentence_payload(ex: ExampleSentence) -> dict:
    lang, text = _translation(ex)
    return {"id": ex.id, "language": ex.language_id, "text": ex.text, "tokens": ex.tokens, "target_tokens": ex.target_tokens,
            "transliteration": ex.transliteration, "tts_locale": tts_locale(ex.language_id),
            "translation": {"language": lang, "text": text} if text and ex.language_id != "vi" else None,
            "source": source_payload(ex)}


def _fill_options(ex: ExampleSentence, target) -> list[str] | None:
    answer = _target_text(ex)
    picks = get_distractor_provider().pick(ex.word, target, 6)
    texts = WordTranslation.objects.filter(word__in=picks, language_id=ex.language_id, status=ReviewStatus.VERIFIED)
    words = set(_words(ex))
    opts = list(dict.fromkeys(t.text for t in texts if t.text != answer and t.text not in words))[:3]
    if len(opts) < 3:
        return None
    opts.append(answer)
    random.shuffle(opts)
    return opts


def _meaning_options(ex: ExampleSentence, pool: list[ExampleSentence]) -> list[str] | None:
    lang, answer = _translation(ex)
    if not answer:
        return None
    others = list(dict.fromkeys(t for t in (_translation(o) for o in pool if o.source_id != ex.source_id)
                                if t[1] and t[1] != answer))
    if len(others) < 3:
        return None
    opts = [t for _, t in random.sample(others, 3)] + [answer]
    random.shuffle(opts)
    return opts


def build_exercise(ex: ExampleSentence, kind: str, target, pool) -> dict | None:
    base = {"id": ex.id, "type": kind, "word": {"id": ex.word_id, "text": _target_text(ex)}}
    lang, translation = _translation(ex)
    if kind == "arrange" and not translation and ex.language_id != "vi":
        return None  # the prompt of "arrange" is the Vietnamese meaning
    if kind in ("arrange", "listen"):
        tiles = [{"t": t["t"], "p": t.get("p", ""), "z": t.get("z", "")} for t in ex.tokens if not t.get("x")]
        if len(tiles) < 3:
            return None
        while len(tiles) > 1 and [t["t"] for t in tiles] == _words(ex):
            random.shuffle(tiles)
        base.update(tiles=tiles, joiner="" if ex.language_id.startswith("zh") else " ",
                    prompt={"language": lang, "text": translation} if kind == "arrange" else None,
                    tts={"text": ex.text, "locale": tts_locale(ex.language_id)} if kind == "listen" else None)
        return base
    if kind == "fill":
        opts = _fill_options(ex, target)
        if not opts:
            return None
        tokens = [({"t": "", "blank": 1} if i == ex.target_tokens[0] else t) for i, t in enumerate(ex.tokens)
                  if i not in ex.target_tokens[1:]]
        base.update(tokens=tokens, options=opts,
                    prompt={"language": lang, "text": translation} if translation and ex.language_id != "vi" else None)
        return base
    opts = _meaning_options(ex, pool)
    if not opts:
        return None
    base.update(sentence=sentence_payload(ex) | {"translation": None}, options=opts)
    return base


def is_correct(ex: ExampleSentence, kind: str, answer) -> bool:
    if kind in ("arrange", "listen"):
        given = "".join(answer) if isinstance(answer, list) else str(answer)
        return normalize_answer(given) == normalize_answer("".join(_words(ex)))
    if kind == "fill":
        return normalize_answer(str(answer)) == normalize_answer(_target_text(ex))
    return str(answer).strip() == _translation(ex)[1].strip()


class CheckSerializer(serializers.Serializer):
    sentence = serializers.IntegerField()
    type = serializers.ChoiceField(choices=TYPES)
    answer = serializers.JSONField(help_text="Danh sách từ (arrange/listen) hoặc chuỗi (fill/meaning)")
    response_ms = serializers.IntegerField(min_value=0, required=False)


@extend_schema(tags=["sentences"], parameters=LANG_PARAMS)
class SentencePracticeViewSet(viewsets.ViewSet):
    """Luyện câu: sắp xếp câu, nghe – sắp xếp, điền từ, chọn nghĩa."""

    def _pool(self, request, target):
        from .levels import current_level

        # only sentences built on words of the learner's level or below
        qs = (ExampleSentence.objects.filter(status=ReviewStatus.VERIFIED, language_id=target.code)
              .filter(**{f"word__levels__{target.learn}__lte": current_level(request.user, target)})
              .select_related("word"))
        topic = request.query_params.get("topic")
        if topic:
            return qs.filter(word__in=TopicWord.objects.filter(topic_id=topic).values("word_id")), "topic"
        mine = PersonalWord.objects.filter(user=request.user, language=target.learn).exclude(status=PersonalWord.Status.NEW)
        if qs.filter(word__in=mine.values("word_id")).exists():
            return qs.filter(word__in=mine.values("word_id")), "my_words"
        return qs, "all"

    @action(detail=False, methods=["get"])
    def lesson(self, request):
        """?topic=<id>&size=10 – không có topic thì lấy câu chứa các từ người học đã học."""
        target = resolve_target(request)
        size = max(1, min(int(request.query_params.get("size", 10) or 10), MAX_LESSON))
        qs, scope = self._pool(request, target)
        # sentences with a Vietnamese meaning first – they allow every exercise type
        pool = list(qs.exclude(translation_vi="").order_by("?")[:200])
        pool += list(qs.filter(translation_vi="").order_by("?")[:max(0, 200 - len(pool))])
        seen, picked = set(), []
        for ex in pool:
            if ex.source_id not in seen and ex.word_id not in {p.word_id for p in picked}:
                seen.add(ex.source_id)
                picked.append(ex)
        exercises = []
        for i, ex in enumerate(picked):
            if len(exercises) >= size:
                break
            kinds = list(TYPES[i % 4:] + TYPES[:i % 4])
            if target.code == "vi":
                kinds = ["listen", "fill"] if i % 2 == 0 else ["fill", "listen"]
            for kind in kinds:
                item = build_exercise(ex, kind, target, pool)
                if item:
                    exercises.append(item)
                    break
        return Response({"language": target.code, "scope": scope, "exercises": exercises})

    @action(detail=False, methods=["post"])
    def check(self, request):
        ser = CheckSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        ex = ExampleSentence.objects.filter(pk=d["sentence"], status=ReviewStatus.VERIFIED).select_related("word").first()
        if ex is None:
            return Response({"detail": "Không tìm thấy câu"}, status=404)
        correct = is_correct(ex, d["type"], d["answer"])
        lang = ex.language_id.split("-")[0]
        SentenceAttempt.objects.create(
            user=request.user, sentence=ex, language=lang, script=("hant" if ex.language_id == "zh-Hant" else
                                                                   "hans" if ex.language_id == "zh-Hans" else ""),
            exercise=d["type"], correct=correct, answer=str(d["answer"])[:300], response_ms=d.get("response_ms"),
        )
        xp = award_xp(request.user, XpTransaction.Source.PRACTICE, XP_CORRECT, source_id=f"sentence:{ex.id}") if correct else 0
        mark_activity(request.user)
        return Response({"correct": correct, "xp": xp, "answer": _target_text(ex) if d["type"] == "fill" else None,
                         "sentence": sentence_payload(ex)})

    @action(detail=False, methods=["get"])
    def stats(self, request):
        target = resolve_target(request)
        qs, _ = self._pool(request, target)
        topic_counts = {}
        for row in (ExampleSentence.objects.filter(status=ReviewStatus.VERIFIED, language_id=target.code)
                    .filter(~Q(word__topicword=None)).values_list("word__topicword__topic_id", flat=True)):
            topic_counts[row] = topic_counts.get(row, 0) + 1
        return Response({"available": qs.count(), "by_topic": topic_counts})
