"""Exercise generation and checking for the Vietnamese early-literacy course.

Every graded exercise carries a signed token with its expected answer, so checking is stateless and the client
cannot forge answers. Exercise types (all audio-first, no English):
  listen_choose – hear a syllable / word, tap the written form
  find_unit     – which initial / rhyme / tone does this syllable have?
  build         – hear a syllable, build it from initial + rhyme + tone
  rule          – c or k? g or gh? ng or ngh? (luật chính tả)
  dictation     – hear a word (picture as hint) and write it
  sentence      – hear a short sentence and write it (from lesson 17, review lessons)
"""
import random
import uuid

from django.core import signing

from apps.vocab.lang import vi_phonics as ph
from apps.vocab.lang import vietnamese
from apps.vocab.models import ReviewStatus, WordTranslation

from . import curriculum as cur

SALT = "literacy.v1"
MAX_EXERCISES = 14
TTS = "vi-VN"


def sign(**data) -> str:
    return signing.dumps(data, salt=SALT, compress=True)


def unsign(token: str, max_age: int = 6 * 3600) -> dict:
    return signing.loads(token, salt=SALT, max_age=max_age)


# ------------------------------------------------------------------ helpers

def _weighted_pick(items: list, k: int, rng: random.Random) -> list:
    """Prefer frequent syllables (they come first) but keep some variety."""
    head = items[: max(k * 4, 12)]
    return rng.sample(head, min(k, len(head)))


def _examples(unit: cur.Unit, n: int) -> list[ph.Syllable]:
    """Common syllables containing the unit; dictionary-only rare ones only when no common one exists (oăn, uych)."""
    matching = [(s, c) for s, c in cur.readable_syllables(n) if unit.matches(s)]
    common = [s for s, c in matching if c > 0]
    return common or [s for s, _ in matching]


def _words(n: int) -> list[dict]:
    """Vocabulary words (with a picture) a child can read at lesson n."""
    out = []
    for tr in WordTranslation.objects.filter(language_id="vi", status=ReviewStatus.VERIFIED).select_related("word"):
        image = tr.word.image.url if tr.word.image else tr.word.image_url
        if tr.word.audience == "adult" or not (tr.word.emoji or image):
            continue
        if cur.readable_text(tr.text, n):
            out.append({"id": tr.word_id, "text": tr.text, "emoji": tr.word.emoji, "image": image or None})
    return out


def spell_payload(s: ph.Syllable) -> dict:
    return {"text": s.text, "onset": s.onset, "rhyme": s.rhyme, "tone": s.tone, "spell": ph.spell(s.text)}


def _options(answer: str, pool: list[str], k: int, rng: random.Random) -> list[str]:
    others = [p for p in dict.fromkeys(pool) if p != answer]
    opts = rng.sample(others, min(k - 1, len(others))) + [answer]
    rng.shuffle(opts)
    return opts


def _similar(target: ph.Syllable, n: int) -> list[str]:
    """Syllables that differ from the target in exactly one part – good listening distractors."""
    out = []
    for s, c in cur.readable_syllables(n)[:800]:
        if c == 0:
            continue
        diff = (s.onset != target.onset) + (s.rhyme != target.rhyme) + (s.tone != target.tone)
        if diff == 1:
            out.append(s.text)
    return out


# ------------------------------------------------------------------ exercise builders

def listen_choose(s: ph.Syllable, n: int, rng, ctx) -> dict | None:
    pool = _similar(s, n)
    if len(pool) < 2:
        return None
    return {"type": "listen_choose", "tts": {"text": s.text, "locale": TTS}, "options": _options(s.text, pool, 4, rng),
            "token": sign(t="listen_choose", a=s.text, **ctx)}


def find_unit(s: ph.Syllable, unit: cur.Unit, n: int, rng, ctx) -> dict | None:
    t = cur.taught_until(n)
    if unit.kind == "thanh":
        pool, answer, ask = [ph.TONE_LABEL[x] for x in ["ngang", *sorted(t.tones)]], ph.TONE_LABEL[s.tone], "dấu thanh"
    elif unit.kind == "van" or unit.is_vowel:
        pool, answer, ask = sorted(t.rhymes | t.vowels), s.rhyme, "vần"
    else:
        pool, answer, ask = sorted(t.onsets), s.onset, "âm đầu"
    if len(set(pool)) < 2:
        return None
    return {"type": "find_unit", "question": f"Tiếng “{s.text}” có {ask} nào?", "syllable": s.text,
            "tts": {"text": s.text, "locale": TTS}, "options": _options(answer, pool, 4, rng),
            "token": sign(t="find_unit", a=answer, **ctx)}


def build(s: ph.Syllable, n: int, rng, ctx) -> dict | None:
    t = cur.taught_until(n)
    onsets = _options(s.onset or "∅", [o or "∅" for o in sorted(t.onsets)] + ["∅"], 3, rng)
    rhymes = _options(s.rhyme, sorted(t.rhymes | t.vowels), 3, rng)
    tones = ["ngang", *[x for x in ph.TONES if x in t.tones]]
    if len(rhymes) < 2:
        return None
    return {"type": "build", "tts": {"text": s.text, "locale": TTS},
            "onsets": onsets, "rhymes": rhymes,
            "tones": [{"code": x, "label": ph.TONE_LABEL[x], "symbol": ph.TONE_SYMBOL[x]} for x in tones],
            "token": sign(t="build", a=s.text, **ctx)}


def rule(s: ph.Syllable, pair: tuple[str, str], rng, ctx) -> dict:
    return {"type": "rule", "tts": {"text": s.text, "locale": TTS},
            "question": "Chọn chữ đúng để điền vào chỗ trống",
            "pattern": "_" + ph.compose("", s.rhyme, s.tone), "options": list(pair),
            "token": sign(t="rule", a=s.onset, w=s.text, **ctx)}


def dictation(word: dict | None, s: ph.Syllable | None, ctx) -> dict:
    text = word["text"] if word else s.text
    return {"type": "dictation", "tts": {"text": text, "locale": TTS}, "emoji": word["emoji"] if word else "",
            "image": word["image"] if word else None,
            "syllables": len(ph.syllables_of(text)), "token": sign(t="dictation", a=text, **ctx)}


def sentence(item: dict, ctx) -> dict:
    return {"type": "sentence", "tts": {"text": item["text"], "locale": TTS}, "syllables": item["syllables"],
            "source": {"name": "Tatoeba", "id": item["id"], "license": "CC BY 2.0 FR",
                       "url": f"https://tatoeba.org/sentences/show/{item['id']}"},
            "token": sign(t="sentence", a=item["text"], **ctx)}


# ------------------------------------------------------------------ lesson

def intro(unit: cur.Unit, n: int) -> dict:
    ex = _examples(unit, n)
    words = [w for w in _words(n) if any(unit.matches(p) for p in map(ph.parse, ph.syllables_of(w["text"])) if p)]
    return {"type": "intro", "unit": unit.payload(),
            "examples": [spell_payload(s) for s in ex[:4]], "words": words[:4],
            "rhyme_spell": ph.spell_rhyme(unit.code) if unit.kind == "van" else []}


def build_lesson(n: int, seed: int | None = None) -> dict:
    lesson = cur.lesson(n)
    rng = random.Random(seed)
    session = uuid.uuid4().hex[:12]
    exercises: list[dict] = []
    idx = 0

    def ctx(unit: cur.Unit | None):
        nonlocal idx
        idx += 1
        return {"l": n, "s": session, "i": idx, "u": f"{unit.kind}:{unit.code}" if unit else "review"}

    units = lesson["units"]
    words = _words(n)
    for unit in units:
        ex = _examples(unit, n)
        if not ex:
            continue
        picks = _weighted_pick(ex, 3, rng)
        for s in picks[:2]:
            if item := listen_choose(s, n, rng, ctx(unit)):
                exercises.append(item)
        if item := find_unit(picks[-1], unit, n, rng, ctx(unit)):
            exercises.append(item)
        if item := build(rng.choice(picks), n, rng, ctx(unit)):
            exercises.append(item)
        unit_words = [w for w in words if any(unit.matches(p) for p in map(ph.parse, ph.syllables_of(w["text"])) if p)]
        if unit_words:
            exercises.append(dictation(rng.choice(unit_words), None, ctx(unit)))
        else:
            exercises.append(dictation(None, rng.choice(picks), ctx(unit)))

    if lesson.get("rule"):
        a, b = lesson["rule"]
        candidates = [s for s, c in cur.readable_syllables(n)[:600] if c > 0 and s.onset in (a, b)]
        for s in rng.sample(candidates, min(3, len(candidates))):
            exercises.append(rule(s, (a, b), rng, ctx(None)))

    if n >= 17:
        sentences = [x for x in cur.corpus()["sentences"] if cur.readable_text(x["text"], n)]
        if not lesson.get("review"):
            sentences = [x for x in sentences
                         if any(u.matches(p) for u in units for p in map(ph.parse, ph.syllables_of(x["text"])) if p)]
        sentences = [x for x in sentences if x["syllables"] <= (6 if n < 40 else 8)]
        for item in rng.sample(sentences, min(2 if not lesson.get("review") else 8, len(sentences))):
            exercises.append(sentence(item, ctx(None)))

    seen, unique = set(), []
    for e in exercises:
        key = (e["type"], unsign(e["token"])["a"])
        if key not in seen:
            seen.add(key)
            unique.append(e)
    rng.shuffle(unique)
    # keep every exercise type represented when a lesson has many units (round-robin over types)
    by_type: dict[str, list] = {}
    for e in unique:
        by_type.setdefault(e["type"], []).append(e)
    exercises = []
    while len(exercises) < MAX_EXERCISES and any(by_type.values()):
        for items in by_type.values():
            if items and len(exercises) < MAX_EXERCISES:
                exercises.append(items.pop())
    # listening first, writing last
    order = {"listen_choose": 0, "find_unit": 1, "build": 2, "rule": 3, "dictation": 4, "sentence": 5}
    exercises.sort(key=lambda e: order[e["type"]])
    return {"n": n, "title": lesson["title"], "session": session, "units": [u.payload() for u in units],
            "intro": [intro(u, n) for u in units], "exercises": exercises}


# ------------------------------------------------------------------ checking

def _norm(text: str) -> str:
    return " ".join(ph.syllables_of(vietnamese.normalize(text)))


def compare_text(expected: str, given: str) -> list[dict]:
    """Per-syllable feedback for dictation: [{"expected": "mèo", "given": "meo", "ok": False}, …]."""
    exp, got = ph.syllables_of(vietnamese.normalize(expected)), ph.syllables_of(vietnamese.normalize(given))
    out = []
    for i, e in enumerate(exp):
        g = got[i] if i < len(got) else ""
        item = {"expected": e, "given": g, "ok": e == g}
        if not item["ok"] and g:
            pe, pg = ph.parse(e), ph.parse(g)
            if pe and pg:
                item["hint"] = ("sai dấu thanh" if (pe.onset, pe.rhyme) == (pg.onset, pg.rhyme) else
                                "sai âm đầu" if pe.rhyme == pg.rhyme else "sai vần" if pe.onset == pg.onset else "")
        out.append(item)
    for g in got[len(exp):]:
        out.append({"expected": "", "given": g, "ok": False})
    return out


def check(data: dict, answer) -> tuple[bool, dict]:
    kind, expected = data["t"], data["a"]
    if kind == "build":
        a = answer if isinstance(answer, dict) else {}
        onset = "" if a.get("onset") in (None, "∅") else str(a.get("onset"))
        given = ph.compose(onset, str(a.get("rhyme", "")), str(a.get("tone", "ngang")))
        ok = given == expected
        return ok, {"expected": expected, "given": given, "spell": ph.spell(expected)}
    if kind in ("dictation", "sentence"):
        diff = compare_text(expected, str(answer))
        ok = _norm(str(answer)) == _norm(expected)
        return ok, {"expected": expected, "diff": diff}
    if kind == "rule":
        return str(answer) == expected, {"expected": expected, "word": data.get("w", ""), "spell": ph.spell(data.get("w", ""))}
    ok = str(answer).strip() == expected
    extra = {"expected": expected}
    if kind == "listen_choose" and (s := ph.parse(expected)):
        extra["spell"] = ph.spell(s.text)
    return ok, extra
