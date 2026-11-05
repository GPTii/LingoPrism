"""Fine-tune dataset v7: the base model labels what people did not draw on the new COCO/LVIS photos (pseudo-labels).

Why (AI/report/yolo/finetune_ft6.md): on the COCO train2017 photos of v6 only COCO's 80 classes are drawn exhaustively;
LVIS boxes are federated (an image is checked for a few categories only) and window / door / mango… have no LVIS
category at all. Every object without a box is taught as *background*: v6 lost door (-0.20), bird, bread, bench, and
pushed look-alike labels onto COCO objects (orange -> lemon, sheep -> pig, fork -> chopsticks).

This script runs the base model (the "teacher", yolov8m-oiv7, never the fine-tuned one) on every coco_*.jpg of the
dataset and adds its confident boxes (>= --conf) where people drew nothing:
  * classes of COCO's 80 labels: never – COCO's boxes are exhaustive, a teacher box there would only add its mistakes;
  * classes of the LVIS labels (chopsticks, egg, pillow…): only when no human box of that label overlaps (IoU >= 0.5),
    LVIS may simply not have checked the image for it;
  * every other Open Images class (door, window, human face, plate's neighbours, clothing…): yes.
The Open Images replay photos are left as they are (the base model learnt from exactly those labels).

    python AI/scripts/pseudo_label_finetune.py --data DS --conf 0.5

The human labels are kept in <DS>/labels_human/ so a rerun (another --conf) starts again from them; <DS>/pseudo.json
records what was added. Ultralytics' label caches are removed.
"""
import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_lvis_finetune import LVIS_MAP  # noqa: E402
from build_oiv7_finetune import label_groups  # noqa: E402


def coco_names() -> set[str]:
    import ultralytics

    data = yaml.safe_load((Path(ultralytics.__file__).parent / "cfg" / "datasets" / "coco.yaml").read_text(encoding="utf-8"))
    return set(data["names"].values())


def iou(a, b) -> float:  # boxes as (cx, cy, w, h), relative
    ax1, ay1, ax2, ay2 = a[0] - a[2] / 2, a[1] - a[3] / 2, a[0] + a[2] / 2, a[1] + a[3] / 2
    bx1, by1, bx2, by2 = b[0] - b[2] / 2, b[1] - b[3] / 2, b[0] + b[2] / 2, b[1] + b[3] / 2
    iw, ih = max(0.0, min(ax2, bx2) - max(ax1, bx1)), max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = iw * ih
    return inter / (a[2] * a[3] + b[2] * b[3] - inter + 1e-9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="thư mục dataset (có images/, labels/, summary.json)")
    ap.add_argument("--base", default="yolov8m-oiv7.pt", help="model thầy – luôn là model gốc")
    ap.add_argument("--conf", type=float, default=0.5)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--limit", type=int, default=0, help="chỉ thử N ảnh (kiểm tra nhanh)")
    args = ap.parse_args()

    from ultralytics import YOLO

    ds = Path(args.data)
    marker = ds / "pseudo.json"
    if marker.exists() and json.loads(marker.read_text(encoding="utf-8")).get("conf") == args.conf and not args.limit:
        print(f"Đã gán nhãn giả (conf {args.conf}) – bỏ qua")
        return

    model = YOLO(args.base)
    names = model.names
    groups = label_groups(names)
    label_of = {i: lab for lab, idx in groups.items() for i in idx}
    coco = coco_names() & set(groups)
    lvis = set(LVIS_MAP) & set(groups) - coco
    never = {i for lab in coco for i in groups[lab]}  # COCO classes: exhaustive human boxes
    print(f"Nhãn COCO (không gán thêm): {len(coco)}; nhãn LVIS (gán khi chưa có box người): {len(lvis)}; "
          f"lớp Open Images được gán: {len(names) - len(never)}", flush=True)

    files = []
    for part in ("train", "val"):
        for img in sorted((ds / "images" / part).glob("coco_*.jpg")):
            files.append((part, img))
    if args.limit:
        files = files[: args.limit]
    added, images_with = Counter(), 0
    for k in range(0, len(files), args.batch):
        chunk = files[k: k + args.batch]
        results = model.predict([str(f) for _, f in chunk], conf=args.conf, imgsz=args.imgsz, verbose=False)
        for (part, img), res in zip(chunk, results):
            label = ds / "labels" / part / f"{img.stem}.txt"
            backup = ds / "labels_human" / part / f"{img.stem}.txt"
            if not backup.exists():
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(label, backup) if label.exists() else backup.write_text("", encoding="utf-8")
            human = []
            for line in backup.read_text(encoding="utf-8").split("\n"):
                if line.strip():
                    c, *xywh = line.split()
                    human.append((int(c), [float(v) for v in xywh]))
            extra = []
            for c, xywh in zip(res.boxes.cls.tolist(), res.boxes.xywhn.tolist()):
                c = int(c)
                if c in never:
                    continue
                lab = label_of.get(c)
                if lab in lvis and any(label_of.get(h) == lab and iou(xywh, b) >= 0.5 for h, b in human):
                    continue
                if any(h == c and iou(xywh, b) >= 0.7 for h, b in human + extra):  # the same box twice
                    continue
                extra.append((c, xywh))
                added[names[c]] += 1
            images_with += bool(extra)
            lines = [f"{c} {' '.join(f'{v:.6f}' for v in b)}" for c, b in human + extra]
            label.write_text("\n".join(lines) + "\n", encoding="utf-8")
        done = min(k + args.batch, len(files))
        if done % (args.batch * 20) < args.batch or done == len(files):
            print(f"   {done}/{len(files)} ảnh, +{sum(added.values())} box", flush=True)

    for cache in (ds / "labels").glob("*.cache"):
        cache.unlink()
    info = {"conf": args.conf, "teacher": args.base, "images": len(files), "images_with_pseudo": images_with,
            "boxes": sum(added.values()), "per_class": dict(added.most_common())}
    if not args.limit:
        marker.write_text(json.dumps(info, indent=1, ensure_ascii=False), encoding="utf-8")
    top = ", ".join(f"{n} {v}" for n, v in added.most_common(25))
    print(f"→ +{info['boxes']} box nhãn giả trên {images_with}/{len(files)} ảnh COCO/LVIS. Nhiều nhất: {top}")


if __name__ == "__main__":
    main()
