"""Free translation (typed or spoken) between Vietnamese, English and Chinese, written by the same AI as the dialogues.

This is a tool, not learning data: the answer is shown as a machine translation and is never stored. Pinyin is
computed here (pypinyin + CC-CEDICT neutral tones), Chinese output in the wrong script is refused, and the only
words a learner can save from it are verified vocabulary found in the two texts."""
import json
import re

from django.conf import settings
from django.db.models.functions import Lower, Trim

from apps.vocab.models import ReviewStatus, WordTranslation

from . import generator
from .generator import LANGUAGE_NAMES, AiUnavailable

LANGUAGES = ("vi", "en", "zh-Hans", "zh-Hant")
AUTO = "auto"  # source only: the model detects it
MAX_CHARS = 500
MAX_WORDS = 8

SCHEMA = {
    "type": "object",
    "properties": {"translation": {"type": "string"}},
    "required": ["translation"],
    "additionalProperties": False,
}

SYSTEM = (
    "You are the translator of a language-learning app for Vietnamese learners. Translate the user's text "
    "faithfully and naturally into the requested language, keeping its meaning, tone and register. The text may "
    "come from speech recognition: fix obvious recognition slips silently, but never add explanations, "
    "alternatives or notes. Write Chinese only in the requested script - never mix Simplified and Traditional "
    "characters - and never add pinyin. Put only the translation in `translation`."
)
FAIL = "Không dịch được lúc này, thử lại sau."

HAN = re.compile(r"[一-鿿㐀-䶿]")
WORD_RUN = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)*")


def translate(text: str, source: str, target: str) -> dict:
    """→ {"translation", "reading", "source_reading", "model"}; raises AiUnavailable."""
    if not generator.enabled():
        raise AiUnavailable("Tính năng dịch chưa được bật trên máy chủ.")
    if source == AUTO:  # chat: the learner may type or speak any of the languages
        prompt = (
            f"Detect the language of the text and translate it into {LANGUAGE_NAMES[target]}. If it is already "
            f"in that language, return it unchanged.\nText:\n{text}"
        )
    else:
        prompt = (
            f"Translate from {LANGUAGE_NAMES[source]} into {LANGUAGE_NAMES[target]}.\n"
            f"Text:\n{text}"
        )
    if settings.GEMINI_API_KEY:  # a small fast model: the learner is waiting with the mic in hand
        raw, model = generator._gemini(prompt, system=SYSTEM, schema=SCHEMA, fail=FAIL,
                                       model=settings.GEMINI_TRANSLATE_MODEL, timeout=25)
    else:
        raw, model = generator._claude(prompt, system=SYSTEM, schema=SCHEMA, fail=FAIL)
    try:
        out = str(json.loads(raw).get("translation", "")).strip()
    except (ValueError, AttributeError) as e:
        raise AiUnavailable(FAIL) from e
    if not out or wrong_script(out, target):
        raise AiUnavailable(FAIL)
    return {"translation": out[:MAX_CHARS * 3], "reading": generator._reading(out, target),
            "source_reading": generator._reading(text, _script_of(text) if source == AUTO else source), "model": model}


def _script_of(text: str) -> str:
    """For pinyin of an auto-detected text: Chinese in the script its characters show ('' when not Chinese)."""
    if not HAN.search(text):
        return ""
    return "zh-Hant" if wrong_script(text, "zh-Hans") else "zh-Hans"


def wrong_script(text: str, language: str) -> bool:
    """Chinese written with characters that exist only in the other script (CC-CEDICT); unknown when the
    dictionary is not installed."""
    if not language.startswith("zh"):
        return False
    try:
        from apps.vocab.lang.sources import cedict

        ce = cedict()
    except FileNotFoundError:
        return False
    other = ce.traditional_only if language == "zh-Hans" else ce.simplified_only
    return any(ch in other for ch in text)


def verified_words(texts: dict[str, str], user) -> list[dict]:
    """Verified vocabulary found in the texts ({language: text}), longest match first, for "save to flashcards".
    Vietnamese is the learners' own language, so only English / Chinese words are offered."""
    from apps.vocab.services import visible_translations_q

    found: list[dict] = []
    seen: set[int] = set()
    for language, text in texts.items():
        if language in ("vi", AUTO) or not text:
            continue
        rows = WordTranslation.objects.filter(visible_translations_q(user), language_id=language)
        if language.startswith("zh"):
            chars = set(HAN.findall(text))
            rows = rows.filter(text__regex=r"^[一-鿿㐀-䶿]{1,6}$")
            vocab = {r.text: r for r in rows.order_by("-id") if set(r.text) <= chars}
            spans = _greedy(text, vocab, lambda t, i, n: t[i:i + n], 6)
        else:
            tokens = [m.group(0).lower() for m in WORD_RUN.finditer(text)]
            wanted = {" ".join(tokens[i:i + n]) for n in (1, 2, 3) for i in range(len(tokens))}
            vocab = {}
            for r in rows.annotate(key=Lower(Trim("text"))).filter(key__in=wanted).order_by("id"):
                vocab.setdefault(r.key, r)
            spans = _greedy(tokens, vocab, lambda t, i, n: " ".join(t[i:i + n]), 3)
        for tr in spans:
            if tr.word_id in seen:
                continue
            seen.add(tr.word_id)
            vi = WordTranslation.objects.filter(visible_translations_q(user), word_id=tr.word_id,
                                                language_id="vi").first()
            found.append({
                "word_id": tr.word_id, "language": language, "text": tr.text,
                "reading": tr.pinyin if language.startswith("zh") else tr.ipa,
                "meaning_vi": vi.text if vi else tr.meaning_vi,
                "lang": "zh" if language.startswith("zh") else language,
                "script": {"zh-Hans": "hans", "zh-Hant": "hant"}.get(language, ""),
                "unverified": tr.status != ReviewStatus.VERIFIED,
            })
            if len(found) >= MAX_WORDS:
                return found
    return found


def _greedy(seq, vocab: dict, piece, longest: int) -> list:
    out, i = [], 0
    while i < len(seq):
        for n in range(min(longest, len(seq) - i), 0, -1):
            hit = vocab.get(piece(seq, i, n))
            if hit:
                out.append(hit)
                i += n
                break
        else:
            i += 1
    return out
