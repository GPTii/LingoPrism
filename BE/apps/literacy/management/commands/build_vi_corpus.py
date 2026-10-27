"""Build seed/cache/vi_corpus.json: real Vietnamese syllables and short sentences for early-literacy exercises.

Sources, cross-checked so children never see a typo or a made-up syllable:
  * Tatoeba sentences written by native Vietnamese speakers (CC BY 2.0 FR)
  * Viet74K word list from Hồ Ngọc Đức's Free Vietnamese Dictionary (verification only, not redistributed)
A syllable is kept when it is well-formed (initial + rhyme, spelling rules, one tone mark, standard tone
placement), is written in lower case in the sentences (not a name like "Tom"), occurs at least --min-count
times AND appears in the dictionary. Sentences with a capitalised word after the first one (names) are skipped.
"""
import json
import re
import unicodedata
import urllib.request
from collections import Counter

from django.core.management.base import BaseCommand

from apps.vocab.lang import vi_phonics as ph
from apps.vocab.lang import vietnamese
from apps.vocab.lang.sources import CACHE_DIR, SOURCES_DIR, USER_AGENT

CORPUS = CACHE_DIR / "vi_corpus.json"
WORDLIST = SOURCES_DIR / "viet74k.txt"
WORDLIST_URL = "https://raw.githubusercontent.com/duyet/vietnamese-wordlist/master/Viet74K.txt"
WORD_RE = re.compile(r"[^\W\d_]+")
# this is a children's course: no vulgar or violent syllables, in drills or in dictation sentences
KID_BLOCKLIST = {
    "đéo", "đếch", "địt", "đụ", "lồn", "cặc", "buồi", "đĩ", "dái", "chửi", "giết", "chém", "đâm", "súng", "máu",
    "tởm", "rượu", "bia", "thuốc", "ma", "quỷ", "chết", "say", "nghiện", "khốn", "ngu", "đần", "cút",
}


class Command(BaseCommand):
    help = "Tạo kho tiếng & câu ngắn tiếng Việt (người bản xứ, Tatoeba) cho phần học đọc – viết"

    def add_arguments(self, parser):
        parser.add_argument("--min-count", type=int, default=3)
        parser.add_argument("--max-sentence", type=int, default=8, help="Số tiếng tối đa của câu nghe – viết")

    def handle(self, *args, min_count=3, max_sentence=8, **opts):
        from apps.vocab.management.commands.import_tatoeba import Command as Tatoeba

        tat = Tatoeba()
        tat.stdout = self.stdout
        tat.download()
        natives = tat.natives()["vie"]
        sentences = tat.sentences("vie", natives, 120)

        dictionary = self.dictionary()
        counts = Counter()
        capitalised = Counter()
        lower_mid = Counter()
        bad = Counter()
        for text, _owner in sentences.values():
            for i, raw in enumerate(WORD_RE.findall(unicodedata.normalize("NFC", text))):
                if i > 0 and raw[0].isupper():
                    capitalised[raw.lower()] += 1  # names (Tom, Hà Nội…) are not counted as common syllables
                    continue
                syl = raw.lower()
                if i > 0:
                    lower_mid[syl] += 1
                if self.valid(syl) and syl in dictionary:
                    counts[syl] += 1
                else:
                    bad[syl] += 1
        # a lower-case "tom" that is mostly written "Tom" is a name typed in lower case, not a Vietnamese word
        syllables = {s: n for s, n in counts.most_common()
                     if n >= min_count and s not in KID_BLOCKLIST and capitalised[s] <= 3 * lower_mid[s]}
        # rare rhymes (oăn, uơ, uych…) hardly occur in short sentences: well-formed dictionary syllables fill the gap
        rare = sorted(s for s in dictionary if s not in syllables and s not in KID_BLOCKLIST and self.valid(s))

        short = []
        for sid, (text, _owner) in sorted(sentences.items()):
            sy = ph.syllables_of(text)
            if not 2 <= len(sy) <= max_sentence or re.search(r"[0-9\"“”()\-]", text):
                continue
            if any(w[0].isupper() for w in WORD_RE.findall(text)[1:]):
                continue
            if vietnamese.problems(text) or not all(s in syllables for s in sy):
                continue
            short.append({"id": sid, "text": vietnamese.normalize(text), "syllables": len(sy)})

        CORPUS.write_text(json.dumps({
            "source": "Tatoeba (người bản xứ tiếng Việt, CC BY 2.0 FR) – đối chiếu từ điển Hồ Ngọc Đức (Viet74K)",
            "syllables": syllables,
            "rare": rare,
            "sentences": short,
        }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        self.stdout.write(f"Tiếng hợp lệ: {len(syllables)} (≥{min_count} lần) · tiếng hiếm từ từ điển: {len(rare)}"
                          f" · bỏ {len(bad)} dạng không chuẩn")
        self.stdout.write(self.style.SUCCESS(f"Câu ngắn nghe – viết: {len(short)} → {CORPUS}"))

    def dictionary(self) -> set[str]:
        if not WORDLIST.exists():
            self.stdout.write(f"↓ {WORDLIST.name}")
            req = urllib.request.Request(WORDLIST_URL, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as res:  # fixed https source, not user input  # nosec B310
                WORDLIST.write_bytes(res.read())
        # a syllable counts when it is an entry on its own or occurs in at least two entries
        # (a single compound like "kính đên" is not enough evidence)
        standalone, seen = set(), Counter()
        for line in WORDLIST.read_text(encoding="utf-8").splitlines():
            if not line or line[0].isupper():
                continue
            parts = WORD_RE.findall(unicodedata.normalize("NFC", line.lower()))
            if len(parts) == 1:
                standalone.add(parts[0])
            seen.update(set(parts))
        return standalone | {s for s, n in seen.items() if n >= 2}

    @staticmethod
    def valid(syl: str) -> bool:
        s = ph.parse(syl)
        if s is None or ph.spelling_error(s.onset, s.rhyme) or s.text != syl:
            return False
        return not vietnamese.problems(syl)
