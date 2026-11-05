"""Old vs new server detector on real photos, through the server's own code (BE/apps/detection/inference.py).

Photo sets (never used for training):
  * word photos: the reviewed Wikimedia Commons photo of every word with a YOLO label (BE/seed/images/<slug>.jpg,
    label from the database: Word.yolo_label);
  * own photos: AI/eval_photos/ (file name = the objects in it, e.g. cup+spoon.jpg).

Setups:
  * old: yolov8m-oiv7 + COCO m (INT8), "most confident box wins" merge, CLIP when YOLO < 0.6 (until 06/11/2026)
  * new: yolov8l-oiv7 + COCO m (INT8), weighted box fusion, CLIP when YOLO < 0.6 (from 06/11/2026)

    cd BE && .venv/Scripts/python ../AI/scripts/eval_word_photos.py

Writes AI/report/yolo/word_photos.json and prints the table used in AI/report/yolo/ensemble_upgrade.md.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "BE"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
import django  # noqa: E402

django.setup()
from apps.algorithms import yolo_report as R  # noqa: E402
from apps.detection import inference as I  # noqa: E402

MODELS = ROOT / "BE" / "models"
SETUPS = {
    "old": (MODELS / "yolov8m-oiv7-lingoprism-int8.onnx", "merge", 0.6),
    "new": (MODELS / "yolov8l-oiv7-lingoprism-int8.onnx", "wbf", 0.6),
}


class OldEnsemble(I.EnsembleDetector):
    """The merge served until 06/11/2026: no fusion, the most confident box of an object wins."""

    def __init__(self, primary, base):
        self.primary, self.base, self.classes, self.name = primary, base, primary.classes, f"{primary.name}+coco"
        self._base_classes = set(base.classes)

    def combine(self, b_new, b_base, min_conf=None):
        known = set(self.classes)
        unknown = [b for b in b_new if b.label not in self._base_classes and b.confidence >= I.SURE_UNKNOWN]
        b_base = [b for b in b_base if b.label in known and not any(I._iou(b.bbox, n.bbox) >= 0.5 for n in unknown)]
        return I._merge([I.Box(b.label, b.confidence, b.bbox, list(b.top_k), b.memory_id) for b in b_base + b_new])


def main():
    clip = I.LabelVerifier(str(MODELS / "clip-mobileclip2-s2.onnx"))
    out = {}
    for name, (path, fusion, clip_max) in SETUPS.items():
        I.CLIP_MAX_CONF = clip_max
        primary, coco = I.Detector(str(path)), I.Detector(str(MODELS / "yolov10m-int8.onnx"))
        ens = (OldEnsemble if fusion == "merge" else I.EnsembleDetector)(primary, coco)
        det = I.VerifiedDetector(ens, clip)
        sets = R.photo_sets(primary.classes)
        out[name] = {}
        for set_name, photos in sets.items():
            if photos:
                out[name][set_name], per_photo = R._score(det, photos, set(coco.classes))
                out[name][set_name + "_per_photo"] = per_photo
        print(name, {k: v for k, v in out[name].items() if not k.endswith("_per_photo")}, flush=True)
    (ROOT / "AI" / "report" / "yolo" / "word_photos.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                                                    encoding="utf-8")
    print("\n| Bộ ảnh | Cấu hình | Số ảnh | Top-1 | Top-1 lớp ngoài COCO | Tìm thấy | Precision | Box sai | ms/ảnh |")
    print("|---|---|---|---|---|---|---|---|---|")
    for set_name in ("word_photos", "own_photos"):
        for name in SETUPS:
            r = out[name].get(set_name)
            if r:
                print(f"| {set_name} | {name} | {r['photos']} | {r['top1']:.0%} | {r['top1_new_classes'] or 0:.0%} | "
                      f"{r['found']:.0%} | {r['precision']:.0%} | {r['wrong_boxes']} | {r['ms_per_image']} |")


if __name__ == "__main__":
    main()
