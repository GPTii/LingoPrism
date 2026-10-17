"""Compare detector setups on real photos, through the server's own inference code (BE/apps/detection/inference.py).

Expected labels come from the file name or the parent folder, as a label or slug of AI/classes.yaml:
    photos/cup.jpg, photos/cup_2.jpg, photos/kitchen/cup+spoon+bowl.jpg, photos/pillow/IMG_001.jpg
Photos whose name matches no class are skipped.

    python AI/scripts/eval_photos.py BE/media/photos --model coco=BE/models/yolov10n.onnx \
        --model oiv7+coco=AI/runs/oiv7-pretrained/yolov8s-oiv7-lingoprism.onnx+BE/models/yolov10n.onnx

top-1  : the most confident box is an expected object (photo of a single object)
recall : share of the expected objects found anywhere in the photo (photo of several objects)
wrong  : boxes whose label is not in the photo (false alarms shown to the learner)
"""
import argparse
import re
import sys
from pathlib import Path

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "BE"))
from apps.detection.inference import Detector, EnsembleDetector  # noqa: E402

classes = yaml.safe_load((ROOT / "AI" / "classes.yaml").read_text(encoding="utf-8"))["classes"]
ALIASES = {}
for c in classes:
    for key in (c["label"], c["slug"]):
        ALIASES[key.lower().replace(" ", "-")] = c["label"]
LABELS = [c["label"] for c in classes]


def expected(path: Path):
    for name in (path.stem, path.parent.name):
        parts = [re.sub(r"_[A-Za-z0-9]{7}$|[_ ]\d+$", "", p).lower().replace(" ", "-") for p in name.split("+")]
        found = {ALIASES[p] for p in parts if p in ALIASES}
        if found:
            return found
    return set()


def build(spec):
    """'a.onnx' or 'primary.onnx+coco_base.onnx' (served like the server: base answers for the classes it knows)."""
    paths = spec.split("+")
    primary = Detector(paths[0])
    return EnsembleDetector(primary, Detector(paths[1])) if len(paths) > 1 else primary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--model", action="append", required=True, help="tên=đường_dẫn.onnx[+coco_base.onnx]")
    ap.add_argument("-v", "--verbose", action="store_true", help="in kết quả từng ảnh")
    args = ap.parse_args()

    photos = [(p, expected(p)) for p in sorted(Path(args.folder).rglob("*"))
              if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
    photos = [(p, e) for p, e in photos if e]
    print(f"{len(photos)} ảnh có đáp án\n")
    print(f"{'model':28} {'top-1':>7} {'recall':>7} {'wrong':>6} {'ms/ảnh':>7}")
    for spec in args.model:
        name, path = spec.split("=", 1)
        det = build(path)
        top1 = found = total = wrong = ms = 0
        for p, exp in photos:
            boxes, t = det.predict(Image.open(p))
            boxes = [b for b in boxes if b.label in LABELS]
            got = {b.label for b in boxes}
            top1 += bool(boxes) and boxes[0].label in exp
            found += len(exp & got)
            total += len(exp)
            wrong += len(got - exp)
            ms += t
            if args.verbose:
                print(f"   {p.name:28} cần {sorted(exp)} → {[(b.label, round(b.confidence, 2)) for b in boxes[:4]]}")
        n = len(photos)
        print(f"{name:28} {top1 / n:7.0%} {found / total:7.0%} {wrong:6} {ms / n:7.0f}")


if __name__ == "__main__":
    main()
