import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.detection.models import ModelVersion
from apps.vocab.models import Word


class Command(BaseCommand):
    help = "Đăng ký model YOLOv10 đã train (đọc model_card.json do AI/scripts/train_eval_export.py tạo) và kích hoạt"

    def add_arguments(self, parser):
        parser.add_argument("--onnx", required=True, help="Đường dẫn file .onnx trên server")
        parser.add_argument("--card", required=True, help="Đường dẫn model_card.json")
        parser.add_argument("--no-activate", action="store_true")

    def handle(self, *args, onnx, card, no_activate=False, **opts):
        onnx_path, card_path = Path(onnx), Path(card)
        if not onnx_path.exists() or not card_path.exists():
            raise CommandError("Không tìm thấy file .onnx hoặc model_card.json")
        info = json.loads(card_path.read_text(encoding="utf-8"))
        m = info.get("metrics", {})
        mv, _ = ModelVersion.objects.update_or_create(name=info["name"], defaults={
            "file": str(onnx_path.resolve()), "classes": info["classes"], "input_size": info.get("imgsz", 640),
            "precision": m.get("precision"), "recall": m.get("recall"), "map50": m.get("map50"),
            "map50_95": m.get("map50_95"), "is_active": not no_activate,
        })
        if mv.is_active:
            ModelVersion.objects.exclude(pk=mv.pk).update(is_active=False)
        mapped = set(Word.objects.filter(yolo_label__in=info["classes"]).values_list("yolo_label", flat=True))
        unmapped = [c for c in info["classes"] if c not in mapped]
        self.stdout.write(self.style.SUCCESS(f"Đã đăng ký {mv.name} (mAP50={mv.map50}) – active={mv.is_active}"))
        if unmapped:
            self.stdout.write(self.style.WARNING(f"Lớp chưa gắn với từ vựng (yolo_label): {', '.join(unmapped)}"))
