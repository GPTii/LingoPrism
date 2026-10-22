"""Loaders for the authoritative language sources (see PLAN.md §3b).

Raw downloads live in BE/seed/sources/ (gitignored, fetched by `manage.py fetch_sources`).
Per-word Taiwan MOE dictionary lookups are cached in BE/seed/cache/moedict.json (committed)
so seeding is reproducible offline.
"""
import gzip
import json
import re
import threading
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from django.conf import settings

SEED_DIR = Path(settings.BASE_DIR) / "seed"
SOURCES_DIR = SEED_DIR / "sources"
CACHE_DIR = SEED_DIR / "cache"

DOWNLOADS = {
    "cedict_ts.u8.gz": "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz",
    "cmudict.dict": "https://raw.githubusercontent.com/cmusphinx/cmudict/master/cmudict.dict",
    "hsk_complete.json": "https://raw.githubusercontent.com/drkameleon/complete-hsk-vocabulary/main/complete.json",
}

USER_AGENT = "LingoPrism/1.0 (graduation project; vocabulary verification)"


# ------------------------------------------------------------------ CC-CEDICT

@dataclass
class CedictEntry:
    traditional: str
    simplified: str
    pinyin: str  # numbered, normalized
    glosses: list[str]
    classifiers: list[tuple[str, str, str]] = field(default_factory=list)  # (trad, simp, pinyin)

    @property
    def taiwan_pinyin(self) -> str | None:
        for g in self.glosses:
            m = re.search(r"Taiwan pr\. \[([^\]]+)\]", g)
            if m:
                return m.group(1)
        return None


_LINE_RE = re.compile(r"^(\S+) (\S+) \[([^\]]+)\] /(.*)/\s*$")
_CL_RE = re.compile(r"([^\s,|\[\]]+)(?:\|([^\s,|\[\]]+))?\[([^\]]+)\]")


class Cedict:
    def __init__(self, path: Path):
        from .pinyin import normalize_numbered

        self.by_trad: dict[str, list[CedictEntry]] = {}
        self.by_simp: dict[str, list[CedictEntry]] = {}
        trad_chars: set[str] = set()
        simp_chars: set[str] = set()
        s_to_t: set[tuple[str, str]] = set()
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("#"):
                    continue
                m = _LINE_RE.match(line)
                if not m:
                    continue
                trad, simp, pin, rest = m.groups()
                glosses = [g for g in rest.split("/") if g]
                classifiers = []
                for g in glosses:
                    for cl in re.findall(r"CL:([^/)]+)", g):
                        for cm in _CL_RE.finditer(cl):
                            t, s, p = cm.group(1), cm.group(2) or cm.group(1), cm.group(3)
                            classifiers.append((t, s, normalize_numbered(p)))
                entry = CedictEntry(trad, simp, normalize_numbered(pin), glosses, classifiers)
                self.by_trad.setdefault(trad, []).append(entry)
                self.by_simp.setdefault(simp, []).append(entry)
                trad_chars.update(trad)
                simp_chars.update(simp)
                if len(trad) == len(simp):
                    s_to_t.update((s, t) for s, t in zip(simp, trad) if s != t)
        # characters that only ever appear on one side
        self.simplified_only = {s for s, _ in s_to_t} - trad_chars
        self.traditional_only = {t for _, t in s_to_t} - simp_chars


# ------------------------------------------------------------------ HSK

class Hsk:
    def __init__(self, path: Path):
        data = json.loads(path.read_text(encoding="utf-8"))
        self.by_simp: dict[str, dict] = {}
        for e in data:
            self.by_simp.setdefault(e["simplified"], e)

    def level(self, simplified: str) -> str | None:
        e = self.by_simp.get(simplified)
        if not e:
            return None
        levels = e.get("level", [])
        new = sorted(lv for lv in levels if lv.startswith("new-"))
        if new:
            return "HSK " + new[0].split("-")[1]
        old = sorted(lv for lv in levels if lv.startswith("old-"))
        return ("HSK " + old[0].split("-")[1] + " (cũ)") if old else None

    def readings(self, simplified: str) -> list[dict]:
        e = self.by_simp.get(simplified)
        return e.get("forms", []) if e else []


# ------------------------------------------------------------------ CMUdict

class CmuDict:
    def __init__(self, path: Path):
        self.words: dict[str, list[list[str]]] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.split("#")[0].strip()
            if not line:
                continue
            head, *phones = line.split()
            word = re.sub(r"\(\d+\)$", "", head)
            self.words.setdefault(word, []).append(phones)

    def lookup(self, word: str) -> list[list[str]] | None:
        """Multi-word expressions ("traffic light") are looked up word by word."""
        parts = word.lower().split()
        found = [self.words.get(p) for p in parts]
        if not all(found):
            return None
        if len(parts) == 1:
            return found[0]
        # one pronunciation per word, words separated by a "|" marker
        joined = []
        for f in found:
            if joined:
                joined.append("|")
            joined.extend(f[0])
        return [joined]


# ------------------------------------------------------------------ Taiwan MOE dictionary (moedict)

class MoeDict:
    """Lookups against https://www.moedict.tw (教育部重編國語辭典修訂本, CC BY-ND 3.0 TW), cached on disk."""

    URL = "https://www.moedict.tw/uni/{}"

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self.cache: dict[str, dict | None] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        self._dirty = False

    def lookup(self, word: str, allow_network: bool = True) -> dict | None:
        if word in self.cache:
            return self.cache[word]
        if not allow_network:
            return None
        url = self.URL.format(urllib.parse.quote(word))
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=20) as res:
                raw = json.loads(res.read().decode("utf-8"))
            data = {
                "title": raw.get("title"),
                "heteronyms": [
                    {"pinyin": h.get("pinyin", ""), "bopomofo": h.get("bopomofo", "")}
                    for h in raw.get("heteronyms", [])
                ],
            }
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
            data = None
        time.sleep(0.3)  # be polite to the public API
        with self._lock:
            self.cache[word] = data
            self._dirty = True
        return data

    def save(self):
        if self._dirty:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
            self._dirty = False


# ------------------------------------------------------------------ accessors

def _require(name: str) -> Path:
    path = SOURCES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Thiếu {path}. Chạy: python manage.py fetch_sources")
    return path


@lru_cache(maxsize=1)
def cedict() -> Cedict:
    return Cedict(_require("cedict_ts.u8.gz"))


@lru_cache(maxsize=1)
def hsk() -> Hsk:
    return Hsk(_require("hsk_complete.json"))


@lru_cache(maxsize=1)
def cmudict() -> CmuDict:
    return CmuDict(_require("cmudict.dict"))


@lru_cache(maxsize=1)
def moedict() -> MoeDict:
    return MoeDict(CACHE_DIR / "moedict.json")


def sources_available() -> bool:
    return all((SOURCES_DIR / name).exists() for name in DOWNLOADS)


@lru_cache(maxsize=1)
def neutral_tone_words() -> dict[str, tuple[int, ...]]:
    """Words whose CC-CEDICT reading has a neutral tone (妈妈 ma1 ma5, 谢谢 xie4 xie5), keyed by simplified and
    traditional form → tones. Only words where every entry agrees (东西 "thing" vs "east and west" is left out),
    and, for traditional forms, not ones marked with a different Taiwan reading. Small – read once from the
    file, without loading the whole dictionary. Empty when the file is missing."""
    from .pinyin import normalize_numbered

    path = SOURCES_DIR / "cedict_ts.u8.gz"
    if not path.exists():
        return {}
    seen: dict[str, set[tuple[int, ...]]] = {}
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            m = _LINE_RE.match(line)
            if not m:
                continue
            trad, simp, pin, rest = m.groups()
            syl = normalize_numbered(pin).split()
            if len(syl) != len(simp) or len(simp) < 2 or len(simp) > 4 or not all(s[-1:].isdigit() for s in syl):
                continue
            tones = tuple(int(s[-1]) for s in syl)
            seen.setdefault("s:" + simp, set()).add(tones)
            seen.setdefault("t:" + trad, set()).add((0,) if "Taiwan pr." in rest else tones)
    out: dict[str, tuple[int, ...]] = {}
    for key, variants in seen.items():
        if len(variants) == 1:
            (tones,) = variants
            if 5 in tones:
                out[key] = tones
    return out
