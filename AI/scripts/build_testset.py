"""Labelled test set for the thesis: confusion matrix, precision / recall / F1, mAP of every detector setup.

Images come from the *validation* splits of COCO-2017 and Open Images V7. No model saw them: the self-trained v1 was
trained on our dataset built from the train splits (build_dataset.py), the COCO yolov10n on COCO train2017, the
Open Images yolov8s on Open Images train.

    C:/lpvenv/Scripts/python AI/scripts/build_testset.py --per-class 30        # ~3 000 images, ~1 GB download

Fair scoring (the Open Images protocol): a source labels only some classes in an image, so each image lists its
`evaluable` classes and a prediction of another class is ignored, not counted as a false positive:
  * COCO image  -> every LingoPrism class that has a COCO category (COCO boxes are exhaustive for its 80 classes);
  * OI image    -> the classes verified present or absent in that image (image-level positive / negative labels).
Images with a COCO crowd box or an Open Images group-of / depiction box of our classes are left out (one box over
many objects, or a drawing, cannot be matched fairly).

Output: AI/testset/images/*.jpg (long side 640 px) + AI/testset/annotations.json
    {"classes": [...], "images": [{"file", "source", "evaluable": [...], "boxes": [{"label", "bbox": [x1,y1,x2,y2]}]}]}
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "testset"


def _flag(det, name):
    return det.has_field(name) and bool(det[name])


def _xyxy(d):
    x, y, w, h = d.bounding_box  # FiftyOne: relative top-left x, y, width, height
    return [round(x, 5), round(y, 5), round(min(1.0, x + w), 5), round(min(1.0, y + h), 5)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=30, help="ảnh tối đa mỗi lớp mỗi nguồn")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--max-side", type=int, default=640)
    args = ap.parse_args()

    import fiftyone.utils.openimages as fouo
    import fiftyone.zoo as foz
    from PIL import Image

    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from export_pretrained_oiv7 import EXTRA

    classes = yaml.safe_load((ROOT / "classes.yaml").read_text(encoding="utf-8"))["classes"]
    labels = [c["label"] for c in classes]
    coco_map = {c["coco"]: c["label"] for c in classes if c.get("coco")}
    oi_valid = set(fouo.get_classes())
    oi_map = {}
    for c in classes:
        for name in ([c["oi"]] if c.get("oi") else []) + EXTRA.get(c["label"], []):
            if name in oi_valid:
                oi_map[name] = c["label"]
    coco_evaluable = sorted(set(coco_map.values()))

    (OUT / "images").mkdir(parents=True, exist_ok=True)
    images, seen, dropped = [], set(), Counter()

    def add(sample, source, boxes, evaluable):
        key = Path(sample.filepath).name
        if key in seen or not boxes:
            return
        seen.add(key)
        name = f"{source}_{Path(key).stem}.jpg"
        with Image.open(sample.filepath) as im:
            im = im.convert("RGB")
            im.thumbnail((args.max_side, args.max_side))
            im.save(OUT / "images" / name, quality=90)
        images.append({"file": name, "source": source, "evaluable": evaluable, "boxes": boxes})

    print("== COCO-2017 validation ==")
    for coco_name in coco_map:
        ds = foz.load_zoo_dataset("coco-2017", split="validation", label_types=["detections"], classes=[coco_name],
                                  max_samples=args.per_class, shuffle=True, seed=args.seed,
                                  dataset_name=f"lp-test-coco-{coco_name}")
        for s in ds.iter_samples():
            src = s.ground_truth.detections if s.ground_truth else []
            if any(_flag(d, "iscrowd") for d in src):
                dropped["coco crowd"] += 1
                continue
            add(s, "coco", [{"label": coco_map[d.label], "bbox": _xyxy(d)} for d in src if d.label in coco_map],
                coco_evaluable)
        ds.delete()

    print("== Open Images V7 validation ==")
    for oi_name in oi_map:
        ds = foz.load_zoo_dataset("open-images-v7", split="validation", label_types=["detections", "classifications"],
                                  classes=[oi_name], max_samples=args.per_class, shuffle=True, seed=args.seed,
                                  dataset_name=f"lp-test-oi-{oi_name}")
        for s in ds.iter_samples():
            src = s.detections.detections if s.detections else []  # several label types: one field per type
            ours = [d for d in src if d.label in oi_map]
            if any(_flag(d, "IsGroupOf") or _flag(d, "IsDepiction") for d in ours):
                dropped["oi group-of / depiction"] += 1
                continue
            verified = set()
            for field in ("positive_labels", "negative_labels"):
                if s.has_field(field) and s[field]:
                    verified |= {c.label for c in s[field].classifications}
            verified |= {d.label for d in ours}
            evaluable = sorted({oi_map[n] for n in verified if n in oi_map})
            add(s, "oi", [{"label": oi_map[d.label], "bbox": _xyxy(d)} for d in ours], evaluable)
        ds.delete()

    (OUT / "annotations.json").write_text(json.dumps({"classes": labels, "images": images}, ensure_ascii=False),
                                          encoding="utf-8")
    counts = Counter(b["label"] for im in images for b in im["boxes"])
    print(f"{len(images)} ảnh ({sum(im['source'] == 'coco' for im in images)} COCO, "
          f"{sum(im['source'] == 'oi' for im in images)} Open Images), {sum(counts.values())} box. Đã bỏ: {dict(dropped)}")
    for lab in labels:
        print(f"  {lab:15} {counts.get(lab, 0):5} box")


if __name__ == "__main__":
    main()
