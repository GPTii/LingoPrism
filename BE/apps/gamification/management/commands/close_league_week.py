from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.gamification.models import LeagueCycle
from apps.gamification.services import close_cycle


class Command(BaseCommand):
    help = "Chốt các giải đấu tuần đã kết thúc (chạy mỗi thứ Hai 00:05 bằng cron / Celery beat)"

    def handle(self, *args, **opts):
        cycles = LeagueCycle.objects.filter(status=LeagueCycle.Status.ACTIVE, end_at__lte=timezone.now())
        for c in cycles:
            close_cycle(c)
        self.stdout.write(f"Đã chốt {cycles.count()} nhóm giải đấu")
