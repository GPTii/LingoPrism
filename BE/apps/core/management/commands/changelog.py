from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.core.releases import changelog_markdown


class Command(BaseCommand):
    help = "Ghi CHANGELOG.md (gốc repo) từ apps/core/releases.json."

    def handle(self, *args, **opts):
        target = Path(settings.BASE_DIR).parent / "CHANGELOG.md"
        target.write_text(changelog_markdown(), encoding="utf-8", newline="\n")
        self.stdout.write(f"wrote {target}")
