"""Turn an exercise file (PDF, photo of a worksheet, Word, text) into draft questions with the AI model.

The questions come back as a draft for the group leader to check and edit before giving the assignment – the model
copies the exercises it reads, it does not invent new ones. PDF and images go to Gemini as they are (it reads them,
handwriting and scans included); Word and text files are sent as their text. Nothing is stored here.
"""

import base64
import json
import re
import zipfile
from pathlib import Path

from django.conf import settings

from apps.aitalk import generator
from apps.aitalk.generator import AiUnavailable

MAX_QUESTIONS = 60
MAX_TEXT = 60_000
FAIL = "Không đọc được bài tập trong file này. Thử file rõ hơn hoặc tự nhập câu hỏi."

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "enum": ["mcq", "fill", "essay"]},
                    "prompt": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"text": {"type": "string"}, "correct": {"type": "boolean"}},
                            "required": ["text", "correct"],
                        },
                    },
                    "accepted_answers": {"type": "array", "items": {"type": "string"}},
                    "points": {"type": "number"},
                    "explanation": {"type": "string"},
                },
                "required": ["kind", "prompt"],
            },
        },
    },
    "required": ["questions"],
}

SYSTEM = (
    "You turn a teacher's exercise sheet into questions for a language-learning app. Copy every exercise item in the "
    "document, in its order and its own language, word for word – never invent, translate or drop items. "
    "mcq: a question with choices; give every choice in `options`, `correct` true for exactly one (use the answer key "
    "if the document has one, otherwise the answer you are sure of). fill: a gap to fill or a short answer; "
    "`accepted_answers` lists every correct form. essay: anything answered freely (writing, translating a sentence, "
    "describing a picture). Put an exercise's general instruction in front of its first item's prompt. "
    "`points`: from the document if given, else 1. `title`: the sheet's title if it has one."
)

MIME = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".heic": "image/heic",
}


def _docx_text(raw: bytes) -> str:
    """The paragraphs of a .docx (its word/document.xml) – no extra library needed."""
    import io

    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
    paras = re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S)
    return "\n".join("".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p, flags=re.S)) for p in paras).strip()


def read_questions(upload) -> dict:
    """-> {"title", "questions": [{kind, prompt, options, accepted_answers, points, explanation}], "model"}"""
    ext = Path(upload.name).suffix.lower()
    raw = upload.read()
    parts, text = None, ""
    if ext in MIME:
        if not settings.GEMINI_API_KEY:
            raise AiUnavailable("Đọc PDF / ảnh cần Gemini (GEMINI_API_KEY) trên máy chủ.")
        parts = [{"inline_data": {"mime_type": MIME[ext], "data": base64.b64encode(raw).decode()}}]
    elif ext == ".docx":
        try:
            text = _docx_text(raw)
        except (KeyError, zipfile.BadZipFile) as e:
            raise AiUnavailable("File Word bị lỗi.") from e
    elif ext == ".txt":
        text = raw.decode("utf-8", "ignore")
    else:
        raise AiUnavailable("AI đọc được PDF, ảnh, Word (.docx) hoặc .txt.")
    if parts is None and not text.strip():
        raise AiUnavailable("File không có chữ để đọc.")
    prompt = "Exercise sheet:" if parts else f"Exercise sheet:\n{text[:MAX_TEXT]}"
    if not generator.enabled():
        raise AiUnavailable("Máy chủ chưa bật AI.")
    if settings.GEMINI_API_KEY:
        try:
            out, model = generator._gemini(prompt, system=SYSTEM, schema=SCHEMA, fail=FAIL, timeout=120, parts=parts)
        except AiUnavailable:  # the big model is often overloaded on the free tier: the small one reads well too
            out, model = generator._gemini(
                prompt,
                system=SYSTEM,
                schema=SCHEMA,
                fail=FAIL,
                timeout=120,
                parts=parts,
                model=settings.GEMINI_TRANSLATE_MODEL,
            )
    else:
        out, model = generator._claude(prompt, system=SYSTEM, schema=SCHEMA, fail=FAIL)
    try:
        data = json.loads(out)
    except ValueError as e:
        raise AiUnavailable(FAIL) from e
    questions = []
    for q in (data.get("questions") or [])[:MAX_QUESTIONS]:
        kind = q.get("kind") if q.get("kind") in ("mcq", "fill", "essay") else "essay"
        prompt_text = str(q.get("prompt") or "").strip()
        if not prompt_text:
            continue
        options = [
            {"text": str(o.get("text", "")).strip(), "correct": bool(o.get("correct"))}
            for o in (q.get("options") or [])
            if str(o.get("text", "")).strip()
        ]
        if kind == "mcq" and (len(options) < 2 or sum(o["correct"] for o in options) != 1):
            # no clear key: keep the choices, let the leader tick the right one
            for o in options:
                o["correct"] = False
        accepted = [str(x).strip() for x in (q.get("accepted_answers") or []) if str(x).strip()]
        try:
            points = max(0.25, min(float(q.get("points") or 1), 100))
        except (TypeError, ValueError):
            points = 1
        questions.append(
            {
                "kind": kind,
                "prompt": prompt_text,
                "options": options if kind == "mcq" else [],
                "accepted_answers": accepted if kind == "fill" else [],
                "points": points,
                "explanation": str(q.get("explanation") or "").strip(),
            }
        )
    if not questions:
        raise AiUnavailable(FAIL)
    return {"title": str(data.get("title") or "").strip()[:150], "questions": questions, "model": model}
