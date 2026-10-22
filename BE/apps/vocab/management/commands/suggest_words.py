from django.core.management.base import BaseCommand

from apps.vocab.candidates import WIKTIONARY, suggest


class Command(BaseCommand):
    help = "Đề xuất từ mới theo HSK vào hàng chờ duyệt (nghĩa Anh: CC-CEDICT, nghĩa Việt: Wiktionary tiếng Việt)"

    def add_arguments(self, parser):
        parser.add_argument("--levels", nargs="*", type=int, default=[1, 2, 3])

    def handle(self, *args, levels, **opts):
        if not WIKTIONARY.exists():
            self.stderr.write("Thiếu dữ liệu Wiktionary – tải: https://kaikki.org/dictionary/Vietnamese/"
                              "kaikki.org-dictionary-Vietnamese.jsonl.gz → seed/sources/wiktionary/vi.jsonl.gz")
            return
        self.stdout.write(self.style.SUCCESS(f"Đã thêm {suggest(tuple(levels))} từ vào hàng chờ duyệt"))
