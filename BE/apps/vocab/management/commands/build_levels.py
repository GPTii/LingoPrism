"""Split the vocabulary of each language into 4 levels, from data rather than by hand.

    python manage.py build_levels      # needs the Tatoeba files downloaded by import_tatoeba

* Chinese – the HSK 3.0 band of the simplified word: HSK 1 → level 1, HSK 2 → 2, HSK 3 → 3. HSK is an adult syllabus
  and leaves out many easy concrete words (大象, 熊), so words in HSK 4+ or outside HSK are placed by corpus
  frequency, never below level 2.
* English / Vietnamese – how often the word occurs in Tatoeba sentences: the most frequent quarter of our words is
  level 1, the rarest quarter level 4. Vietnamese also counts the noun without its classifier ("con lợn" ← "lợn"),
  and a word that never occurs takes the level of the same concept in English (the Vietnamese corpus is small).

Result: ``seed/concepts/levels.csv`` (committed, with the evidence: frequency per million sentences and HSK band).
A row can be overridden by hand in the ``override_*`` columns with a ``note``; ``build_vocab`` loads the levels.
"""
import csv
import re
from collections import Counter

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.vocab.lang import sources, vietnamese
from apps.vocab.management.commands import import_tatoeba as tat

LEVELS = 4
FIELDS = ["slug", "en", "zh", "vi", "en_per_m", "zh_per_m", "zh_hsk", "vi_per_m", "override_en", "override_zh",
          "override_vi", "note"]
CLASSIFIERS = {"con", "cái", "quả", "chiếc", "quyển", "cuốn", "cây", "bông", "tờ", "đôi", "bộ", "hòn", "ngôi", "màu"}
_LATIN = re.compile(r"[a-zà-ỹđ']+", re.I)


def ngrams(tokens, n_max):
    for n in range(1, n_max + 1):
        for i in range(len(tokens) - n + 1):
            yield " ".join(tokens[i:i + n])


def quartile_levels(freq: dict[str, float]) -> dict[str, int]:
    """Most frequent quarter → 1 … rarest quarter → 4 (ties keep the same level)."""
    ranked = sorted(freq, key=lambda k: -freq[k])
    out, n = {}, len(ranked)
    for i, key in enumerate(ranked):
        out[key] = min(LEVELS, 1 + i * LEVELS // max(n, 1))
    return out


def hsk_level(band: str) -> int | None:
    m = re.match(r"HSK (\d)", band or "")
    return None if not m else min(int(m.group(1)), LEVELS)


class Command(BaseCommand):
    help = "Chia từ vựng mỗi ngôn ngữ thành 4 cấp độ (HSK + tần suất trong câu người bản xứ trên Tatoeba)"

    def handle(self, *args, **opts):
        concepts = settings.BASE_DIR / "seed" / "concepts"
        with open(concepts / "words.csv", encoding="utf-8") as fh:
            words = list(csv.DictReader(fh))
        if (concepts / "words_approved.csv").exists():
            with open(concepts / "words_approved.csv", encoding="utf-8") as fh:
                words += list(csv.DictReader(fh))
        path = concepts / "levels.csv"
        overrides = {}
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                overrides = {r["slug"]: r for r in csv.DictReader(fh)}

        loader = tat.Command()
        natives = loader.natives()
        self.stdout.write("Đếm tần suất…")
        en_f = self._latin_freq(loader, "eng", natives["eng"], {w["en"].lower() for w in words}, 3, lambda s: s.lower())
        vi_forms = {w["slug"]: self._vi_forms(w["vi"]) for w in words}
        vi_f = self._latin_freq(loader, "vie", None, {f for fs in vi_forms.values() for f in fs}, 6,
                                lambda s: vietnamese.normalize(s).lower())
        zh_f = self._zh_freq(loader, natives["cmn"], {w["zh_hans"] for w in words} | {w["zh_hant"] for w in words})

        hsk = sources.hsk()
        en_per = {w["slug"]: en_f.get(w["en"].lower(), 0) for w in words}
        vi_per = {s: max(vi_f.get(f, 0) for f in fs) for s, fs in vi_forms.items()}
        zh_per = {w["slug"]: zh_f.get(w["zh_hans"], 0) + zh_f.get(w["zh_hant"], 0) if w["zh_hans"] != w["zh_hant"]
                  else zh_f.get(w["zh_hans"], 0) for w in words}
        en_lv, zh_freq_lv = quartile_levels(en_per), quartile_levels(zh_per)
        seen_vi = quartile_levels({s: f for s, f in vi_per.items() if f > 0})
        vi_lv = {s: seen_vi.get(s, en_lv[s]) for s in vi_per}

        rows = []
        for w in words:
            s = w["slug"]
            band = hsk.level(w["zh_hans"]) or ""
            old = overrides.get(s, {})
            rows.append({
                "slug": s, "en": en_lv[s], "vi": vi_lv[s],
                "zh": lv if (lv := hsk_level(band)) and lv <= 3 else max(2, zh_freq_lv[s]),
                "en_per_m": f"{en_per[s]:.1f}", "zh_per_m": f"{zh_per[s]:.1f}", "zh_hsk": band,
                "vi_per_m": f"{vi_per[s]:.1f}",
                **{k: old.get(k, "") for k in ("override_en", "override_zh", "override_vi", "note")},
            })
        with open(path, "w", encoding="utf-8", newline="") as fh:
            out = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
            out.writeheader()
            out.writerows(rows)
        for lang in ("en", "zh", "vi"):
            c = Counter(int(r[f"override_{lang}"] or r[lang]) for r in rows)
            self.stdout.write(f"  {lang}: " + "  ".join(f"cấp {k}={c[k]}" for k in range(1, LEVELS + 1)))
        self.stdout.write(self.style.SUCCESS(f"Đã ghi {path.name}"))

    @staticmethod
    def _vi_forms(text):
        """The word, and the word without its classifier ("con lợn" → "lợn")."""
        full = vietnamese.normalize(text).lower()
        head, _, rest = full.partition(" ")
        return {full, rest} if head in CLASSIFIERS and rest else {full}

    def _latin_freq(self, loader, lang, natives, wanted, n_max, norm):
        """Occurrences per million native sentences of each wanted word/phrase (plural -s/-es counted for English)."""
        counts, total = Counter(), 0
        for row in tat._rows(f"{lang}_sentences_detailed.tsv.bz2"):
            if len(row) < 4 or (natives is not None and row[3] not in natives):
                continue
            total += 1
            toks = _LATIN.findall(norm(row[2]))
            seen = set(ngrams(toks, n_max))
            for g in seen:
                if g in wanted:
                    counts[g] += 1
                elif lang == "eng" and (g.endswith("s") and (g[:-1] in wanted or g.endswith("es") and g[:-2] in wanted)):
                    counts[g[:-2] if g.endswith("es") and g[:-2] in wanted else g[:-1]] += 1
        return {k: v * 1e6 / max(total, 1) for k, v in counts.items()}

    def _zh_freq(self, loader, natives, wanted):
        counts, total = Counter(), 0
        for row in tat._rows("cmn_sentences_detailed.tsv.bz2"):
            if len(row) < 4 or row[3] not in natives:
                continue
            total += 1
            text = row[2]
            for w in wanted:
                if w in text:
                    counts[w] += 1
        return {k: v * 1e6 / max(total, 1) for k, v in counts.items()}
