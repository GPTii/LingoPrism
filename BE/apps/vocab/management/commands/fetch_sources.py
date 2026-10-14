import urllib.request

from django.core.management.base import BaseCommand

from apps.vocab.lang.sources import DOWNLOADS, SOURCES_DIR, USER_AGENT


class Command(BaseCommand):
    help = "Tải các nguồn dữ liệu ngôn ngữ chuẩn (CC-CEDICT, CMUdict, danh sách HSK) vào seed/sources/"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Tải lại kể cả khi đã có")

    def handle(self, *args, force=False, **opts):
        SOURCES_DIR.mkdir(parents=True, exist_ok=True)
        for name, url in DOWNLOADS.items():
            path = SOURCES_DIR / name
            if path.exists() and not force:
                self.stdout.write(f"✓ {name} (đã có)")
                continue
            self.stdout.write(f"↓ {name} ← {url}")
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as res:
                path.write_bytes(res.read())
            self.stdout.write(self.style.SUCCESS(f"✓ {name} ({path.stat().st_size // 1024} KB)"))
