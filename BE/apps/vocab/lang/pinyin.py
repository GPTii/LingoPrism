"""Pinyin utilities: numbered <-> tone marks, syllable parsing and pinyin -> Zhuyin (Bopomofo).

All conversions are deterministic table lookups so they can be used to cross-check
readings coming from different dictionaries.
"""
import re
import unicodedata

TONE_MARKS = {
    "a": "āáǎà", "e": "ēéěè", "i": "īíǐì", "o": "ōóǒò", "u": "ūúǔù", "ü": "ǖǘǚǜ",
}
_MARKED = {m: (base, i + 1) for base, marks in TONE_MARKS.items() for i, m in enumerate(marks)}

SYLLABLE_RE = re.compile(r"^([a-zü]+?)([1-5])$")


def _place_tone(syllable: str, tone: int) -> str:
    """Apply the standard tone-mark placement rules to a lowercase syllable."""
    if tone in (0, 5):
        return syllable
    for vowel in ("a", "e"):
        if vowel in syllable:
            i = syllable.index(vowel)
            return syllable[:i] + TONE_MARKS[vowel][tone - 1] + syllable[i + 1:]
    if "ou" in syllable:
        i = syllable.index("o")
        return syllable[:i] + TONE_MARKS["o"][tone - 1] + syllable[i + 1:]
    for i in range(len(syllable) - 1, -1, -1):
        ch = syllable[i]
        if ch in TONE_MARKS:
            return syllable[:i] + TONE_MARKS[ch][tone - 1] + syllable[i + 1:]
    return syllable


def normalize_numbered(text: str) -> str:
    """CC-CEDICT style ("lu:4 se4", "Ma3") -> lowercase, ü, single spaces."""
    text = text.replace("u:", "ü").replace("v", "ü").replace("U:", "Ü")
    return " ".join(text.lower().split())


def numbered_to_marked(text: str) -> str:
    out = []
    for syl in normalize_numbered(text).split():
        m = SYLLABLE_RE.match(syl)
        if not m:
            out.append(syl)
            continue
        out.append(_place_tone(m.group(1), int(m.group(2))))
    return " ".join(out)


def marked_to_numbered(text: str) -> str:
    """'mǎ líng shǔ' -> 'ma3 ling2 shu3' (neutral tone -> 5)."""
    text = unicodedata.normalize("NFC", text.lower())
    out = []
    for syl in re.split(r"[\s\-']+", text):
        if not syl:
            continue
        tone = 5
        plain = []
        for ch in syl:
            if ch in _MARKED:
                base, tone = _MARKED[ch]
                plain.append(base)
            else:
                plain.append(ch)
        out.append("".join(plain) + str(tone))
    return " ".join(out)


def syllables(numbered: str) -> list[str]:
    return [s for s in normalize_numbered(numbered).split() if s]


def comparable(text: str) -> str:
    """Normalize any pinyin form (marked or numbered) for equality checks."""
    if re.search(r"[1-5]", text):
        return normalize_numbered(text)
    return marked_to_numbered(text)


# ---------------------------------------------------------------- Zhuyin

INITIALS = {
    "zh": "ㄓ", "ch": "ㄔ", "sh": "ㄕ", "b": "ㄅ", "p": "ㄆ", "m": "ㄇ", "f": "ㄈ", "d": "ㄉ", "t": "ㄊ",
    "n": "ㄋ", "l": "ㄌ", "g": "ㄍ", "k": "ㄎ", "h": "ㄏ", "j": "ㄐ", "q": "ㄑ", "x": "ㄒ", "r": "ㄖ",
    "z": "ㄗ", "c": "ㄘ", "s": "ㄙ",
}
FINALS = {
    "a": "ㄚ", "o": "ㄛ", "e": "ㄜ", "ê": "ㄝ", "ai": "ㄞ", "ei": "ㄟ", "ao": "ㄠ", "ou": "ㄡ", "an": "ㄢ",
    "en": "ㄣ", "ang": "ㄤ", "eng": "ㄥ", "er": "ㄦ", "ong": "ㄨㄥ",
    "i": "ㄧ", "ia": "ㄧㄚ", "ie": "ㄧㄝ", "iao": "ㄧㄠ", "iu": "ㄧㄡ", "ian": "ㄧㄢ", "in": "ㄧㄣ",
    "iang": "ㄧㄤ", "ing": "ㄧㄥ", "iong": "ㄩㄥ", "io": "ㄧㄛ",
    "u": "ㄨ", "ua": "ㄨㄚ", "uo": "ㄨㄛ", "uai": "ㄨㄞ", "ui": "ㄨㄟ", "uan": "ㄨㄢ", "un": "ㄨㄣ",
    "uang": "ㄨㄤ", "ueng": "ㄨㄥ",
    "ü": "ㄩ", "üe": "ㄩㄝ", "üan": "ㄩㄢ", "ün": "ㄩㄣ",
}
# y-/w- spellings rewritten to their underlying finals
YW = {
    "yi": "i", "ya": "ia", "ye": "ie", "yao": "iao", "you": "iu", "yan": "ian", "yin": "in",
    "yang": "iang", "ying": "ing", "yong": "iong", "yo": "io",
    "wu": "u", "wa": "ua", "wo": "uo", "wai": "uai", "wei": "ui", "wan": "uan", "wen": "un",
    "wang": "uang", "weng": "ueng",
    "yu": "ü", "yue": "üe", "yuan": "üan", "yun": "ün",
}
TONE_SUFFIX = {1: "", 2: "ˊ", 3: "ˇ", 4: "ˋ", 5: ""}


def _syllable_to_zhuyin(base: str) -> str | None:
    erhua = False
    if base.endswith("r") and base not in ("er",) and len(base) > 1:
        base, erhua = base[:-1], True
    if base in ("zhi", "chi", "shi", "ri", "zi", "ci", "si"):
        out = INITIALS[base[:-1]]
    elif base in YW:
        out = FINALS[YW[base]]
    elif base in FINALS:
        out = FINALS[base]
    else:
        initial = next((i for i in ("zh", "ch", "sh") if base.startswith(i)), base[:1])
        if initial not in INITIALS:
            return None
        final = base[len(initial):]
        if initial in ("j", "q", "x") and final.startswith("u"):
            final = "ü" + final[1:]
        if final not in FINALS:
            return None
        out = INITIALS[initial] + FINALS[final]
    return out + ("ㄦ" if erhua else "")


def numbered_to_zhuyin(numbered: str) -> str | None:
    """'ma3 ling2 shu3' -> 'ㄇㄚˇ ㄌㄧㄥˊ ㄕㄨˇ'. Neutral tone is written with a leading '˙'."""
    out = []
    for syl in syllables(numbered):
        m = SYLLABLE_RE.match(syl)
        if not m:
            return None
        z = _syllable_to_zhuyin(m.group(1))
        if z is None:
            return None
        tone = int(m.group(2))
        out.append(("˙" + z) if tone == 5 else z + TONE_SUFFIX[tone])
    return " ".join(out)


def normalize_zhuyin(text: str) -> str:
    """Make zhuyin comparable: neutral-tone dot always leading, single spaces, no ideographic spaces."""
    parts = []
    for syl in text.replace("　", " ").split():
        if syl.endswith("˙"):
            syl = "˙" + syl[:-1]
        parts.append(syl)
    return " ".join(parts)
