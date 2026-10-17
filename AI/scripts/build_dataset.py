"""Build the LingoPrism YOLO dataset from COCO-2017 and Open Images V7 (via FiftyOne).

Run on Google Colab (needs ~15–25 GB of temporary disk):
    pip install -q fiftyone ultralytics pyyaml
    python AI/scripts/build_dataset.py --per-class 300 --out /content/lingoprism_ds

Output: YOLO format (images/{train,val,test}, labels/{train,val,test}) + data.yaml.
Split 70/20/10 with a fixed seed so results are reproducible.
Images are downscaled to a long side of 640 px (Open Images originals are 1024 px+ and decoding them
on Colab's 2 CPUs is what bottlenecks training). Labels are normalized, so they stay valid.
    python AI/scripts/build_dataset.py --shrink-only --out /content/lingoprism_ds   # for an existing dataset

Label clean-up (v3):
  * images with a COCO "crowd" box or an Open Images "group of" box (one box over many objects) are dropped,
    Open Images boxes on a depiction (drawing, poster, toy picture) are dropped
  * --pseudo-label: each source only labels its own classes – a pillow in a COCO photo, a person in an Open Images
    photo is unlabeled, so training teaches the model to *ignore* it. Large pretrained teachers (COCO yolo11x,
    Open Images yolov8x-oiv7) add their confident boxes (>= 0.5) for the missing objects, on the train split only;
    val/test keep the human labels so the reported metrics stay honest. Needs a GPU (~20–30 min on a T4).
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


def _shrink_one(path, max_side):
    from PIL import Image
    with Image.open(path) as im:
        if max(im.size) <= max_side:
            return 0
        exif = im.info.get("exif", b"")  # keep EXIF orientation – ultralytics/cv2 honour it when loading
        im = im.convert("RGB")
        im.thumbnail((max_side, max_side), Image.LANCZOS)
    im.save(path, "JPEG", quality=90, exif=exif)
    return 1


def shrink_images(out, max_side=640):
    """Downscale every image so its long side is <= max_side (idempotent, fast on a 2nd run)."""
    from concurrent.futures import ProcessPoolExecutor
    from functools import partial
    import os
    paths = [p for p in Path(out, "images").rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")]
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
        n = sum(ex.map(partial(_shrink_one, max_side=max_side), paths, chunksize=64))
    print(f"Thu nhỏ {n}/{len(paths)} ảnh về cạnh dài <= {max_side}px")


def _flag(det, name):
    return det.has_field(name) and bool(det[name])


def _iou_xywh(a, b):
    ax1, ay1, ax2, ay2 = a[0] - a[2] / 2, a[1] - a[3] / 2, a[0] + a[2] / 2, a[1] + a[3] / 2
    bx1, by1, bx2, by2 = b[0] - b[2] / 2, b[1] - b[3] / 2, b[0] + b[2] / 2, b[1] + b[3] / 2
    inter = max(0.0, min(ax2, bx2) - max(ax1, bx1)) * max(0.0, min(ay2, by2) - max(ay1, by1))
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union > 0 else 0.0


def pseudo_label(out, classes, conf=0.5, split="train", coco_teacher="yolo11x.pt", oi_teacher="yolov8x-oiv7.pt"):
    """Add confident teacher boxes for objects the source dataset left unlabeled (see module docstring)."""
    from ultralytics import YOLO

    from export_pretrained_oiv7 import EXTRA

    labels = [c["label"] for c in classes]
    index = {lab: i for i, lab in enumerate(labels)}
    coco_known = {c["label"] for c in classes if c.get("coco")}
    coco_map = {c["coco"]: c["label"] for c in classes if c.get("coco")}
    oi_map = {}
    for c in classes:
        for name in ([c["oi"]] if c.get("oi") else []) + EXTRA.get(c["label"], []):
            oi_map[name] = c["label"]
    # each teacher only answers for the classes it is best at; Open Images first, because COCO names an object it
    # was never taught after the closest class it knows (tiger -> zebra) and those boxes must be refused below
    teachers = [(oi_teacher, oi_map, set(labels) - coco_known), (coco_teacher, coco_map, coco_known)]
    coco_unknown = {index[lab] for lab in set(labels) - coco_known}

    images = sorted(p for p in Path(out, "images", split).iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    added = Counter()
    for weights, name_map, allowed in teachers:
        teacher = YOLO(weights)
        print(f"== Gán nhãn bù bằng {weights} ({len(allowed)} lớp) ==")
        for r in teacher.predict(source=[str(p) for p in images], stream=True, conf=conf, imgsz=640, verbose=False):
            label_file = Path(out, "labels", split, Path(r.path).stem + ".txt")
            lines = label_file.read_text().split("\n") if label_file.exists() else []
            boxes = [(int(v[0]), [float(x) for x in v[1:5]]) for v in (ln.split() for ln in lines) if len(v) >= 5]
            new = []
            for cls, xywh in zip(r.boxes.cls.tolist(), r.boxes.xywhn.tolist()):
                label = name_map.get(teacher.names[int(cls)])
                if label not in allowed:
                    continue
                k = index[label]
                # already labeled: same class on the same spot, or any class on exactly this object
                if any(_iou_xywh(xywh, b) >= (0.5 if c == k else 0.7) for c, b in boxes):
                    continue
                if weights == coco_teacher and any(c in coco_unknown and _iou_xywh(xywh, b) >= 0.5 for c, b in boxes):
                    continue
                boxes.append((k, xywh))
                new.append(f"{k} " + " ".join(f"{v:.6f}" for v in xywh))
                added[label] += 1
            if new:
                label_file.write_text("\n".join([ln for ln in lines if ln.strip()] + new) + "\n")
    for cache in Path(out, "labels").glob("*.cache"):
        cache.unlink()
    print(f"Đã thêm {sum(added.values())} box: " + ", ".join(f"{k} {v}" for k, v in added.most_common()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=300, help="ảnh tối đa mỗi lớp mỗi nguồn")
    ap.add_argument("--out", default="/content/lingoprism_ds")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--max-side", type=int, default=640, help="cạnh dài tối đa của ảnh (= imgsz khi train)")
    ap.add_argument("--shrink-only", action="store_true", help="chỉ thu nhỏ ảnh của dataset đã có")
    ap.add_argument("--pseudo-label", action="store_true", help="gán nhãn bù cho tập train bằng model lớn (cần GPU)")
    args = ap.parse_args()
    if args.shrink_only:
        shrink_images(args.out, args.max_side)
        return

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
    dropped = Counter()
    for s in coco.iter_samples(progress=True):
        src = s.ground_truth.detections if s.ground_truth else []
        if any(_flag(d, "iscrowd") for d in src):  # one box over a crowd: the objects in it are unlabeled
            dropped["coco crowd"] += 1
            continue
        dets = [d for d in src if d.label in coco_map]
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
        if any(_flag(d, "IsGroupOf") for d in src):
            dropped["oi group-of"] += 1
            continue
        dets = [d for d in src if d.label in oi_map and not _flag(d, "IsDepiction")]
        dropped["oi depiction box"] += sum(1 for d in src if d.label in oi_map and _flag(d, "IsDepiction"))
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
    shrink_images(out, args.max_side)
    print("Đã lọc:", dict(dropped))
    if args.pseudo_label:
        pseudo_label(out, classes)

    counts = Counter(d.label for s in merged.iter_samples() for d in s.gt.detections)
    print(f"Tổng ảnh: {n}  (train {len(splits['train'])}, val {len(splits['val'])}, test {len(splits['test'])})")
    for label in labels:
        print(f"  {label:15} {counts.get(label, 0):6} box")


if __name__ == "__main__":
    main()
