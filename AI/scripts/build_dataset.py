"""Build the LingoPrism YOLO dataset from COCO-2017 and Open Images V7 (via FiftyOne).

Run on Google Colab (needs ~15–25 GB of temporary disk):
    pip install -q fiftyone ultralytics pyyaml
    python AI/scripts/build_dataset.py --per-class 300 --out /content/lingoprism_ds

Output: YOLO format (images/{train,val,test}, labels/{train,val,test}) + data.yaml.
Split 70/20/10 with a fixed seed so results are reproducible.
"""
import argparse
import random
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_classes():
    data = yaml.safe_load((ROOT / "classes.yaml").read_text(encoding="utf-8"))
    return data["classes"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=300, help="ảnh tối đa mỗi lớp mỗi nguồn")
    ap.add_argument("--out", default="/content/lingoprism_ds")
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()

    import fiftyone as fo
    import fiftyone.utils.openimages as fouo
    import fiftyone.zoo as foz

    classes = load_classes()
    labels = [c["label"] for c in classes]
    coco_map = {c["coco"]: c["label"] for c in classes if c.get("coco")}
    oi_valid = set(fouo.get_classes())
    oi_map = {}
    for c in classes:
        if c.get("oi"):
            if c["oi"] in oi_valid:
                oi_map[c["oi"]] = c["label"]
            else:
                print(f"[cảnh báo] '{c['oi']}' không có trong Open Images V7 – bỏ qua nguồn này cho lớp {c['label']}")

    merged = fo.Dataset("lingoprism", overwrite=True)

    print("== COCO-2017 ==")
    coco = foz.load_zoo_dataset(
        "coco-2017", split="train", label_types=["detections"], classes=list(coco_map),
        max_samples=args.per_class * len(coco_map), shuffle=True, seed=args.seed, dataset_name="lp-coco",
    )
    for s in coco.iter_samples(progress=True):
        dets = [d for d in (s.ground_truth.detections if s.ground_truth else []) if d.label in coco_map]
        for d in dets:
            d.label = coco_map[d.label]
        s["gt"] = fo.Detections(detections=dets)
        merged.add_sample(fo.Sample(filepath=s.filepath, gt=s["gt"]))

    print("== Open Images V7 ==")
    oi = foz.load_zoo_dataset(
        "open-images-v7", split="train", label_types=["detections"], classes=list(oi_map),
        max_samples=args.per_class * len(oi_map), shuffle=True, seed=args.seed, dataset_name="lp-oi",
    )
    for s in oi.iter_samples(progress=True):
        src = s.ground_truth.detections if s.ground_truth else []
        dets = [d for d in src if d.label in oi_map]
        for d in dets:
            d.label = oi_map[d.label]
        merged.add_sample(fo.Sample(filepath=s.filepath, gt=fo.Detections(detections=dets)))

    # drop images without any of our classes, then split
    merged = merged.match(fo.ViewField("gt.detections").length() > 0).clone("lingoprism-clean")
    ids = merged.values("id")
    random.Random(args.seed).shuffle(ids)
    n = len(ids)
    splits = {"train": ids[: int(n * 0.7)], "val": ids[int(n * 0.7): int(n * 0.9)], "test": ids[int(n * 0.9):]}
    out = Path(args.out)
    for split, split_ids in splits.items():
        merged.select(split_ids).export(
            export_dir=str(out), dataset_type=fo.types.YOLOv5Dataset, label_field="gt", split=split, classes=labels,
        )
    (out / "data.yaml").write_text(yaml.safe_dump({
        "path": str(out), "train": "images/train", "val": "images/val", "test": "images/test",
        "names": {i: n for i, n in enumerate(labels)},
    }, allow_unicode=True), encoding="utf-8")

    counts = Counter(d.label for s in merged.iter_samples() for d in s.gt.detections)
    print(f"Tổng ảnh: {n}  (train {len(splits['train'])}, val {len(splits['val'])}, test {len(splits['test'])})")
    for label in labels:
        print(f"  {label:15} {counts.get(label, 0):6} box")


if __name__ == "__main__":
    main()
