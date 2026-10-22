"""Import example sentences for the vocabulary from Tatoeba (CC BY 2.0 FR).

Only sentences written by members who declared themselves native speakers (level 5) of the language,
with a human translation linked directly on Tatoeba (vi for English, vi or en for Chinese, en for Vietnamese).
Chinese sentences keep their original script: Tatoeba's transcriptions tell whether a sentence was written in
simplified or traditional characters, so zh-Hans and zh-Hant never come from automatic conversion.
"""
import bz2
import csv
import io
import tarfile
import urllib.request
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.vocab.lang import sentences as sl
from apps.vocab.lang.sources import SOURCES_DIR, USER_AGENT
from apps.vocab.models import ExampleSentence, ReviewStatus, WordTranslation

BASE = "https://downloads.tatoeba.org/exports/"
FILES = {
    "cmn_sentences_detailed.tsv.bz2": "per_language/cmn/cmn_sentences_detailed.tsv.bz2",
    "eng_sentences_detailed.tsv.bz2": "per_language/eng/eng_sentences_detailed.tsv.bz2",
    "vie_sentences_detailed.tsv.bz2": "per_language/vie/vie_sentences_detailed.tsv.bz2",
    "cmn-eng_links.tsv.bz2": "per_language/cmn/cmn-eng_links.tsv.bz2",
    "cmn-vie_links.tsv.bz2": "per_language/cmn/cmn-vie_links.tsv.bz2",
    "eng-vie_links.tsv.bz2": "per_language/eng/eng-vie_links.tsv.bz2",
    "cmn_transcriptions.tsv.bz2": "per_language/cmn/cmn_transcriptions.tsv.bz2",
    "user_languages.tar.bz2": "user_languages.tar.bz2",
}
DIR = SOURCES_DIR / "tatoeba"
LICENSE = "CC BY 2.0 FR"
MAX_LEN = {"en": 10, "vi": 12, "zh": 16}  # words / syllables / Han characters


def _rows(name):
    with bz2.open(DIR / name, "rt", encoding="utf-8") as fh:
        for line in fh:
            yield line.rstrip("\n").split("\t")


class Command(BaseCommand):
    help = "Nhập câu ví dụ từ Tatoeba (người bản xứ, có bản dịch người dịch) cho các từ vựng đã kiểm tra"

    def add_arguments(self, parser):
        parser.add_argument("--per-word", type=int, default=6, help="Số câu tối đa mỗi từ mỗi ngôn ngữ")

    def handle(self, *args, per_word=6, **opts):
        self.download()
        natives = self.natives()
        self.stdout.write("Đọc câu…")
        cmn = self.sentences("cmn", natives["cmn"], 40)
        vie = self.sentences("vie", natives["vie"], 80)
        links = {
            "cmn-eng": self.links("cmn-eng_links.tsv.bz2"),
            "cmn-vie": self.links("cmn-vie_links.tsv.bz2"),
            "eng-vie": self.links("eng-vie_links.tsv.bz2"),
        }
        vie_eng = defaultdict(list)
        for e, vs in links["eng-vie"].items():
            for v in vs:
                vie_eng[v].append(e)
        # translations need not be written by natives of the translation language, but must exist on Tatoeba
        eng_any = self.sentences("eng", None, 200, keep={e for es in links["cmn-eng"].values() for e in es}
                                 | {e for es in vie_eng.values() for e in es} | set(links["eng-vie"]))
        eng = {k: v for k, v in eng_any.items() if k in links["eng-vie"] and v[1] in natives["eng"] and len(v[0]) <= 80}
        vie_any = self.sentences("vie", None, 200)
        script, latn = self.transcriptions()

        words = defaultdict(list)  # (lang code, text) -> [word ids]
        for tr in WordTranslation.objects.filter(status=ReviewStatus.VERIFIED).values("word_id", "language_id", "text"):
            words[tr["language_id"]].append((tr["word_id"], tr["text"]))

        candidates = defaultdict(list)  # (word_id, lang) -> [ExampleSentence]
        stats = defaultdict(int)

        def first(ids, pool):
            return next((pool[i][0] for i in ids if i in pool), "")

        # ---- Chinese
        for sid, (text, _owner) in cmn.items():
            sc = script.get(sid)
            if sc is None or sl.han_count(text) > MAX_LEN["zh"] or any(c.isdigit() for c in text):
                continue
            vi = first(links["cmn-vie"].get(sid, []), vie_any)
            en_ids = [e for e in links["cmn-eng"].get(sid, []) if e in eng_any]
            en = eng_any[en_ids[0]][0] if en_ids else ""
            # Learners are Vietnamese: when nobody translated the sentence into Vietnamese directly, use the
            # (human) Vietnamese translation of its English translation on Tatoeba – recorded, never machine-made.
            via = []
            if not vi:
                for e in en_ids:
                    vi = first(links["eng-vie"].get(e, []), vie_any)
                    if vi:
                        via = [f"Bản dịch tiếng Việt lấy qua câu tiếng Anh #{e} trên Tatoeba"]
                        break
            if not (vi or en):
                continue
            lang = "zh-Hans" if sc == "hans" else "zh-Hant"
            pin, reviewer = latn.get(sid, ("", ""))
            zh = None
            for word_id, wtext in words[lang]:
                if wtext not in text:
                    continue
                zh = zh or sl.build_zh(text, sc, pin, bool(reviewer))
                span = sl.word_spans(zh.tokens, wtext, lang)
                if not span:
                    continue
                candidates[(word_id, lang)].append(self.example(
                    word_id, lang, sid, text, zh.tokens, span, vi, en, zh.errors,
                    zh.warnings + via + ([f"Pinyin đã được {reviewer} duyệt trên Tatoeba"] if reviewer else []),
                    sl.py.numbered_to_marked(zh.numbered), reviewed=bool(reviewer),
                ))

        # ---- English (needs a Vietnamese translation) and Vietnamese (needs an English one)
        for lang, pool, trans in (("en", eng, links["eng-vie"]), ("vi", vie, vie_eng)):
            for sid, (text, _owner) in pool.items():
                tr_ids = trans.get(sid, [])
                other = first(tr_ids, vie_any if lang == "en" else eng_any)
                if not other or any(c.isdigit() for c in text):
                    continue
                toks = sl.tokens_latin(text, lang)
                if sum(1 for t in toks if not t.get("x")) > MAX_LEN[lang]:
                    continue
                low = text.lower()
                for word_id, wtext in words[lang]:
                    if wtext.lower() not in low:
                        continue
                    span = sl.word_spans(toks, wtext, lang)
                    if span:
                        vi, en = (other, "") if lang == "en" else ("", other)
                        candidates[(word_id, lang)].append(self.example(word_id, lang, sid, text, toks, span, vi, en))

        rows = []
        for (word_id, lang), items in candidates.items():
            # verified first, then sentences with a Vietnamese translation, reviewed pinyin, short ones
            items.sort(key=lambda e: (e.status != ReviewStatus.VERIFIED, not e.translation_vi,
                                      not e.checks.get("reviewed"), len(e.text)))
            rows.extend(items[:per_word])
            for e in items[:per_word]:
                stats[f"{lang} {e.status}"] += 1
        with transaction.atomic():
            ExampleSentence.objects.filter(source="tatoeba").delete()
            ExampleSentence.objects.bulk_create(rows, batch_size=500)
        for k in sorted(stats):
            self.stdout.write(f"  {k:20} {stats[k]}")
        covered = defaultdict(set)
        for e in rows:
            if e.status == ReviewStatus.VERIFIED:
                covered[e.language_id].add(e.word_id)
        for lang in ("en", "vi", "zh-Hans", "zh-Hant"):
            self.stdout.write(f"  {lang:8} có câu verified: {len(covered[lang])}/{len(words[lang])} từ")
        self.stdout.write(self.style.SUCCESS(f"Đã nhập {len(rows)} câu ví dụ từ Tatoeba"))

    @staticmethod
    def example(word_id, lang, sid, text, tokens, span, vi, en, errors=(), warnings=(), translit="", reviewed=False):
        return ExampleSentence(
            word_id=word_id, language_id=lang, text=text, transliteration=translit, translation_vi=vi,
            translation_en=en, source="tatoeba", source_id=str(sid), license=LICENSE, tokens=tokens,
            target_tokens=span, checks={"errors": list(errors), "warnings": list(warnings), "reviewed": reviewed},
            status=ReviewStatus.FLAGGED if errors else ReviewStatus.VERIFIED,
        )

    # ------------------------------------------------------------------ loading

    def download(self):
        DIR.mkdir(parents=True, exist_ok=True)
        for name, path in FILES.items():
            if (DIR / name).exists():
                continue
            self.stdout.write(f"↓ {name}")
            req = urllib.request.Request(BASE + path, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=300) as res:
                (DIR / name).write_bytes(res.read())

    def natives(self):
        out = defaultdict(set)
        with tarfile.open(DIR / "user_languages.tar.bz2", "r:bz2") as tar:
            member = tar.extractfile(tar.getmember("user_languages.csv"))
            for row in csv.reader(io.TextIOWrapper(member, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
                if len(row) >= 3 and row[1] == "5":
                    out[row[0]].add(row[2])
        return out

    def sentences(self, lang, natives, max_chars, keep=None):
        out = {}
        for row in _rows(f"{lang}_sentences_detailed.tsv.bz2"):
            if len(row) < 4:
                continue
            sid, text, owner = int(row[0]), row[2], row[3]
            if keep is not None and sid not in keep:
                continue
            if natives is not None and owner not in natives:
                continue
            if len(text) <= max_chars:
                out[sid] = (text, owner)
        return out

    def links(self, name):
        out = defaultdict(list)
        for row in _rows(name):
            if len(row) == 2:
                out[int(row[0])].append(int(row[1]))
        return out

    def transcriptions(self):
        """Original script of each Chinese sentence (from the alternative-script row) and its pinyin."""
        script, latn = {}, {}
        for row in _rows("cmn_transcriptions.tsv.bz2"):
            if len(row) < 5:
                continue
            sid, kind, reviewer, text = int(row[0]), row[2], row[3], row[4]
            if kind == "Hans":
                script[sid] = "hant"
            elif kind == "Hant":
                script[sid] = "hans"
            elif kind == "Latn":
                latn[sid] = (text, reviewer)
        return script, latn
