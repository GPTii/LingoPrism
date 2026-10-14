from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.vocab.lang.sources import sources_available


class Command(BaseCommand):
    help = "Đổ toàn bộ dữ liệu demo: nguồn ngôn ngữ → từ vựng đã kiểm tra → tài khoản demo"

    def add_arguments(self, parser):
        parser.add_argument("--offline", action="store_true", help="Không gọi mạng (dùng cache moedict)")

    def handle(self, *args, offline=False, **opts):
        if not sources_available():
            call_command("fetch_sources")
        call_command("build_vocab", offline=offline)
        call_command("seed_gamification")
        call_command("generate_exams")
        call_command("seed_demo_users")
