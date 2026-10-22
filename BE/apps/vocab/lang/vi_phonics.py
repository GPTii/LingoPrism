"""Vietnamese orthography for early literacy (âm đầu + vần + thanh, đánh vần, luật chính tả).

All rules are deterministic properties of the Vietnamese writing system:
  * a syllable (tiếng) = optional initial (âm đầu) + rhyme (vần) + tone (thanh)
  * 'qu' and 'gi' are initials: quả = qu + a, gia = gi + a, gì = gi + i (one 'i' is written)
  * spelling rules: k / gh / ngh before i, e, ê (y for k); c / g / ng elsewhere; q only as 'qu'
Tone marks are placed with the same convention as the vocabulary data (vietnamese.normalize – "kiểu cũ").
"""
import unicodedata
from dataclasses import dataclass

from .vietnamese import _apply_tone, _split_tone

ONSETS = ["ngh", "ng", "gh", "gi", "kh", "nh", "ph", "qu", "th", "tr", "ch",
          "b", "c", "d", "đ", "g", "h", "k", "l", "m", "n", "p", "r", "s", "t", "v", "x"]
VOWELS = set("aăâeêioôơuưy")

TONE_MARKS = {"̀": "huyen", "́": "sac", "̉": "hoi", "̃": "nga", "̣": "nang"}
MARK_OF = {v: k for k, v in TONE_MARKS.items()}
TONES = ["ngang", "huyen", "sac", "hoi", "nga", "nang"]
TONE_LABEL = {"ngang": "thanh ngang", "huyen": "dấu huyền", "sac": "dấu sắc", "hoi": "dấu hỏi",
              "nga": "dấu ngã", "nang": "dấu nặng"}
TONE_SPELL = {"huyen": "huyền", "sac": "sắc", "hoi": "hỏi", "nga": "ngã", "nang": "nặng"}
TONE_SYMBOL = {"ngang": "", "huyen": "`", "sac": "´", "hoi": "ˀ", "nga": "~", "nang": "."}

# how an initial is pronounced when spelling (đánh vần) – Tiếng Việt 1
ONSET_SOUND = {
    "b": "bờ", "c": "cờ", "ch": "chờ", "d": "dờ", "đ": "đờ", "g": "gờ", "gh": "gờ", "gi": "di", "h": "hờ",
    "k": "ca", "kh": "khờ", "l": "lờ", "m": "mờ", "n": "nờ", "ng": "ngờ", "ngh": "ngờ", "nh": "nhờ", "p": "pờ",
    "ph": "phờ", "qu": "quờ", "r": "rờ", "s": "sờ", "t": "tờ", "th": "thờ", "tr": "trờ", "v": "vờ", "x": "xờ",
}
ONSET_NAME = {**ONSET_SOUND, "gh": "gờ kép", "ngh": "ngờ kép"}
VOWEL_SOUND = {"a": "a", "ă": "á", "â": "ớ", "e": "e", "ê": "ê", "i": "i", "o": "o", "ô": "ô", "ơ": "ơ",
               "u": "u", "ư": "ư", "y": "i"}
FINAL_SOUND = {"c": "cờ", "ch": "chờ", "m": "mờ", "n": "nờ", "ng": "ngờ", "nh": "nhờ", "p": "pờ", "t": "tờ",
               "i": "i", "y": "i", "o": "o", "u": "u"}
FRONT = ("i", "e", "ê", "y")  # vowels that require k / gh / ngh


@dataclass(frozen=True)
class Syllable:
    onset: str
    rhyme: str  # without tone mark
    tone: str  # one of TONES

    @property
    def base(self) -> str:
        return join(self.onset, self.rhyme)

    @property
    def text(self) -> str:
        return compose(self.onset, self.rhyme, self.tone)


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def parse(syllable: str) -> Syllable | None:
    """'bà' -> (b, a, huyen); 'quả' -> (qu, a, hoi); 'gì' -> (gi, i, huyen); 'ăn' -> ('', ăn, ngang)."""
    base, mark = _split_tone(_nfc(syllable.strip().lower()))
    tone = TONE_MARKS.get(mark, "ngang") if mark else "ngang"
    if not base or not any(c in VOWELS for c in base):
        return None
    onset = next((o for o in ONSETS if base.startswith(o)), "")
    rhyme = base[len(onset):]
    if onset == "gi":
        if not rhyme:  # gi, gì
            rhyme = "i"
        elif rhyme[0] not in VOWELS or rhyme[0] == "ê":  # gìn = gi + in, giếng = gi + iêng (one 'i' written)
            rhyme = "i" + rhyme
    elif onset == "qu" and not rhyme:
        return None
    if not rhyme or not any(c in VOWELS for c in rhyme):
        return None
    return Syllable(onset, rhyme, tone)


def join(onset: str, rhyme: str) -> str:
    """Write initial + rhyme without tone ('gi' + 'in' -> 'gin', 'gi' + 'i' -> 'gi')."""
    if onset == "gi" and rhyme.startswith("i") and (len(rhyme) == 1 or rhyme[1] not in VOWELS or rhyme[1] == "ê"):
        return "g" + rhyme
    return onset + rhyme


def compose(onset: str, rhyme: str, tone: str = "ngang") -> str:
    base = join(onset, rhyme)
    return _nfc(_apply_tone(base, MARK_OF.get(tone)))


def spelling_error(onset: str, rhyme: str) -> str | None:
    """Luật chính tả c/k/q, g/gh, ng/ngh. Returns the correct initial when (onset, rhyme) is misspelled."""
    front = rhyme.startswith(FRONT)
    if onset == "c" and front:
        return "k"
    if onset == "k" and not front:
        return "c"
    if onset == "g" and front and not rhyme.startswith("y"):
        return "gh"
    if onset == "gh" and not front:
        return "g"
    if onset == "ng" and front and not rhyme.startswith("y"):
        return "ngh"
    if onset == "ngh" and not front:
        return "ng"
    return None


def rhyme_parts(rhyme: str) -> tuple[str, str]:
    """Split a rhyme into vowel nucleus and final consonant: 'anh' -> ('a', 'nh'), 'uôi' -> ('uôi', '')."""
    for final in ("ng", "nh", "ch", "c", "m", "n", "p", "t"):
        if rhyme.endswith(final) and len(rhyme) > len(final):
            return rhyme[: -len(final)], final
    return rhyme, ""


def spell_rhyme(rhyme: str) -> list[str]:
    """'an' -> ['a', 'nờ', 'an']; 'a' -> ['a']; 'oa' -> ['o', 'a', 'oa']."""
    if len(rhyme) == 1:
        return [VOWEL_SOUND.get(rhyme, rhyme)]
    vowel, final = rhyme_parts(rhyme)
    steps = [VOWEL_SOUND.get(c, c) for c in vowel] if len(vowel) <= 2 else [vowel]
    if final:
        steps.append(FINAL_SOUND[final])
    return steps + [rhyme]


def spell(syllable: str) -> list[str]:
    """Đánh vần: 'bà' -> ['bờ', 'a', 'ba', 'huyền', 'bà']; 'ổi' -> ['ôi', 'hỏi', 'ổi']."""
    s = parse(syllable)
    if s is None:
        return [syllable]
    steps = [ONSET_SOUND[s.onset], s.rhyme, s.base] if s.onset else [s.rhyme]
    if s.tone != "ngang":
        steps += [TONE_SPELL[s.tone], s.text]
    return steps


def syllables_of(text: str) -> list[str]:
    import re

    return re.findall(r"[^\W\d_]+", _nfc(text.lower()))
