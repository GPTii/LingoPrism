"""Fine-tune dataset v6: NEW photos for the weak classes, from COCO train2017 with LVIS + COCO boxes drawn by people.

Why v5 lost (AI/report/yolo/finetune_ft.md): its images came from the Open Images *train* split, which is exactly what
yolov8m-oiv7 was trained on – nothing new to learn – and the weak classes had 10x the images of the rest (300 vs 30),
so the model only moved its priors: a pen became a knife, a fork a spoon, scissors and toothbrush were never predicted.

v6 = the v5 builder run *balanced* (same number of Open Images images for every class: replay that keeps the base
model where it is) + this script, which adds photos the base model has never seen:
  * COCO train2017 images that are also in LVIS v1 train (the test set uses COCO *val*2017 and Open Images validation,
    and every test file is excluded again by id, so nothing leaks);
  * on every picked image the boxes of all LingoPrism labels: COCO's 80 classes (exhaustively labelled) + LVIS boxes of
    the labels COCO does not have (chopsticks, egg, pillow, lemon, peach, sandals, shoes, violin, guitar, taxi, pen…);
  * images are picked for the weak labels, at most --per-label each (seeded, reproducible);
  * labels are written in the base model's 601 Open Images classes (the first Open Images class of the label, as the
    server folds them), so the head is reused unchanged.

The annotation files (LVIS 1.1 GB, COCO 450 MB) are streamed from their zips with ijson: little memory.

    python AI/scripts/build_oiv7_finetune.py --out DS --per-class 80 --replay 80      # Open Images part, balanced
    python AI/scripts/build_lvis_finetune.py --out DS --per-label 250                 # + COCO/LVIS photos
    # quick local check (LVIS val + COCO val zips; never train on it):
    python AI/scripts/build_lvis_finetune.py --out ds_check --check --per-label 3

Writes into --out next to the Open Images part: images/{train,val}/coco_<id>.jpg, labels, and updates summary.json
("builder": 3, "lvis": {...}).
"""
import argparse
import hashlib
import heapq
import io
import json
import random
import sys
import urllib.request
import zipfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_oiv7_finetune import label_groups, weak_labels  # noqa: E402

URLS = {
    "lvis": "https://dl.fbaipublicfiles.com/LVIS/lvis_v1_train.json.zip",
    "coco": "http://images.cocodataset.org/annotations/annotations_trainval2017.zip",
    "lvis_val": "https://dl.fbaipublicfiles.com/LVIS/lvis_v1_val.json.zip",
}
COCO_MEMBER = {"train": "annotations/instances_train2017.json", "val": "annotations/instances_val2017.json"}

# LingoPrism label -> LVIS categories, checked by hand against the LVIS definitions. Only labels COCO does not have:
# COCO's own boxes are exhaustive, LVIS's are not (federated), so for a COCO class the COCO box is the one used.
# Left out on purpose: window / door / mango / tree / flower (no LVIS category of the same thing: "doorknob",
# "flower_arrangement" are other objects), flowerpot (a pot, not a potted plant).
LVIS_MAP = {
    "helmet": ["helmet"], "pig": ["hog"], "duck": ["duck"], "rabbit": ["rabbit"], "tiger": ["tiger"], "lion": ["lion"],
    "monkey": ["monkey"], "butterfly": ["butterfly"], "pen": ["pen"], "glasses": ["spectacles"], "hat": ["hat"],
    "watch": ["watch"], "chopsticks": ["chopstick"], "strawberry": ["strawberry"], "watermelon": ["watermelon"],
    "pineapple": ["pineapple"], "tomato": ["tomato"], "egg": ["egg"], "bread": ["bread"], "lamp": ["lamp"],
    "pillow": ["pillow"], "mushroom": ["mushroom"], "pumpkin": ["pumpkin"], "grape": ["grape"], "lemon": ["lemon"],
    "pear": ["pear"], "peach": ["peach"], "potato": ["potato"], "cucumber": ["cucumber"], "cookie": ["cookie"],
    "hamburger": ["hamburger"], "salad": ["salad"], "shrimp": ["prawn"], "fish": ["fish"], "goat": ["goat"],
    "deer": ["deer"], "owl": ["owl"], "penguin": ["penguin"], "panda": ["giant_panda"], "taxi": ["cab_(taxi)"],
    "helicopter": ["helicopter"], "flag": ["flag"], "shirt": ["shirt"], "skirt": ["skirt"], "dress": ["dress"],
    "coat": ["coat"], "jacket": ["jacket"], "scarf": ["scarf"], "belt": ["belt"], "desk": ["desk"],
    "drawer": ["drawer"], "curtain": ["curtain"], "mirror": ["mirror"], "towel": ["towel"], "plate": ["plate"],
    "kettle": ["kettle"], "candle": ["candle"], "fan": ["fan"], "box": ["box"], "balloon": ["balloon"],
    "doll": ["doll"], "ladder": ["ladder"], "calculator": ["calculator"], "camera": ["camera"], "printer": ["printer"],
    "guitar": ["guitar"], "piano": ["piano"], "violin": ["violin"], "pants": ["trousers"], "jeans": ["jean"],
    "shoes": ["shoe"], "boots": ["boot"], "sandals": ["sandal_(type_of_shoe)", "flip-flop_(sandal)"],
    "socks": ["sock"], "gloves": ["glove"], "bookshelf": ["bookcase"], "headphones": ["earphone"],
    "chicken": ["chicken_(animal)"], "crab": ["crab_(animal)"], "drum": ["drum_(musical_instrument)"],
}


def _download(url: str, dst: Path) -> Path:
    if not dst.exists():
        print(f"Tải {url} ...", flush=True)
        urllib.request.urlretrieve(url, dst.with_suffix(".part"))
        dst.with_suffix(".part").rename(dst)
    return dst


def _items(zip_path: Path, member: str | None, prefix: str):
    import ijson

    z = zipfile.ZipFile(zip_path)
    with z.open(member or z.namelist()[0]) as f:
        yield from ijson.items(f, prefix, use_float=True)


def _hash(seed: int, image_id: int) -> int:
    return -int(hashlib.blake2b(f"{seed}:coco:{image_id}".encode(), digest_size=8).hexdigest(), 16)


def _fetch(url: str, dst: Path, max_side: int) -> bool:
    from PIL import Image

    if dst.exists():
        return True
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            im = Image.open(io.BytesIO(resp.read())).convert("RGB")
        im.thumbnail((max_side, max_side))
        im.save(dst, quality=92)
        return True
    except Exception as e:  # a missing / broken image: skip it
        print(f"[bỏ qua ảnh] {url}: {e}", flush=True)
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="thư mục dataset (thường đã có phần Open Images)")
    ap.add_argument("--base", default="yolov8m-oiv7.pt")
    ap.add_argument("--per-label", type=int, default=250, help="số ảnh COCO/LVIS tối đa cho mỗi nhãn yếu")
    ap.add_argument("--threshold", type=float, default=0.55)
    ap.add_argument("--val", type=float, default=0.1)
    ap.add_argument("--max-side", type=int, default=640)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--work", default="", help="nơi để file zip nhãn (mặc định <out>/_work)")
    ap.add_argument("--check", action="store_true", help="thử nhanh trên LVIS val / COCO val2017 – không dùng để train")
    args = ap.parse_args()

    from ultralytics import YOLO

    out = Path(args.out)
    work = Path(args.work) if args.work else out / "_work"
    work.mkdir(parents=True, exist_ok=True)
    names = YOLO(args.base).names
    groups = label_groups(names)
    cls_of = {lab: idx[0] for lab, idx in groups.items()}  # the label's first Open Images class, as served
    weak = weak_labels(args.threshold, groups)
    split = "val" if args.check else "train"
    lvis_zip = _download(URLS["lvis_val" if args.check else "lvis"], work / ("lvis_v1_val.zip" if args.check else "lvis_v1_train.zip"))
    coco_zip = _download(URLS["coco"], work / "annotations_trainval2017.zip")

    # test images never come in, whatever split the annotations say
    test = json.loads((ROOT / "testset" / "annotations.json").read_text(encoding="utf-8"))["images"]
    test_ids = {int(im["file"].split("_")[1].split(".")[0]) for im in test if im["file"].startswith("coco_")}

    print("Lượt 1/4: danh mục lớp LVIS và COCO...", flush=True)
    lvis_name_to_label = {n: lab for lab, ns in LVIS_MAP.items() if lab in cls_of for n in ns}
    lvis_names = {c["id"]: c["name"] for c in _items(lvis_zip, None, "categories.item")}
    unknown = sorted(set(lvis_name_to_label) - set(lvis_names.values()))
    assert not unknown, f"LVIS_MAP có tên không có trong LVIS: {unknown}"
    lvis_cat = {i: lvis_name_to_label[n] for i, n in lvis_names.items() if n in lvis_name_to_label}
    coco_cat = {c["id"]: c["name"] for c in _items(coco_zip, COCO_MEMBER[split], "categories.item") if c["name"] in cls_of}
    lvis_labels, coco_labels = set(lvis_cat.values()) - set(coco_cat.values()), set(coco_cat.values())
    targets = [lab for lab in weak if lab in lvis_labels or lab in coco_labels]
    print(f"   LVIS: {len(lvis_cat)} lớp → {len(lvis_labels)} nhãn; COCO: {len(coco_labels)} nhãn; "
          f"nhãn yếu có ảnh mới: {', '.join(targets)}", flush=True)

    print("Lượt 2/4: ảnh LVIS...", flush=True)
    images = {}
    for im in _items(lvis_zip, None, "images.item"):
        if f"/{split}2017/" in im["coco_url"] and im["id"] not in test_ids:
            images[im["id"]] = (im["width"], im["height"], im["coco_url"])

    print("Lượt 3/4: box LVIS + COCO...", flush=True)
    boxes: dict[int, list] = defaultdict(list)
    for a in _items(lvis_zip, None, "annotations.item"):
        lab = lvis_cat.get(a["category_id"])
        if lab in lvis_labels and a["image_id"] in images:
            boxes[a["image_id"]].append((lab, a["bbox"]))
    for a in _items(coco_zip, COCO_MEMBER[split], "annotations.item"):
        lab = coco_cat.get(a["category_id"])
        if lab and a["image_id"] in images and not a.get("iscrowd"):
            boxes[a["image_id"]].append((lab, a["bbox"]))

    # a seeded random sample of up to --per-label images for every weak label
    heaps: dict[str, list] = {lab: [] for lab in targets}
    for image_id, bs in boxes.items():
        h = _hash(args.seed, image_id)
        for lab in {lab for lab, _ in bs if lab in heaps}:
            heap = heaps[lab]
            if len(heap) < args.per_label:
                heapq.heappush(heap, (h, image_id))
            elif h > heap[0][0]:
                heapq.heapreplace(heap, (h, image_id))
    picked = sorted({i for heap in heaps.values() for _, i in heap})
    random.Random(args.seed).shuffle(picked)
    n_val = int(len(picked) * args.val)
    part_of = {i: "val" if k < n_val else "train" for k, i in enumerate(picked)}
    for part in ("train", "val"):
        (out / "images" / part).mkdir(parents=True, exist_ok=True)
        (out / "labels" / part).mkdir(parents=True, exist_ok=True)

    print(f"Lượt 4/4: tải và thu nhỏ {len(picked)} ảnh COCO...", flush=True)
    with ThreadPoolExecutor(args.workers) as pool:
        futures = {i: pool.submit(_fetch, images[i][2], out / "images" / part_of[i] / f"coco_{i}.jpg", args.max_side)
                   for i in picked}
        ok = {}
        for k, (i, f) in enumerate(futures.items(), 1):
            ok[i] = f.result()
            if k % 500 == 0:
                print(f"   {k}/{len(picked)} ảnh", flush=True)

    kept, per_label = 0, defaultdict(lambda: {"images": 0, "boxes": 0})
    for i in picked:
        if not ok[i]:
            continue
        w, h, _ = images[i]
        lines = []
        for lab, (x, y, bw, bh) in boxes[i]:
            if bw <= 1 or bh <= 1:
                continue
            lines.append(f"{cls_of[lab]} {(x + bw / 2) / w:.6f} {(y + bh / 2) / h:.6f} {bw / w:.6f} {bh / h:.6f}")
            per_label[lab]["boxes"] += 1
        for lab in {lab for lab, _ in boxes[i]}:
            per_label[lab]["images"] += 1
        (out / "labels" / part_of[i] / f"coco_{i}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        kept += 1

    if not (out / "data.yaml").exists():  # this part alone (a local check)
        (out / "data.yaml").write_text(yaml.safe_dump(
            {"path": str(out.resolve()), "train": "images/train", "val": "images/val", "names": dict(names)},
            allow_unicode=True, sort_keys=False), encoding="utf-8")
    summary_file = out / "summary.json"
    summary = json.loads(summary_file.read_text(encoding="utf-8")) if summary_file.exists() else \
        {"base": args.base, "weak": weak, "replay": [lab for lab in groups if lab not in weak], "images": 0}
    summary["builder"] = 3
    summary["images_open_images"] = summary.get("images_open_images", summary["images"])
    summary["images"] = summary["images_open_images"] + kept
    summary["lvis"] = {"split": split, "per_label_quota": args.per_label, "images": kept, "targets": targets,
                       "per_label": {lab: per_label[lab] for lab in sorted(per_label, key=lambda l: -per_label[l]["images"])}}
    summary_file.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    weak_counts = ", ".join(f"{lab} {per_label[lab]['images']}" for lab in targets)
    print(f"→ {out}: +{kept} ảnh COCO/LVIS (ảnh mỗi nhãn yếu: {weak_counts}); tổng {summary['images']} ảnh")


if __name__ == "__main__":
    main()
