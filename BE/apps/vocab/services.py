"""Language resolution and learner-facing word cards."""
from dataclasses import dataclass

from django.utils import timezone
from django.db.models import Prefetch, Q

from .models import ExampleSentence, ReviewStatus, Word, WordTranslation

LEARN_LANGUAGES = ("vi", "en", "zh")


@dataclass
class Target:
    learn: str  # vi | en | zh
    code: str  # vi | en | zh-Hans | zh-Hant
    script: str  # "" | hans | hant


def resolve_target(request) -> Target:
    """?lang=vi|en|zh&script=hans|hant, defaulting to the user's settings."""
    user = request.user
    learn = request.query_params.get("lang") or getattr(user, "active_language", "en")
    if learn not in LEARN_LANGUAGES:
        learn = "en"
    if learn != "zh":
        return Target(learn, learn, "")
    script = request.query_params.get("script") or getattr(user, "zh_script", "hans")
    script = script if script in ("hans", "hant") else "hans"
    return Target("zh", "zh-Hant" if script == "hant" else "zh-Hans", script)


def visible_translations_q(user, prefix: str = "") -> Q:
    """Learners only see verified data; staff see everything; users see their own drafts."""
    if getattr(user, "is_staff_role", False):
        return Q()
    return Q(**{f"{prefix}status": ReviewStatus.VERIFIED}) | Q(**{f"{prefix}word__created_by": user})


def words_for_target(qs, user, target: Target):
    """Restrict to words that have a visible translation in the target language and prefetch what cards need."""
    codes = {target.code, "vi", "en"}
    vis = visible_translations_q(user)
    visible_ids = WordTranslation.objects.filter(vis, language_id=target.code).values("word_id")
    return qs.filter(id__in=visible_ids).prefetch_related(
        Prefetch(
            "translations",
            queryset=WordTranslation.objects.filter(vis, language_id__in=codes),
            to_attr="visible_translations",
        ),
        Prefetch(
            "examples",
            queryset=ExampleSentence.objects.filter(
                Q(status=ReviewStatus.VERIFIED) if not getattr(user, "is_staff_role", False) else Q(),
                language_id=target.code,
            ),
            to_attr="visible_examples",
        ),
    )


TTS_LOCALES = {"vi": "vi-VN", "en": "en-US", "zh-Hans": "zh-CN", "zh-Hant": "zh-TW"}


def tts_locale(code: str) -> str:
    return TTS_LOCALES.get(code, "")


def translation_payload(tr: WordTranslation | None) -> dict | None:
    if tr is None:
        return None
    data = {"id": tr.id, "language": tr.language_id, "text": tr.text, "tts_locale": tts_locale(tr.language_id)}
    if tr.language_id == "en":
        data["ipa"] = tr.ipa
    if tr.language_id.startswith("zh"):
        data.update(pinyin=tr.pinyin, measure_word=tr.measure_word, level=tr.level,
                    regional_difference=tr.regional_difference)
        if tr.language_id == "zh-Hant":
            data["zhuyin"] = tr.zhuyin
    if tr.status != ReviewStatus.VERIFIED:
        data["unverified"] = True
    return data


def card(word: Word, target: Target, personal=None, request=None) -> dict:
    by_lang = {t.language_id: t for t in getattr(word, "visible_translations", [])}
    image = word.image.url if word.image else word.image_url
    if image and request is not None and image.startswith("/"):
        image = request.build_absolute_uri(image)
    vi = by_lang.get("vi")
    return {
        "id": word.id,
        "slug": word.slug,
        "image": image or None,
        "image_credit": word.image_credit if word.image and word.image.name.startswith("words/seed_") else "",
        "image_source": word.image_source if word.image and word.image.name.startswith("words/seed_") else "",
        "emoji": word.emoji,
        "part_of_speech": word.part_of_speech,
        "difficulty": word.difficulty,
        "level": (word.levels or {}).get(target.learn),
        "audience": word.audience,
        "yolo_label": word.yolo_label,
        "target": translation_payload(by_lang.get(target.code)),
        "meaning_vi": vi.text if vi else "",
        # learners are Vietnamese: a Chinese word is explained in Vietnamese, never through English
        "english": None,
        "examples": [
            {"id": e.id, "text": e.text, "transliteration": e.transliteration, "tokens": e.tokens,
             "target_tokens": e.target_tokens, "translation_vi": e.translation_vi,
             # Vietnamese is taught to Vietnamese children – no English gloss
             "translation_en": "",
             "source": e.source, "source_id": e.source_id}
            for e in getattr(word, "visible_examples", [])[:3]
        ],
        "personal": None if personal is None else {
            "id": personal.id, "status": personal.status, "stage": personal.stage,
            "due_at": personal.due_at, "last_reviewed_at": personal.last_reviewed_at,
            "recall": recall_now(personal),
        },
    }


def recall_now(personal) -> float | None:
    """FSRS retrievability today: the chance (0–1) the learner still remembers this word right now.
    None until the word has been reviewed at least once."""
    from apps.algorithms.fsrs import retrievability

    stability = getattr(personal, "fsrs_stability", 0) or 0
    if not personal.last_reviewed_at or stability <= 0:
        return None
    days = (timezone.now() - personal.last_reviewed_at).total_seconds() / 86400
    return round(retrievability(days, stability), 3)


def personal_map(user, word_ids, target: Target) -> dict:
    from apps.learning.models import PersonalWord

    return {
        p.word_id: p
        for p in PersonalWord.objects.filter(user=user, language=target.learn, word_id__in=list(word_ids))
    }
