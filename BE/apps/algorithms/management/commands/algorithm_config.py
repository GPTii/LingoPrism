import json
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.algorithms.models import AlgorithmConfig, ExperimentRun

FIELDS = ["scheduler", "review_priority", "distractor", "proximity", "fsrs_weights", "vip_weights", "desired_retention"]


class Command(BaseCommand):
    help = ("Xuất / nạp cấu hình thuật toán (AlgorithmConfig) và hồ sơ nhầm lẫn thị giác của VIP dạng JSON – đưa kết quả "
            "benchmark ở máy lên server: --export deploy/algorithm_config.json ở máy, deploy.sh nạp lại bằng --load -")

    def add_arguments(self, parser):
        parser.add_argument("--export", metavar="FILE")
        parser.add_argument("--load", metavar="FILE", help="'-' = đọc từ stdin")

    def handle(self, *args, export=None, load=None, **opts):
        if bool(export) == bool(load):
            raise CommandError("Dùng đúng một trong --export / --load")
        config = AlgorithmConfig.get()
        if export:
            data = {f: getattr(config, f) for f in FIELDS}
            # VIP's visual-confusion profile (notebook 03, from the YOLO test-set confusion matrix): the server cannot
            # rebuild it, the test set and AI/ are not deployed
            vision = ExperimentRun.objects.filter(kind="vision").first()
            if vision:
                data["vision"] = vision.results
            Path(export).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Đã xuất {export}"))
            return
        # "-" = stdin: deploy.sh pipes the file in, the container does not see deploy/
        data = json.load(sys.stdin) if load == "-" else json.loads(Path(load).read_text(encoding="utf-8"))
        vision = data.pop("vision", None)
        unknown = set(data) - set(FIELDS)
        if unknown:
            raise CommandError(f"Trường không hợp lệ: {', '.join(sorted(unknown))}")
        for f, v in data.items():
            setattr(config, f, v)
        config.full_clean()
        config.save()
        if vision:
            ExperimentRun.objects.create(kind="vision", results=vision)
        self.stdout.write(self.style.SUCCESS(
            f"Đã nạp: {config.scheduler} · {config.review_priority} · {config.distractor} · {config.proximity}"
            + (f" · hồ sơ thị giác {len(vision.get('classes', {}))} lớp ({vision.get('source')})" if vision else "")))
