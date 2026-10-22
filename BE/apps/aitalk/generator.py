"""Writes the dialogue with Gemini (Google AI Studio, has a free tier) when GEMINI_API_KEY is set, otherwise with
Claude (Anthropic API) when ANTHROPIC_API_KEY is set; off when neither is.

The model only writes the sentences and their meaning; the reading of Chinese lines (pinyin) is computed
here with pypinyin, and every word comes from the verified vocabulary – the model never adds words to it."""
import json
import logging
import re

from django.conf import settings

log = logging.getLogger(__name__)

LANGUAGE_NAMES = {
    "en": "American English",
    "zh-Hans": "Mandarin Chinese written in Simplified characters (Mainland usage)",
    "zh-Hant": "Mandarin Chinese written in Traditional characters (Taiwan usage)",
    "vi": "Vietnamese",
}
LEVEL_HINTS = {
    1: "a complete beginner: very short sentences (max ~8 words), the most common words only",
    2: "an elementary learner: short everyday sentences",
    3: "an intermediate learner: natural everyday sentences",
    4: "an upper-intermediate learner: natural sentences, some variety",
}

SCHEMA = {
    "type": "object",
    "properties": {
        "title_vi": {"type": "string", "description": "Tên ngắn của tình huống, bằng tiếng Việt"},
        "lines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "speaker": {"type": "string", "enum": ["A", "B"]},
                    "text": {"type": "string"},
                    "translation": {"type": "string"},
                },
                "required": ["speaker", "text", "translation"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title_vi", "lines"],
    "additionalProperties": False,
}

SYSTEM = (
    "You write short practice dialogues for a language-learning app used by Vietnamese learners. "
    "The learner just photographed some objects; the dialogue is a small, realistic everyday scene where "
    "two people (A and B) talk about or use those objects. Use each given word exactly as written "
    "(same characters / spelling). Keep the content friendly and suitable for children. "
    "Write only in the requested language and script - never mix Simplified and Traditional characters."
)


HAN_RUN = re.compile(r"[一-鿿㐀-䶿]+")


class AiUnavailable(Exception):
    pass


def enabled() -> bool:
    return bool(settings.GEMINI_API_KEY or settings.ANTHROPIC_API_KEY)


def _reading(text: str, language: str) -> str:
    if not language.startswith("zh"):
        return ""
    from pypinyin import Style, pinyin

    from apps.vocab.lang import pinyin as py
    from apps.vocab.lang.sources import neutral_tone_words

    # pypinyin reads each character in context but misses most neutral tones (妈妈 mā mā); CC-CEDICT words
    # put them back (mā ma), longest word first. Tone sandhi of 一/不 from pypinyin is kept.
    neutral, side = neutral_tone_words(), "t:" if language == "zh-Hant" else "s:"
    out = []
    for run in HAN_RUN.findall(text):
        syl = [p[0].replace("v", "ü") for p in pinyin(run, style=Style.TONE3, neutral_tone_with_five=True)]
        i = 0
        while i < len(run):
            n = next((n for n in (4, 3, 2) if side + run[i:i + n] in neutral), 1)
            for k, tone in enumerate(neutral.get(side + run[i:i + n], ())):
                if tone == 5:
                    syl[i + k] = syl[i + k][:-1] + "5"
            i += n
        out += syl
    return py.numbered_to_marked(" ".join(out))


def generate(words: list[dict], language: str, level: int) -> dict:
    """words: [{"text": "苹果", "meaning_vi": "quả táo"}] → {"title_vi", "lines": [...], "model"}."""
    if not enabled():
        raise AiUnavailable("Tính năng hội thoại AI chưa được bật trên máy chủ.")
    gloss = "English" if language == "vi" else "Vietnamese"
    word_list = "\n".join(f"- {w['text']} ({w.get('meaning_vi') or ''})" for w in words)
    prompt = (
        f"Language of the dialogue: {LANGUAGE_NAMES[language]}.\n"
        f"Learner: {LEVEL_HINTS.get(level, LEVEL_HINTS[1])}.\n"
        f"Words from the photo:\n{word_list}\n\n"
        f"Write 4 to 6 lines that together use every word above at least once. "
        f"For each line give its {gloss} translation in `translation`."
    )
    text, model = _gemini(prompt) if settings.GEMINI_API_KEY else _claude(prompt)
    try:
        data = json.loads(text)
    except ValueError as e:
        raise AiUnavailable("Không tạo được hội thoại lúc này.") from e
    lines = [
        {"speaker": ln["speaker"], "text": ln["text"].strip(), "reading": _reading(ln["text"], language),
         "translation": ln["translation"].strip()}
        for ln in data.get("lines", []) if ln.get("text", "").strip()
    ][:8]
    if not lines:
        raise AiUnavailable("Không tạo được hội thoại cho ảnh này.")
    return {"title_vi": data.get("title_vi", "")[:200], "lines": lines, "model": model}


def _gemini(prompt: str) -> tuple[str, str]:
    import requests

    model = settings.GEMINI_MODEL
    try:
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key": settings.GEMINI_API_KEY},
            json={
                "systemInstruction": {"parts": [{"text": SYSTEM}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json", "responseJsonSchema": SCHEMA,
                                     "maxOutputTokens": 4000},
            },
            timeout=60,
        )
    except requests.RequestException as e:
        raise AiUnavailable("Máy chủ không kết nối được tới dịch vụ AI.") from e
    if res.status_code == 429:
        raise AiUnavailable("AI đang bận, thử lại sau ít phút.")
    if res.status_code != 200:
        log.warning("Gemini API error %s: %s", res.status_code, res.text[:300])
        raise AiUnavailable("Không tạo được hội thoại lúc này.")
    body = res.json()
    cand = (body.get("candidates") or [{}])[0]
    if cand.get("finishReason") not in (None, "STOP"):  # SAFETY, MAX_TOKENS, ... → nothing usable
        raise AiUnavailable("Không tạo được hội thoại cho ảnh này.")
    text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []) if not p.get("thought"))
    return text, body.get("modelVersion") or model


def _claude(prompt: str) -> tuple[str, str]:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=60.0, max_retries=1)
    try:
        response = client.beta.messages.create(
            model=settings.AI_TALK_MODEL,
            max_tokens=4000,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.RateLimitError as e:
        raise AiUnavailable("AI đang bận, thử lại sau ít phút.") from e
    except anthropic.APIStatusError as e:
        log.warning("Anthropic API error %s (request %s)", e.status_code, getattr(e, "request_id", ""))
        raise AiUnavailable("Không tạo được hội thoại lúc này.") from e
    except anthropic.APIConnectionError as e:
        raise AiUnavailable("Máy chủ không kết nối được tới dịch vụ AI.") from e

    if response.stop_reason in ("refusal", "max_tokens"):
        raise AiUnavailable("Không tạo được hội thoại cho ảnh này.")
    return next((b.text for b in response.content if b.type == "text"), ""), response.model
