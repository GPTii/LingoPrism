"""Tokenising and cross-checking example sentences (Tatoeba) – see PLAN.md §3b.

Chinese sentences are segmented with CC-CEDICT (forward maximum matching on the sentence's own script),
pinyin comes from Tatoeba's transcription and is aligned one syllable per Han character. A sentence is only
`verified` when its pinyin was reviewed by a Tatoeba member or agrees with an independent reading (pypinyin),
and – for zh-Hant – no word has a different Taiwan reading in CC-CEDICT.
"""
import re
from collections import Counter
from functools import lru_cache
import unicodedata
from dataclasses import dataclass, field

from . import pinyin as py
from . import sources

HAN_RE = re.compile(r"[一-鿿㐀-䶿\U00020000-\U0002a6df]")
EN_WORD_RE = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)*")
VI_WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
MAX_WORD = 8
SANDHI_CHARS = set("一不")


@dataclass
class ZhSentence:
    tokens: list[dict] = field(default_factory=list)  # {"t": text, "p": marked pinyin, "z": zhuyin} or {"t": punct, "x": 1}
    numbered: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def han_count(text: str) -> int:
    return len(HAN_RE.findall(text))


def pinyin_syllables(transcription: str) -> list[str]:
    """'Wo3men5 gai1 zou3 le5.' -> ['wo3', 'men5', 'gai1', 'zou3', 'le5']"""
    text = transcription.lower().replace("u:", "ü").replace("v", "ü")
    return [m.group(0) for m in re.finditer(r"[a-zü]+?[1-5]", text)]


def segment_zh(text: str, script: str) -> list[str]:
    """Forward maximum matching against CC-CEDICT words written in the sentence's script."""
    ced = sources.cedict()
    lexicon = ced.by_simp if script == "hans" else ced.by_trad
    out, i = [], 0
    while i < len(text):
        ch = text[i]
        if not HAN_RE.match(ch):
            j = i + 1
            if ch.isalnum():
                while j < len(text) and text[j].isalnum() and not HAN_RE.match(text[j]):
                    j += 1
            out.append(text[i:j])
            i = j
            continue
        for size in range(min(MAX_WORD, len(text) - i), 0, -1):
            piece = text[i:i + size]
            if size == 1 or piece in lexicon:
                out.append(piece)
                i += size
                break
    return out


def _equivalent(chars: str, a: list[str], b: list[str]) -> bool:
    """Same syllables; neutral tone and the tone sandhi of 一/不 are not counted as differences."""
    if len(a) != len(b):
        return False
    for ch, x, y in zip(chars, a, b):
        if x == y:
            continue
        if x[:-1] != y[:-1]:
            return False
        if "5" in (x[-1], y[-1]) or ch in SANDHI_CHARS:
            continue
        return False
    return True


def independent_reading(text: str) -> list[str]:
    from pypinyin import Style, pinyin

    hans = "".join(HAN_RE.findall(text))
    return [p[0].replace("v", "ü") for p in pinyin(hans, style=Style.TONE3, neutral_tone_with_five=True)]


@lru_cache(maxsize=1)
def _wrong_script_chars() -> dict[str, set[str]]:
    """Characters that almost only occur as the *other* script's form.

    Besides characters exclusive to one side (CC-CEDICT), catch the ones that also exist as a rare character
    of their own: 圣 is the simplified form of 聖 in 100+ words but a traditional character in only a couple,
    so 圣 inside a traditional sentence is a mixing error.
    """
    ced = sources.cedict()
    as_simp, in_trad, as_trad, in_simp = Counter(), Counter(), Counter(), Counter()
    for trad, entries in ced.by_trad.items():
        in_trad.update(set(trad))
        for e in entries:
            if len(e.simplified) == len(trad):
                as_simp.update({s for s, t in zip(e.simplified, trad) if s != t})
                as_trad.update({t for s, t in zip(e.simplified, trad) if s != t})
    for simp in ced.by_simp:
        in_simp.update(set(simp))

    def rare(conv: Counter, own: Counter) -> set[str]:
        return {c for c, n in conv.items() if n >= 10 and own[c] < min(20, n * 0.1)}

    return {
        "hant": ced.simplified_only | rare(as_simp, in_trad),
        "hans": ced.traditional_only | rare(as_trad, in_simp),
    }


def build_zh(text: str, script: str, transcription: str, reviewed: bool) -> ZhSentence:
    out = ZhSentence()
    ced = sources.cedict()
    wrong_script = _wrong_script_chars()[script]
    bad = sorted({c for c in text if c in wrong_script})
    if bad:
        out.errors.append(f"Có chữ {'phồn' if script == 'hans' else 'giản'} thể trong câu {script}: {''.join(bad)}")
    lexicon = ced.by_simp if script == "hans" else ced.by_trad
    unknown = sorted({c for c in HAN_RE.findall(text) if c not in lexicon})
    if unknown:
        out.errors.append(f"Chữ không có trong CC-CEDICT ({script}): {''.join(unknown)}")

    syls = pinyin_syllables(transcription)
    hans_chars = "".join(HAN_RE.findall(text))
    if len(syls) != len(hans_chars):
        out.errors.append(f"Pinyin Tatoeba không khớp số chữ ({len(syls)} âm tiết / {len(hans_chars)} chữ)")
        return out
    out.numbered = " ".join(syls)
    if not reviewed:
        if not _equivalent(hans_chars, syls, independent_reading(text)):
            out.errors.append("Pinyin tự sinh của Tatoeba khác cách đọc đối chiếu (pypinyin) – cần duyệt tay")
        else:
            out.warnings.append("Pinyin tự sinh, đã khớp đối chiếu pypinyin")

    k = 0
    for piece in segment_zh(text, script):
        n = han_count(piece)
        if n == 0:
            out.tokens.append({"t": piece, "x": 1} if not piece.strip() or not piece[0].isalnum() else {"t": piece})
            continue
        numbered = " ".join(syls[k:k + n])
        k += n
        tok = {"t": piece, "p": py.numbered_to_marked(numbered)}
        if script == "hant":
            tok["z"] = py.numbered_to_zhuyin(numbered) or ""
            for entry in lexicon.get(piece, []):
                tw = entry.taiwan_pinyin
                if tw and py.normalize_numbered(tw) != numbered and entry.pinyin == numbered:
                    out.errors.append(f"{piece}: Đài Loan đọc {py.numbered_to_marked(tw)}, câu ghi {tok['p']}")
        out.tokens.append(tok)
    return out


def tokens_latin(text: str, lang: str) -> list[dict]:
    """English: words incl. contractions; Vietnamese: syllables. Punctuation kept as separate tokens."""
    rx = EN_WORD_RE if lang == "en" else VI_WORD_RE
    out, pos = [], 0
    text = unicodedata.normalize("NFC", text)
    for m in rx.finditer(text):
        gap = text[pos:m.start()].strip()
        if gap:
            out.append({"t": gap, "x": 1})
        out.append({"t": m.group(0)})
        pos = m.end()
    tail = text[pos:].strip()
    if tail:
        out.append({"t": tail, "x": 1})
    return out


def word_spans(tokens: list[dict], target: str, lang: str) -> list[int]:
    """Indexes of the tokens forming `target` (first occurrence), [] if absent."""
    words = [(i, t["t"]) for i, t in enumerate(tokens) if not t.get("x")]
    if lang.startswith("zh"):
        return [i for i, w in words if w == target][:1]
    parts = (EN_WORD_RE if lang == "en" else VI_WORD_RE).findall(unicodedata.normalize("NFC", target))
    parts = [p.lower() for p in parts]
    if not parts:
        return []
    for start in range(len(words) - len(parts) + 1):
        if [w.lower() for _, w in words[start:start + len(parts)]] == parts:
            return [i for i, _ in words[start:start + len(parts)]]
    return []


def normalize_answer(text: str) -> str:
    """For comparing arranged sentences: case-, space- and punctuation-insensitive."""
    text = unicodedata.normalize("NFC", text).lower().replace("’", "'")
    return "".join(ch for ch in text if ch.isalnum() or ch == "'")
