from django.core.management.base import BaseCommand

from apps.algorithms import benchmark


class Command(BaseCommand):
    help = "Thử mọi thuật toán / tham số của từng quyết định, chọn tốt nhất theo quy tắc nêu rõ (và áp dụng với --apply)"

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Ghi cấu hình tốt nhất vào hệ thống")
        parser.add_argument("--tolerance", type=float, default=0.02, help="Mức giảm tỉ lệ nhớ chung chấp nhận được")
        parser.add_argument("--no-rerun", action="store_true", help="Dùng kết quả Distractor / Proximity đã có")

    def handle(self, *args, apply, tolerance, no_rerun, **opts):
        run = benchmark.run(apply=apply, tolerance=tolerance, rerun=not no_rerun, log=self.stdout.write)
        r = run.results
        self.stdout.write("\nDự đoán nhớ / quên trên tập test:")
        for k, m in r["prediction"]["models"].items():
            self.stdout.write(f"  {k:8s} log-loss {m['log_loss']}  AUC {m['auc']}  accuracy {m['accuracy']}")
        self.stdout.write("\n5 tổ hợp lịch ôn × thứ tự ôn có tỉ lệ nhớ chung cao nhất (mô phỏng):")
        for x in sorted(r["schedule"]["rows"], key=lambda x: -x["recall_all"])[:5]:
            self.stdout.write(f"  {benchmark.label(x):32s} nhớ chung {x['recall_all']:.1%}  từ dễ nhầm {x['recall_confusable']:.1%}")
        self.stdout.write("\nKiểm tra lại trên nhóm người học mới:")
        for v in r["schedule"]["validation"]:
            self.stdout.write(f"  {v['label']:32s} nhớ chung {v['recall_all']:.1%}  từ dễ nhầm {v['recall_confusable']:.1%}")
        self.stdout.write("\nQuyết định:")
        for d in r["decisions"]:
            self.stdout.write(f"  {d['decision']}: {d['chosen']}  ({d['evidence']})")
        self.stdout.write(self.style.SUCCESS(f"\nĐã áp dụng: {r['applied']}" if r["applied"] else "\nChưa áp dụng (thêm --apply)"))
