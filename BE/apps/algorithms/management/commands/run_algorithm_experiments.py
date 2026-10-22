from django.core.management.base import BaseCommand

from apps.algorithms import experiments, vision, yolo_report

STEPS = ["yolo", "vision", "srs", "ga", "vip", "distractor", "proximity"]


class Command(BaseCommand):
    help = "Chạy các thực nghiệm của đề cương (SM-2/FSRS, GA, VIP, Smart Distractor, Proximity Search) và lưu kết quả"

    def add_arguments(self, parser):
        parser.add_argument("--only", nargs="*", choices=STEPS)
        parser.add_argument("--confusion", help="confusion_matrix.json của model YOLO đã train (nếu có)")

    def handle(self, *args, only=None, confusion=None, **opts):
        for step in only or STEPS:
            self.stdout.write(f"▶ {step}")
            if step == "yolo":
                run = yolo_report.run()
                for m in run.results["comparison"]["models"]:
                    self.stdout.write(f"  {m['model']}: {m['results']}")
            elif step == "vision":
                profile = vision.build(confusion)
                top = sorted(profile.items(), key=lambda kv: -kv[1]["score"])[:8]
                self.stdout.write("  dễ nhầm nhất: " + ", ".join(f"{k}={v['score']}" for k, v in top))
            elif step == "ga":
                run = experiments.run_ga(log=self.stdout.write)
                self.stdout.write(f"  test: {run.results['test']}  áp dụng={run.results['applied']}")
            else:
                run = getattr(experiments, step)()
                self.stdout.write(f"  {str(run.results)[:600]}")
