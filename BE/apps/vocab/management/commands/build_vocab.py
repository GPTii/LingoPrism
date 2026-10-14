import csv
from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.vocab.lang import checks, sources
from apps.vocab.models import Language, ReviewStatus, Topic, TopicWord, Word, WordTranslation

LANGUAGES = [
    ("vi", "Tiếng Việt", "Tiếng Việt", "vi-VN", 1),
    ("en", "Tiếng Anh", "English", "en-US", 2),
    ("zh-Hans", "Tiếng Trung giản thể (đại lục)", "简体中文", "zh-CN", 3),
    ("zh-Hant", "Tiếng Trung phồn thể (Đài Loan)", "繁體中文", "zh-TW", 4),
]
TRANSLATION_FIELDS = [
    "ipa", "pinyin", "pinyin_numbered", "zhuyin", "measure_word", "level", "meaning_en",
]


class Command(BaseCommand):
    help = "Dựng dữ liệu từ vựng từ seed/concepts/*.csv và kiểm tra chéo với các nguồn chuẩn (PLAN.md §3b)"

    def add_arguments(self, parser):
        parser.add_argument("--offline", action="store_true", help="Không gọi moedict qua mạng, chỉ dùng cache")
        parser.add_argument("--only", nargs="*", help="Chỉ xử lý các slug này")

    def handle(self, *args, offline=False, only=None, **opts):
        concepts = sources.SEED_DIR / "concepts"
        for code, name, native, tts, order in LANGUAGES:
            Language.objects.update_or_create(
                code=code, defaults={"name": name, "native_name": native, "tts_locale": tts, "order": order}
            )
        self._topics(concepts / "topics.csv")

        stats = Counter()
        flagged = []
        with open(concepts / "words.csv", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        for i, row in enumerate(rows):
            if only and row["slug"] not in only:
                continue
            result = self._word(row, i, offline)
            for code, status, issues in result:
                stats[(code, status)] += 1
                if status == ReviewStatus.FLAGGED:
                    flagged.append((row["slug"], code, [x for x in issues if x["level"] == "error"]))
            if i % 25 == 0:
                sources.moedict().save()
        sources.moedict().save()

        self.stdout.write("")
        for code, *_ in LANGUAGES:
            self.stdout.write(
                f"{code:8} verified={stats[(code, 'verified')]:4}  flagged={stats[(code, 'flagged')]:4}"
                f"  (giữ nguyên thủ công={stats[(code, 'kept')]})"
            )
        if flagged:
            self.stdout.write(self.style.WARNING(f"\n{len(flagged)} bản dịch cần xem lại (ẩn với học viên):"))
            for slug, code, errors in flagged:
                self.stdout.write(f"  - {slug} [{code}]: " + " | ".join(e["message"] for e in errors))

    def _topics(self, path):
        ced = sources.cedict()
        with open(path, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                for field, banned, label in (("name_zh_hans", ced.traditional_only, "phồn thể"),
                                             ("name_zh_hant", ced.simplified_only, "giản thể")):
                    bad = [ch for ch in row[field] if ch in banned]
                    in_dict = row[field] in (ced.by_simp if field == "name_zh_hans" else ced.by_trad)
                    if bad or not in_dict:
                        self.stdout.write(self.style.ERROR(
                            f"Chủ đề {row['slug']}: '{row[field]}' " + (f"lẫn chữ {label}" if bad else "không có trong CC-CEDICT")))
                Topic.objects.update_or_create(
                    slug=row["slug"],
                    defaults={
                        "order": int(row["order"]), "icon": row["icon"], "audience": row["audience"],
                        "name_vi": row["name_vi"], "name_en": row["name_en"],
                        "name_zh_hans": row["name_zh_hans"], "name_zh_hant": row["name_zh_hant"],
                        "owner": None, "visibility": Topic.Visibility.PUBLIC,
                    },
                )

    @transaction.atomic
    def _word(self, row, order, offline):
        word, _ = Word.objects.update_or_create(
            slug=row["slug"],
            defaults={
                "yolo_label": row["yolo_label"], "part_of_speech": row["pos"], "audience": row["audience"],
                "difficulty": int(row["difficulty"] or 1),
            },
        )
        for topic_slug in filter(None, row["topics"].split("|")):
            topic = Topic.objects.get(slug=topic_slug)
            TopicWord.objects.get_or_create(topic=topic, word=word, defaults={"order": order})

        en_terms = [row["en"]] + [a for a in row["en_aliases"].split(";") if a]
        is_noun = row["pos"] == "noun"
        vi = checks.build_vi(row["vi"])
        en = checks.build_en(row["en"])
        hans = checks.build_zh_hans(row["zh_hans"], en_terms, is_noun, prefer_trad=row["zh_hant"])
        hant = checks.build_zh_hant(row["zh_hant"], en_terms, is_noun, allow_network=not offline)
        regional = checks.check_hans_hant_pair(hans, hant)

        results = []
        for code, data in (("vi", vi), ("en", en), ("zh-Hans", hans), ("zh-Hant", hant)):
            results.append(self._save(word, code, data, vi["text"], en["text"], regional and code.startswith("zh")))
        return results

    def _save(self, word, code, data, meaning_vi, meaning_en, regional):
        issues = [{"level": "error", "message": m} for m in data["errors"]]
        issues += [{"level": "warning", "message": m} for m in data["warnings"]]
        tr = WordTranslation.objects.filter(word=word, language_id=code).first()
        if tr and tr.text == data["text"] and (
            tr.status == ReviewStatus.REJECTED or (tr.status == ReviewStatus.VERIFIED and tr.verified_method == "manual")
        ):
            tr.issues, tr.sources = issues, data["sources"]
            tr.save(update_fields=["issues", "sources", "updated_at"])
            return code, "kept", issues

        tr = tr or WordTranslation(word=word, language_id=code)
        tr.text = data["text"]
        for f in TRANSLATION_FIELDS:
            setattr(tr, f, data.get(f, "") or "")
        if code == "en":
            tr.meaning_en = meaning_en
        tr.meaning_vi = meaning_vi
        tr.regional_difference = regional
        tr.sources = data["sources"]
        tr.issues = issues
        tr.mark(ReviewStatus.FLAGGED if data["errors"] else ReviewStatus.VERIFIED, method="auto")
        tr.save()
        return code, tr.status, issues
