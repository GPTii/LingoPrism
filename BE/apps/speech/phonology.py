"""Expected pronunciation of a verified text, in the phone symbols of the recogniser (docs/thiet-ke-luyen-noi.md).

The recogniser (wav2vec2 XLSR-53 espeak, AI/scripts/export_phoneme_model.py) was trained on espeak-ng transcriptions,
so espeak-ng gives the expected phones in exactly its conventions:
  * en – the English text, US voice;
  * zh – the verified pinyin, syllable by syllable (espeak reads numbered pinyin; a syllable it cannot read falls back
    to its character). Tones come from the verified pinyin, not from espeak (its Mandarin tone digits merge tone 1 and
    tone 4), and are checked on the pitch curve (tones.py);
  * vi – the Vietnamese text: written Vietnamese is phonemic, espeak's rules mark the 6 tones on the vowel
    (no mark = ngang, 2 huyền, ɜ sắc, 4 hỏi, 5 ngã, 6 nặng).

espeak-ng: the system library (Docker: apt install espeak-ng) or the espeakng-loader wheel (Windows development).
"""
import re
import threading
import unicodedata
from dataclasses import dataclass, field

TONE_CHARS = "123456ɜ"
VI_TONES = {"": "ngang", "2": "huyền", "ɜ": "sắc", "4": "hỏi", "5": "ngã", "6": "nặng"}
ZH_TONE_NAMES = {1: "thanh 1 (ngang cao)", 2: "thanh 2 (lên)", 3: "thanh 3 (xuống rồi lên)", 4: "thanh 4 (xuống)",
                 5: "thanh nhẹ"}
VOWEL_CHARS = set("aɑæɐəɚɜɛeiɪoɔʊuʌyøœɯɤɨɵɒäɝʉ")

_lock = threading.RLock()  # _phonemize holds it and calls _backend
_backends: dict = {}


class PhonemizerUnavailable(Exception):
    pass


def _backend(language: str):
    with _lock:
        if language not in _backends:
            try:
                from phonemizer.backend import EspeakBackend
                from phonemizer.backend.espeak.wrapper import EspeakWrapper

                try:  # Windows development: the bundled library; Linux / Docker: the system espeak-ng
                    import espeakng_loader

                    EspeakWrapper.set_library(espeakng_loader.get_library_path())
                    EspeakWrapper.set_data_path(espeakng_loader.get_data_path())
                except ImportError:
                    pass
                voice = {"en": "en-us", "zh": "cmn", "vi": "vi"}[language]
                _backends[language] = EspeakBackend(voice, preserve_punctuation=False, with_stress=False,
                                                    language_switch="keep-flags")
            except Exception as e:  # noqa: BLE001 - no espeak-ng: speaking practice is off, the rest of the app runs
                raise PhonemizerUnavailable(str(e)) from e
        return _backends[language]


def available() -> bool:
    try:
        _backend("en")
        return True
    except PhonemizerUnavailable:
        return False


def _phonemize(texts: list[str], language: str) -> list[list[list[str]]]:
    """texts -> per text, its words, each a list of phone tokens."""
    from phonemizer.separator import Separator

    sep = Separator(phone=" ", word=" | ", syllable="")
    with _lock:
        out = _backend(language).phonemize(texts, separator=sep, strip=True, njobs=1)
    return [[w.split() for w in o.split(" | ") if w.strip()] for o in out]


def split_tone(tok: str) -> tuple[str, str]:
    """'ɑ5' -> ('ɑ', '5'), 'aːɜ' -> ('aː', 'ɜ'); a lone 'ɜ' / 'ɜː' is the English vowel, not a tone."""
    if len(tok) > 1 and tok[-1] in TONE_CHARS and any(c in VOWEL_CHARS for c in tok[:-1]):
        return tok[:-1], tok[-1]
    return tok, ""


_UNIFY = {"g": "ɡ", "ɝ": "ɜ", "r": "ɹ", "ɐ": "a", "ä": "a", "ɫ": "l", "ʤ": "dʒ", "ʧ": "tʃ"}


def base(tok: str) -> str:
    """The comparable form of a phone: no tone, no length mark, a few spellings unified (ɡ/g, ɝ/ɜ, r/ɹ)."""
    t, _ = split_tone(tok)
    t = t.replace("ː", "").replace(":", "")
    return "".join(_UNIFY.get(c, c) for c in t) if len(t) > 1 else _UNIFY.get(t, t)


def is_vowel(tok: str) -> bool:
    b = base(tok)
    return bool(b) and b[0] in VOWEL_CHARS


@dataclass
class Unit:
    """One word (en) or syllable (zh, vi) of the text, as the learner sees it."""

    text: str
    phones: list[str]
    tone: str | int | None = None  # zh: 1-5 from the pinyin; vi: tone name; en: None
    reading: str = ""  # pinyin / IPA shown under the unit
    extra: dict = field(default_factory=dict)


# --- pinyin --------------------------------------------------------------------------------------------------------

_TONE_MARKS = {"ā": ("a", 1), "á": ("a", 2), "ǎ": ("a", 3), "à": ("a", 4), "ē": ("e", 1), "é": ("e", 2), "ě": ("e", 3),
               "è": ("e", 4), "ī": ("i", 1), "í": ("i", 2), "ǐ": ("i", 3), "ì": ("i", 4), "ō": ("o", 1), "ó": ("o", 2),
               "ǒ": ("o", 3), "ò": ("o", 4), "ū": ("u", 1), "ú": ("u", 2), "ǔ": ("u", 3), "ù": ("u", 4),
               "ǖ": ("ü", 1), "ǘ": ("ü", 2), "ǚ": ("ü", 3), "ǜ": ("ü", 4), "ń": ("n", 2), "ň": ("n", 3),
               "ǹ": ("n", 4)}


def numbered(syllable: str) -> tuple[str, int]:
    """'nǚ' -> ('nü', 3), 'ma5' -> ('ma', 5), 'ma' -> ('ma', 5) (no mark = neutral tone)."""
    s = syllable.strip().lower()
    m = re.fullmatch(r"([a-zü:v]+)([1-5])", s)
    if m:
        return m.group(1).replace("u:", "ü").replace("v", "ü"), int(m.group(2))
    tone, out = 5, []
    for ch in unicodedata.normalize("NFC", s):
        if ch in _TONE_MARKS:
            letter, tone = _TONE_MARKS[ch]
            out.append(letter)
        elif ch.isalpha() or ch == "ü":
            out.append(ch)
    return "".join(out), tone


def _is_han(ch: str) -> bool:
    return "一" <= ch <= "鿿" or "㐀" <= ch <= "䶿"


def zh_units(chars: str, pinyin: list[str]) -> list[Unit]:
    """chars: the Chinese text; pinyin: one verified syllable per character (marks or numbers)."""
    han = [c for c in chars if _is_han(c)]
    sylls = [numbered(p) for p in pinyin if p.strip()]
    if len(han) != len(sylls):
        han = han[:len(sylls)] + [""] * max(0, len(sylls) - len(han))
    words = _phonemize([f"{s.replace('ü', 'v')}{t}" for s, t in sylls], "zh")
    fallback = [i for i, w in enumerate(words) if not w or any("(" in p for ph in w for p in ph)]
    if fallback:  # a syllable espeak cannot read as pinyin: its character (the verified tone is kept anyway)
        again = _phonemize([han[i] or "啊" for i in fallback], "zh")
        for i, w in zip(fallback, again):
            words[i] = w
    units = []
    for (syl, tone), ch, w in zip(sylls, han, words):
        phones = [p for ph in w for p in ph if "(" not in p]
        units.append(Unit(ch or syl, phones, tone, f"{syl}{tone}"))
    return units


def vi_units(text: str) -> list[Unit]:
    sylls = [s for s in re.split(r"[\s\-]+", re.sub(r"[^\w\s\-]", " ", text)) if s]
    words = _phonemize(sylls, "vi")
    units = []
    for s, w in zip(sylls, words):
        phones = [p for ph in w for p in ph]
        tone = next((split_tone(p)[1] for p in phones if split_tone(p)[1]), "")
        units.append(Unit(s, phones, VI_TONES.get(tone, "ngang"), " ".join(phones)))
    return units


def en_units(text: str) -> list[Unit]:
    words = [w for w in re.split(r"\s+", text.strip()) if re.search(r"\w", w)]
    phon = _phonemize([text], "en")[0]
    if len(phon) == len(words):
        return [Unit(w, p, None, " ".join(p)) for w, p in zip(words, phon)]
    # numbers, contractions… split differently: one word at a time
    per = _phonemize(words, "en")
    return [Unit(w, [p for ph in pp for p in ph], None, " ".join(p for ph in pp for p in ph)) for w, pp in zip(words, per)]


def expected_units(text: str, language: str, pinyin: list[str] | None = None) -> list[Unit]:
    """language: en | vi | zh-Hans | zh-Hant."""
    if language.startswith("zh"):
        return zh_units(text, pinyin or [])
    if language == "vi":
        return vi_units(text)
    return en_units(text)
