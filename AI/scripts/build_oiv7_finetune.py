"""Fine-tune dataset (v5) for the Open Images V7 model the server runs (yolov8m-oiv7), with human labels only.

Why the earlier attempts lost to the pretrained model (AI/report/yolo/ghi_chu.md):
  * v1–v3 trained a 78-class model from scratch / from COCO weights: too little data and GPU time;
  * v4 fine-tuned on a 78-class head with pseudo labels: the head lost the 601 Open Images classes and the machine-made
    labels pulled precision down (0.864 -> 0.694).
v5 keeps everything the pretrained model knows and only adds clean examples of what it gets wrong:
  * labels stay in the base model's own 601-class space (same names, same order) -> the detection head is reused as is;
  * Open Images boxes drawn by people only – no pseudo labels. "Group of" boxes (one box over a bunch of bananas, a row
    of windows) stay ordinary boxes, as in the data the base model was trained on – dropping those images would throw
    away most examples of exactly the weak classes; images with a drawing ("depiction") of a LingoPrism class are left
    out (the app sees real objects);
  * the *train* split only: the test set (AI/testset, build_testset.py) comes from the validation splits, so no leak;
  * weak classes get many images (AP50 of the server setup below --threshold on the test set, plus the pairs it confuses
    on real photos), every other LingoPrism class a few "replay" images so the model does not forget them.

Low memory on purpose: the Open Images box file of the train split has 14.6 million rows. FiftyOne loads it into memory
for every request and a free Colab (12 GB) was killed (exit -9) on the large classes, so the file is streamed twice
here – pass 1 picks the images (a seeded random sample per class, kept in small heaps), pass 2 collects every box of the
picked images – and the images are downloaded directly from the public Open Images bucket. A rerun skips the images
already downloaded.

    # Colab
    python AI/scripts/build_oiv7_finetune.py --out /content/oiv7_ft --per-class 300 --replay 30
    # quick local check on the cached validation split (never train on it)
    python AI/scripts/build_oiv7_finetune.py --split validation --per-class 3 --replay 1 --limit-classes 3 --out ds_check

Output: YOLO format (images/{train,val}, labels/{train,val}), data.yaml with the base model's 601 names, summary.json
(labels chosen, images and boxes per LingoPrism label).
"""

import argparse
import csv
import hashlib
import heapq
import json
import random
import sys
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_pretrained_oiv7 import EXTRA  # noqa: E402  (the same label -> Open Images classes folding as the server)

SERVER_SETUP = "oiv7m-int8+coco-m-int8+clip"
# mistaken for one another on the vocabulary photos (ghi_chu.md, CLIP section); these labels are "extra" classes the
# test set does not score, so they are added by hand
CONFUSED = [
    "lemon",
    "mango",
    "peach",
    "orange",
    "sandals",
    "shoes",
    "violin",
    "guitar",
    "scissors",
    "knife",
    "spoon",
    "taxi",
    "car",
]
CACHE = Path.home() / "fiftyone" / "open-images-v7"  # FiftyOne's copy of the label files, used when present
URLS = {
    "train": "https://storage.googleapis.com/openimages/v6/oidv6-train-annotations-bbox.csv",
    "validation": "https://storage.googleapis.com/openimages/v5/validation-annotations-bbox.csv",
    "classes": "https://storage.googleapis.com/openimages/v7/oidv7-class-descriptions-boxable.csv",
}
IMAGE_URL = "https://open-images-dataset.s3.amazonaws.com/{split}/{id}.jpg"


def label_groups(names: dict[int, str]) -> dict[str, list[int]]:
    """LingoPrism label -> indices of its Open Images classes in the base model (export_pretrained_oiv7.py)."""
    data = yaml.safe_load((ROOT / "classes.yaml").read_text(encoding="utf-8"))
    index = {n: i for i, n in names.items()}
    out = {}
    for c in data["classes"] + data.get("extra", []):
        oi = c.get("oi") or []
        wanted = (oi if isinstance(oi, list) else [oi]) + EXTRA.get(c["label"], [])
        idx = [index[n] for n in wanted if n in index]
        if idx:
            out[c["label"]] = idx
    return out


def weak_labels(threshold: float, groups: dict) -> list[str]:
    metrics = json.loads((ROOT / "report/yolo/testset/metrics.json").read_text(encoding="utf-8"))
    per_class = metrics["setups"][SERVER_SETUP]["per_class"]
    weak = [lab for lab, m in sorted(per_class.items(), key=lambda kv: kv[1]["map50"]) if m["map50"] < threshold]
    return [lab for lab in dict.fromkeys(weak + CONFUSED) if lab in groups]


def _file(cached: Path, url: str, work: Path) -> Path:
    if cached.exists():
        return cached
    dst = work / Path(url).name
    if not dst.exists():
        print(f"Tải {url} ...", flush=True)
        urllib.request.urlretrieve(url, dst.with_suffix(".part"))
        dst.with_suffix(".part").rename(dst)
    return dst


def _rows(path: Path):
    with open(path, newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


def pick_images(boxes_csv: Path, quotas: dict[str, int], seed: int) -> set[str]:
    """Pass 1: for every Open Images class id with a quota, the `quota` images with the smallest seeded hash – a
    reproducible random sample that never holds more than `quota` ids per class in memory."""
    heaps: dict[str, list] = {mid: [] for mid in quotas}
    last: dict[str, str] = {}  # the file is sorted by ImageID: one image's boxes of a class are consecutive rows
    for r in _rows(boxes_csv):
        mid, image = r["LabelName"], r["ImageID"]
        if mid not in heaps or last.get(mid) == image:
            continue
        last[mid] = image
        h = -int(hashlib.blake2b(f"{seed}:{image}".encode(), digest_size=8).hexdigest(), 16)  # max-heap of size quota
        heap = heaps[mid]
        if len(heap) < quotas[mid]:
            heapq.heappush(heap, (h, image))
        elif h > heap[0][0]:
            heapq.heapreplace(heap, (h, image))
    return {i for heap in heaps.values() for _, i in heap}


def collect_boxes(boxes_csv: Path, images: set[str]) -> dict[str, list]:
    """Pass 2: every box of the picked images: (class id, (xmin, xmax, ymin, ymax), is_depiction)."""
    out: dict[str, list] = defaultdict(list)
    for r in _rows(boxes_csv):
        if r["ImageID"] in images:
            out[r["ImageID"]].append(
                (r["LabelName"], tuple(float(r[k]) for k in ("XMin", "XMax", "YMin", "YMax")), r["IsDepiction"] == "1")
            )
    return out


def _fetch(split: str, image_id: str, dst: Path, max_side: int) -> bool:
    from PIL import Image

    if dst.exists():
        return True
    local = CACHE / split / "data" / f"{image_id}.jpg"
    try:
        if local.exists():
            im = Image.open(local)
        else:
            import io

            with urllib.request.urlopen(IMAGE_URL.format(split=split, id=image_id), timeout=30) as resp:
                im = Image.open(io.BytesIO(resp.read()))
        im = im.convert("RGB")
        im.thumbnail((max_side, max_side))
        im.save(dst, quality=92)
        return True
    except Exception as e:  # a missing / broken image: skip it
        print(f"[bỏ qua ảnh] {image_id}: {e}", flush=True)
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--base", default="yolov8m-oiv7.pt", help="model the head comes from (its 601 names)")
    ap.add_argument("--split", default="train", help="train (Colab). validation only for a quick local check")
    ap.add_argument("--per-class", type=int, default=300, help="ảnh mỗi lớp Open Images của lớp yếu")
    ap.add_argument("--replay", type=int, default=30, help="ảnh mỗi lớp Open Images của các lớp còn lại (chống quên)")
    ap.add_argument("--threshold", type=float, default=0.55, help="lớp yếu: AP50 trên tập test dưới ngưỡng này")
    ap.add_argument("--limit-classes", type=int, default=0, help="chỉ để thử nhanh")
    ap.add_argument("--val", type=float, default=0.1)
    ap.add_argument("--max-side", type=int, default=640)
    ap.add_argument("--workers", type=int, default=16, help="số ảnh tải song song")
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()

    from ultralytics import YOLO

    out = Path(args.out)
    work = out / "_work"
    work.mkdir(parents=True, exist_ok=True)
    names = YOLO(args.base).names  # {0: "Accordion", ...} – the head we keep
    index = {n: i for i, n in names.items()}
    groups = label_groups(names)
    weak = weak_labels(args.threshold, groups)
    others = [lab for lab in groups if lab not in weak]
    if args.limit_classes:
        weak, others = weak[: args.limit_classes], others[: args.limit_classes]
    print(f"{len(weak)} lớp yếu: {', '.join(weak)}")
    print(f"{len(others)} lớp ôn lại (replay {args.replay} ảnh / lớp Open Images)", flush=True)

    classes_csv = _file(CACHE / args.split / "metadata" / "classes.csv", URLS["classes"], work)
    mid_of = {row[1]: row[0] for row in csv.reader(open(classes_csv, encoding="utf-8")) if len(row) >= 2}
    name_of = {m: n for n, m in mid_of.items()}
    quotas: dict[str, int] = {}
    for labs, n in ((others, args.replay), (weak, args.per_class)):  # weak last: their larger quota wins
        for lab in labs:
            for i in groups[lab]:
                if names[i] in mid_of and n:
                    quotas[mid_of[names[i]]] = n
    boxes_csv = _file(CACHE / args.split / "labels" / "detections.csv", URLS[args.split], work)

    picked_file = work / "picked.json"
    if picked_file.exists():
        picked = json.loads(picked_file.read_text(encoding="utf-8"))
    else:
        print(f"Lượt 1/3: chọn ảnh cho {len(quotas)} lớp Open Images (đọc {boxes_csv.name} theo dòng)...", flush=True)
        ids = pick_images(boxes_csv, quotas, args.seed)
        print(f"Lượt 2/3: lấy mọi box của {len(ids)} ảnh...", flush=True)
        picked = collect_boxes(boxes_csv, ids)
        picked_file.write_text(json.dumps(picked), encoding="utf-8")

    paths = sorted(picked)
    random.Random(args.seed).shuffle(paths)
    n_val = max(1, int(len(paths) * args.val)) if len(paths) > 1 else 0
    label_of = {i: lab for lab, idx in groups.items() for i in idx}
    keep = [p for p in paths if not any(dep and index.get(name_of.get(m)) in label_of for m, _, dep in picked[p])]
    skipped_depiction = len(paths) - len(keep)  # a drawn cup must not teach what a cup looks like
    for part in ("train", "val"):
        (out / "images" / part).mkdir(parents=True, exist_ok=True)
        (out / "labels" / part).mkdir(parents=True, exist_ok=True)
    part_of = {p: "val" if k < n_val else "train" for k, p in enumerate(paths)}

    print(f"Lượt 3/3: tải và thu nhỏ {len(keep)} ảnh...", flush=True)
    done = 0
    with ThreadPoolExecutor(args.workers) as pool:
        futures = {
            p: pool.submit(_fetch, args.split, p, out / "images" / part_of[p] / f"{p}.jpg", args.max_side) for p in keep
        }
        ok = {}
        for k, (p, f) in enumerate(futures.items(), 1):
            ok[p] = f.result()
            done += ok[p]
            if k % 500 == 0:
                print(f"   {k}/{len(keep)} ảnh", flush=True)

    kept, boxes_per_label, images_per_label = 0, Counter(), defaultdict(set)
    for p in keep:
        if not ok.get(p):
            continue
        lines = []
        for m, (x0, x1, y0, y1), _ in picked[p]:
            cls = index.get(name_of.get(m))
            if cls is None:
                continue
            lines.append(f"{cls} {(x0 + x1) / 2:.6f} {(y0 + y1) / 2:.6f} {x1 - x0:.6f} {y1 - y0:.6f}")
            if cls in label_of:
                boxes_per_label[label_of[cls]] += 1
                images_per_label[label_of[cls]].add(p)
        (out / "labels" / part_of[p] / f"{p}.txt").write_text(
            "\n".join(lines) + ("\n" if lines else ""), encoding="utf-8"
        )
        kept += 1

    (out / "data.yaml").write_text(
        yaml.safe_dump(
            {"path": str(out.resolve()), "train": "images/train", "val": "images/val", "names": dict(names)},
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    summary = {
        "builder": 2,
        "base": args.base,
        "split": args.split,
        "threshold": args.threshold,
        "weak": weak,
        "replay": others,
        "images": kept,
        "val_images": sum(1 for p in keep if ok.get(p) and part_of[p] == "val"),
        "skipped_depiction": skipped_depiction,
        "per_label": {
            lab: {"images": len(images_per_label[lab]), "boxes": boxes_per_label[lab]} for lab in weak + others
        },
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"→ {out}: {kept} ảnh ({skipped_depiction} ảnh có tranh vẽ bị bỏ), data.yaml + summary.json")


if __name__ == "__main__":
    main()
