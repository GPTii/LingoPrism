"""Early-literacy curriculum for Vietnamese children (học đọc – viết tiếng Việt).

Order follows the usual progression of Tiếng Việt 1: single letters with the tones, then digraph initials
(ch, gh, ngh…), then rhymes (vần). A syllable is *readable* at lesson n when its initial, rhyme and tone have all
been taught in lessons 1..n – exercises only ever use readable, real syllables (seed/cache/vi_corpus.json).
"""
import json
from dataclasses import dataclass
from functools import lru_cache

from apps.vocab.lang import vi_phonics as ph
from apps.vocab.lang.sources import CACHE_DIR

VOWEL_LETTERS = {"a", "o", "ô", "ơ", "e", "ê", "i", "u", "ư", "y"}


@dataclass(frozen=True)
class Unit:
    kind: str  # am (letter / initial) | thanh (tone) | van (rhyme)
    code: str

    @property
    def is_vowel(self) -> bool:
        return self.kind == "am" and self.code in VOWEL_LETTERS

    @property
    def label(self) -> str:
        if self.kind == "thanh":
            return ph.TONE_LABEL[self.code]
        return ("âm " if self.kind == "am" else "vần ") + self.code

    @property
    def sound(self) -> str:
        """How the unit is read aloud when spelling."""
        if self.kind == "thanh":
            return ph.TONE_SPELL.get(self.code, "ngang")
        if self.is_vowel:
            return ph.VOWEL_SOUND[self.code]
        if self.kind == "am":
            return ph.ONSET_NAME[self.code]
        return " – ".join(ph.spell_rhyme(self.code))

    def matches(self, s: ph.Syllable) -> bool:
        if self.kind == "thanh":
            return s.tone == self.code
        if self.is_vowel or self.kind == "van":
            return s.rhyme == self.code
        return s.onset == self.code

    def payload(self) -> dict:
        return {"kind": self.kind, "code": self.code, "label": self.label, "sound": self.sound,
                "symbol": ph.TONE_SYMBOL.get(self.code, "") if self.kind == "thanh" else ""}


def _am(*codes):
    return [Unit("am", c) for c in codes]


def _van(*codes):
    return [Unit("van", c) for c in codes]


def _thanh(code):
    return [Unit("thanh", code)]


LESSONS: list[dict] = [
    {"title": "Âm a, b · dấu huyền", "units": _am("a", "b") + _thanh("huyen")},
    {"title": "Âm c, o · dấu sắc", "units": _am("c", "o") + _thanh("sac")},
    {"title": "Âm ô, ơ · dấu hỏi", "units": _am("ô", "ơ") + _thanh("hoi")},
    {"title": "Âm d, đ · dấu nặng", "units": _am("d", "đ") + _thanh("nang")},
    {"title": "Âm e, ê · dấu ngã", "units": _am("e", "ê") + _thanh("nga")},
    {"title": "Âm h, i, k", "units": _am("h", "i", "k"), "rule": ("c", "k")},
    {"title": "Âm l, u, ư", "units": _am("l", "u", "ư")},
    {"title": "Âm m, n", "units": _am("m", "n")},
    {"title": "Âm g, gh", "units": _am("g", "gh"), "rule": ("g", "gh")},
    {"title": "Âm ng, ngh", "units": _am("ng", "ngh"), "rule": ("ng", "ngh")},
    {"title": "Âm nh, ph", "units": _am("nh", "ph")},
    {"title": "Âm ch, kh", "units": _am("ch", "kh")},
    {"title": "Âm gi, qu", "units": _am("gi", "qu")},
    {"title": "Âm r, s", "units": _am("r", "s")},
    {"title": "Âm t, th, tr", "units": _am("t", "th", "tr")},
    {"title": "Âm v, x, y", "units": _am("v", "x", "y")},
    {"title": "Vần ia, ua, ưa", "units": _van("ia", "ua", "ưa")},
    {"title": "Vần ai, ay, ây", "units": _van("ai", "ay", "ây")},
    {"title": "Vần oi, ôi, ơi", "units": _van("oi", "ôi", "ơi")},
    {"title": "Vần ui, ưi", "units": _van("ui", "ưi")},
    {"title": "Vần ao, eo", "units": _van("ao", "eo")},
    {"title": "Vần au, âu, êu", "units": _van("au", "âu", "êu")},
    {"title": "Vần iu, ưu", "units": _van("iu", "ưu")},
    {"title": "Vần an, ăn, ân", "units": _van("an", "ăn", "ân")},
    {"title": "Vần on, ôn, ơn", "units": _van("on", "ôn", "ơn")},
    {"title": "Vần en, ên, in, un", "units": _van("en", "ên", "in", "un")},
    {"title": "Vần am, ăm, âm", "units": _van("am", "ăm", "âm")},
    {"title": "Vần om, ôm, ơm", "units": _van("om", "ôm", "ơm")},
    {"title": "Vần em, êm, im, um", "units": _van("em", "êm", "im", "um")},
    {"title": "Vần anh, ênh, inh", "units": _van("anh", "ênh", "inh")},
    {"title": "Vần ang, ăng, âng", "units": _van("ang", "ăng", "âng")},
    {"title": "Vần ong, ông, ung, ưng", "units": _van("ong", "ông", "ung", "ưng")},
    {"title": "Vần ac, ăc, âc", "units": _van("ac", "ăc", "âc")},
    {"title": "Vần oc, ôc, uc, ưc", "units": _van("oc", "ôc", "uc", "ưc")},
    {"title": "Vần at, ăt, ât", "units": _van("at", "ăt", "ât")},
    {"title": "Vần ot, ôt, ơt", "units": _van("ot", "ôt", "ơt")},
    {"title": "Vần et, êt, it, ut, ưt", "units": _van("et", "êt", "it", "ut", "ưt")},
    {"title": "Vần ap, ăp, âp", "units": _van("ap", "ăp", "âp")},
    {"title": "Vần op, ôp, ơp", "units": _van("op", "ôp", "ơp")},
    {"title": "Vần ep, êp, ip, up", "units": _van("ep", "êp", "ip", "up")},
    {"title": "Vần ach, êch, ich", "units": _van("ach", "êch", "ich")},
    {"title": "Vần iê, yê", "units": _van("iên", "iêt", "iêng", "iêc", "iêm", "iêp", "iêu", "yên", "yêu")},
    {"title": "Vần uô", "units": _van("uôn", "uông", "uôt", "uôc", "uôi", "uôm")},
    {"title": "Vần ươ", "units": _van("ươn", "ương", "ươt", "ươc", "ươi", "ươu", "ươm")},
    {"title": "Vần oa, oe", "units": _van("oa", "oe", "oai", "oay", "oan", "oăn", "oat", "oăt", "oang", "oăng", "oanh", "oach")},
    {"title": "Vần uê, uy", "units": _van("uê", "uy", "uơ", "uya", "uân", "uât", "uyên", "uyêt", "uynh", "uych")},
    {"title": "Ôn tập: nghe – viết câu", "units": [], "review": True},
]
for _i, _l in enumerate(LESSONS, start=1):
    _l["n"] = _i


@dataclass
class Taught:
    onsets: set
    vowels: set
    rhymes: set
    tones: set

    def readable(self, s: ph.Syllable) -> bool:
        if s.onset and s.onset not in self.onsets:
            return False
        if s.tone != "ngang" and s.tone not in self.tones:
            return False
        return s.rhyme in self.rhymes or (len(s.rhyme) == 1 and s.rhyme in self.vowels)


@lru_cache(maxsize=None)
def taught_until(n: int) -> Taught:
    t = Taught(set(), set(), set(), set())
    for lesson in LESSONS[:n]:
        for u in lesson["units"]:
            if u.kind == "thanh":
                t.tones.add(u.code)
            elif u.kind == "van":
                t.rhymes.add(u.code)
            elif u.is_vowel:
                t.vowels.add(u.code)
            else:
                t.onsets.add(u.code)
    return t


def lesson(n: int) -> dict | None:
    return LESSONS[n - 1] if 1 <= n <= len(LESSONS) else None


@lru_cache(maxsize=1)
def corpus() -> dict:
    data = json.loads((CACHE_DIR / "vi_corpus.json").read_text(encoding="utf-8"))
    parsed = {}
    for syl, count in data["syllables"].items():
        s = ph.parse(syl)
        if s is not None:
            parsed[syl] = (s, count)
    data["parsed"] = parsed
    data["rare_parsed"] = [s for s in (ph.parse(x) for x in data.get("rare", [])) if s is not None]
    return data


@lru_cache(maxsize=None)
def readable_syllables(n: int) -> list[tuple[ph.Syllable, int]]:
    """Real syllables readable at lesson n, most frequent first (dictionary-only rare ones last, count 0)."""
    t = taught_until(n)
    common = sorted(((s, c) for s, c in corpus()["parsed"].values() if t.readable(s)), key=lambda x: -x[1])
    return common + [(s, 0) for s in corpus()["rare_parsed"] if t.readable(s)]


def readable_text(text: str, n: int) -> bool:
    t = taught_until(n)
    for syl in ph.syllables_of(text):
        s = ph.parse(syl)
        if s is None or not t.readable(s):
            return False
    return True
