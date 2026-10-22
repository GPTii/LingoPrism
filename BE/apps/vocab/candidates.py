"""Queue of new words proposed from the HSK syllabus, reviewed by teachers before learners see them.

Suggestion (``suggest_words`` command): for every HSK word not yet in the vocabulary, the English meaning comes from
CC-CEDICT and Vietnamese options from Vietnamese Wiktionary entries whose gloss is that English word (only words that
also exist in the Vietnamese dictionary). ``confidence = high`` when the three primary senses agree – still reviewed:
automatic sense matching is wrong surprisingly often (打 → "dozen", 把手 → "shake hands").

Approval runs exactly the checks of ``build_vocab`` (CC-CEDICT, HSK, MOE dictionary, CMUdict, Vietnamese spelling);
the approved row is appended to ``seed/concepts/words_approved.csv`` so a fresh ``seed_all`` rebuilds it.
"""
import csv
import gzip
import json
import re
import unicodedata
from collections import defaultdict

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsStaffRole

from .lang import checks, sources
from .lang import pinyin as py
from .models import Topic, Word, WordCandidate

APPROVED_CSV = settings.BASE_DIR / "seed" / "concepts" / "words_approved.csv"
WIKTIONARY = sources.SEED_DIR / "sources" / "wiktionary" / "vi.jsonl.gz"
CSV_FIELDS = ["slug", "topics", "yolo_label", "pos", "audience", "difficulty", "vi", "en", "en_aliases", "zh_hans", "zh_hant"]
_SKIP = ("surname", "variant", "old variant", "used in", "abbr.", "(literary)", "(old)", "(dialect)")


def clean_gloss(g: str) -> str | None:
    g = re.sub(r"\([^)]*\)|\[[^]]*\]", "", g).strip().lower()
    g = re.sub(r"^(to |a |an |the )", "", g).strip(" .!?")
    return g if re.fullmatch(r"[a-z][a-z' -]{0,30}", g) and len(g.split()) <= 3 else None


def _vietnamese_index():
    """English gloss → Vietnamese words (primary sense first), restricted to words of the Vietnamese dictionary."""
    v74 = {s for line in (sources.SEED_DIR / "sources" / "viet74k.txt").read_text(encoding="utf-8").splitlines()
           for s in line.strip().lower().split()}
    primary, other = defaultdict(list), defaultdict(list)
    with gzip.open(WIKTIONARY, "rt", encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            w = unicodedata.normalize("NFC", d.get("word", "")).strip()
            if not w or w[0].isupper() or not re.fullmatch(r"[^\W\d_]+( [^\W\d_]+)*", w):
                continue
            if not all(s.lower() in v74 for s in w.split()):
                continue
            for i, sense in enumerate(d.get("senses", [])):
                for part in re.split(r"[;,]", (sense.get("glosses") or [""])[0]):
                    e = clean_gloss(part)
                    if e:
                        (primary if i == 0 else other)[e].append(w.lower())
    return primary, other


def suggest(levels=(1, 2, 3)) -> int:
    hsk = json.loads((sources.SEED_DIR / "sources" / "hsk_complete.json").read_text(encoding="utf-8"))
    ced, cmu = sources.cedict(), sources.cmudict()
    existing = set(Word.objects.filter(translations__language_id="zh-Hans").values_list("translations__text", flat=True))
    existing |= set(WordCandidate.objects.values_list("zh_hans", flat=True))
    primary, other = _vietnamese_index()
    made = 0
    for e in hsk:
        simp = e["simplified"]
        lv = next((int(x.split("-")[1]) for x in sorted(e.get("level", [])) if x.startswith("new-") and x[4:].isdigit()), None)
        if lv not in levels or simp in existing:
            continue
        entries = [x for x in ced.by_simp.get(simp, []) if not x.glosses[0].lower().startswith(_SKIP)]
        if not entries:
            continue
        entry = entries[0]
        glosses = [g for g in (clean_gloss(g) for g in entry.glosses[:4]) if g and cmu.lookup(g)]
        if not glosses:
            continue
        en = glosses[0]
        options = list(dict.fromkeys(primary.get(en, []) + [w for g in glosses for w in primary.get(g, []) + other.get(g, [])]))
        WordCandidate.objects.create(
            zh_hans=simp, zh_hant=entry.traditional, pinyin=py.numbered_to_marked(entry.pinyin),
            hsk_level=lv, glosses=entry.glosses[:8], en=en, vi=options[0] if options else "", vi_options=options[:8],
            part_of_speech="verb" if entry.glosses[0].startswith("to ") else "noun",
            confidence="high" if primary.get(en) and len(primary[en]) <= 2 else "low",
        )
        existing.add(simp)
        made += 1
    return made


def check(c: WordCandidate) -> dict:
    """The same source checks as build_vocab, without saving anything."""
    terms = [c.en] + [g for g in (clean_gloss(x) for x in c.glosses) if g]
    is_noun = c.part_of_speech == "noun"
    results = {
        "vi": checks.build_vi(c.vi) if c.vi else {"errors": ["vi: chưa có nghĩa tiếng Việt"], "warnings": []},
        "en": checks.build_en(c.en) if c.en else {"errors": ["en: chưa có từ tiếng Anh"], "warnings": []},
        "zh-Hans": checks.build_zh_hans(c.zh_hans, terms, is_noun, prefer_trad=c.zh_hant),
        "zh-Hant": checks.build_zh_hant(c.zh_hant, terms, is_noun),
    }
    sources.moedict().save()
    out = {lang: {"errors": r["errors"], "warnings": r["warnings"]} for lang, r in results.items()}
    if not c.topics:
        out["topics"] = {"errors": ["Chọn ít nhất một chủ đề"], "warnings": []}
    elif unknown := [t for t in c.topics.split("|") if not Topic.objects.filter(slug=t).exists()]:
        out["topics"] = {"errors": [f"Không có chủ đề: {', '.join(unknown)}"], "warnings": []}
    if Word.objects.filter(translations__language_id="vi", translations__text=checks.build_vi(c.vi)["text"]).exists() and c.vi:
        out.setdefault("vi", {"errors": [], "warnings": []})["warnings"].append("Đã có từ khác cùng nghĩa tiếng Việt này")
    return out


def _slug(c: WordCandidate) -> str:
    base = slugify(c.en) or slugify(c.pinyin)
    slug, n = base, 2
    while Word.objects.filter(slug=slug).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


@transaction.atomic
def approve(c: WordCandidate, user) -> Word:
    from .management.commands.build_vocab import Command as BuildVocab

    row = {"slug": _slug(c), "topics": c.topics, "yolo_label": "", "pos": c.part_of_speech, "audience": c.audience,
           "difficulty": str(min(c.hsk_level, 3)), "vi": c.vi, "en": c.en,
           "en_aliases": ";".join(dict.fromkeys(g for g in (clean_gloss(x) for x in c.glosses[:4]) if g and g != c.en)),
           "zh_hans": c.zh_hans, "zh_hant": c.zh_hant}
    BuildVocab()._word(row, Word.objects.count(), offline=False)
    word = Word.objects.get(slug=row["slug"])
    word.levels = {"zh": min(c.hsk_level, 4), "en": min(c.hsk_level, 4), "vi": min(c.hsk_level, 4)}
    word.save(update_fields=["levels"])
    new_file = not APPROVED_CSV.exists()
    with open(APPROVED_CSV, "a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS, lineterminator="\n")
        if new_file:
            w.writeheader()
        w.writerow(row)
    c.status, c.word, c.reviewed_by, c.reviewed_at = WordCandidate.Status.APPROVED, word, user, timezone.now()
    c.save()
    return word


# ------------------------------------------------------------------ API

class CandidateSerializer(serializers.ModelSerializer):
    word_slug = serializers.CharField(source="word.slug", read_only=True, default=None)

    class Meta:
        model = WordCandidate
        fields = ["id", "zh_hans", "zh_hant", "pinyin", "hsk_level", "glosses", "en", "vi", "vi_options",
                  "part_of_speech", "topics", "audience", "confidence", "status", "checks", "note", "word_slug",
                  "reviewed_at"]
        read_only_fields = ["zh_hans", "pinyin", "hsk_level", "glosses", "vi_options", "confidence", "status", "checks",
                            "word_slug", "reviewed_at"]


@extend_schema(tags=["admin-vocab"])
class AdminCandidateViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                            viewsets.GenericViewSet):
    """Hàng chờ từ mới (HSK): sửa nghĩa → kiểm tra nguồn → duyệt (thêm vào kho từ) hoặc bỏ qua."""

    serializer_class = CandidateSerializer
    permission_classes = [IsStaffRole]
    filterset_fields = ["status", "hsk_level", "confidence"]
    search_fields = ["zh_hans", "zh_hant", "en", "vi"]
    queryset = WordCandidate.objects.all()

    @action(detail=True, methods=["post"])
    def check(self, request, pk=None):
        c = self.get_object()
        c.checks = check(c)
        c.save(update_fields=["checks", "updated_at"])
        return Response(self.get_serializer(c).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        c = self.get_object()
        if c.status != WordCandidate.Status.PENDING:
            return Response({"detail": "Từ này đã được xử lý"}, status=status.HTTP_400_BAD_REQUEST)
        c.checks = check(c)
        c.save(update_fields=["checks", "updated_at"])
        errors = [m for r in c.checks.values() for m in r["errors"]]
        if errors:
            return Response({"detail": "Chưa qua kiểm tra nguồn: " + "; ".join(errors), "candidate": self.get_serializer(c).data},
                            status=status.HTTP_400_BAD_REQUEST)
        approve(c, request.user)
        return Response(self.get_serializer(c).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        c = self.get_object()
        c.status, c.reviewed_by, c.reviewed_at = WordCandidate.Status.REJECTED, request.user, timezone.now()
        c.note = (request.data.get("note") or c.note)[:300]
        c.save()
        return Response(self.get_serializer(c).data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        from django.db.models import Count

        rows = WordCandidate.objects.values("hsk_level", "status").annotate(n=Count("id"))
        return Response({"rows": list(rows), "words": Word.objects.count()})
