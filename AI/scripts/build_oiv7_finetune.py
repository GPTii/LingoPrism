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

    # Colab (needs ~20 GB disk the first time: FiftyOne downloads the Open Images train labels)
    python AI/scripts/build_oiv7_finetune.py --out /content/oiv7_ft --per-class 400 --replay 40
    # quick local check on the cached validation split (never train on it)
    python AI/scripts/build_oiv7_finetune.py --split validation --per-class 3 --replay 0 --limit-classes 3 --out ds_check

Output: YOLO format (images/{train,val}, labels/{train,val}), data.yaml with the base model's 601 names, summary.json
(labels chosen, images and boxes per LingoPrism label).
"""
import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_pretrained_oiv7 import EXTRA  # noqa: E402  (the same label -> Open Images classes folding as the server)

SERVER_SETUP = "oiv7m-int8+coco-m-int8+clip"
BATCH = 25  # replay classes per FiftyOne call
# mistaken for one another on the vocabulary photos (ghi_chu.md, CLIP section); these labels are "extra" classes the
# test set does not score, so they are added by hand
CONFUSED = ["lemon", "mango", "peach", "orange", "sandals", "shoes", "violin", "guitar", "scissors", "knife", "spoon",
            "taxi", "car"]


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


def _flag(det, field: str) -> bool:
    try:
        return bool(det[field])
    except (KeyError, AttributeError):
        return False


def load_samples(oi_classes: list[str], split: str, n: int, seed: int):
    """n images showing any of oi_classes. Every call re-reads the large Open Images label files, so the replay
    classes are asked for in batches, not one by one."""
    import fiftyone.zoo as foz

    name = f"lp-ft-{split}-{oi_classes[0]}-{len(oi_classes)}-{n}-{seed}".replace(" ", "_")
    ds = foz.load_zoo_dataset(
        "open-images-v7", split=split, label_types=["detections"], classes=oi_classes, max_samples=n, shuffle=True,
        seed=seed, only_matching=False,  # every box of the image, not only this class: fewer unlabeled objects
        dataset_name=name, drop_existing_dataset=True)
    return [(s.filepath, (s.ground_truth.detections if s.ground_truth else [])) for s in ds]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--base", default="yolov8m-oiv7.pt", help="model the head comes from (its 601 names)")
    ap.add_argument("--split", default="train", help="train (Colab). validation only for a quick local check")
    ap.add_argument("--per-class", type=int, default=400, help="ảnh mỗi lớp Open Images của lớp yếu")
    ap.add_argument("--replay", type=int, default=40, help="ảnh mỗi lớp Open Images của các lớp còn lại (chống quên)")
    ap.add_argument("--threshold", type=float, default=0.55, help="lớp yếu: AP50 trên tập test dưới ngưỡng này")
    ap.add_argument("--limit-classes", type=int, default=0, help="chỉ để thử nhanh")
    ap.add_argument("--val", type=float, default=0.1)
    ap.add_argument("--max-side", type=int, default=640)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()

    from PIL import Image
    from ultralytics import YOLO

    names = YOLO(args.base).names  # {0: "Accordion", ...} – the head we keep
    index = {n: i for i, n in names.items()}
    groups = label_groups(names)
    weak = weak_labels(args.threshold, groups)
    others = [lab for lab in groups if lab not in weak]
    if args.limit_classes:
        weak, others = weak[:args.limit_classes], others[:args.limit_classes]
    print(f"{len(weak)} lớp yếu: {', '.join(weak)}")
    print(f"{len(others)} lớp ôn lại (replay {args.replay} ảnh / lớp Open Images)")

    # weak classes one by one (each gets its share of images); replay classes in batches of BATCH
    weak_oi = list(dict.fromkeys(names[i] for lab in weak for i in groups[lab]))
    replay_oi = [c for c in dict.fromkeys(names[i] for lab in others for i in groups[lab]) if c not in weak_oi]
    plan = [([c], args.per_class) for c in weak_oi]
    if args.replay:
        plan += [(replay_oi[k:k + BATCH], args.replay * len(replay_oi[k:k + BATCH]))
                 for k in range(0, len(replay_oi), BATCH)]
    print(f"{len(plan)} lượt tải ({len(weak_oi)} lớp yếu, {len(replay_oi)} lớp ôn lại theo nhóm {BATCH})")

    images: dict[str, list] = {}
    for step, (oi_classes, n) in enumerate(plan, 1):
        print(f"[{step}/{len(plan)}] {', '.join(oi_classes[:3])}{'…' if len(oi_classes) > 3 else ''}", flush=True)
        try:
            for path, dets in load_samples(oi_classes, args.split, n, args.seed):
                images.setdefault(path, dets)
        except Exception as e:  # a class with no train boxes, a download hiccup: skip it, report it
            print(f"[bỏ qua] {oi_classes[0]}…: {e}")

    out = Path(args.out)
    rng = random.Random(args.seed)
    paths = sorted(images)
    rng.shuffle(paths)
    n_val = max(1, int(len(paths) * args.val)) if len(paths) > 1 else 0
    label_of = {i: lab for lab, idx in groups.items() for i in idx}
    kept, skipped_depiction, boxes_per_label, images_per_label = 0, 0, Counter(), defaultdict(set)
    for k, path in enumerate(paths):
        dets = images[path]
        if any(_flag(d, "IsDepiction") and index.get(d.label) in label_of for d in dets):
            skipped_depiction += 1  # a drawn cup must not teach what a cup looks like
            continue
        lines = []
        for d in dets:
            if d.label not in index:
                continue
            x, y, w, h = d.bounding_box  # relative, top-left
            cls = index[d.label]
            lines.append(f"{cls} {x + w / 2:.6f} {y + h / 2:.6f} {w:.6f} {h:.6f}")
            if cls in label_of:
                boxes_per_label[label_of[cls]] += 1
                images_per_label[label_of[cls]].add(path)
        part = "val" if k < n_val else "train"
        stem = Path(path).stem
        (out / "images" / part).mkdir(parents=True, exist_ok=True)
        (out / "labels" / part).mkdir(parents=True, exist_ok=True)
        with Image.open(path) as im:
            im = im.convert("RGB")
            im.thumbnail((args.max_side, args.max_side))
            im.save(out / "images" / part / f"{stem}.jpg", quality=92)
        (out / "labels" / part / f"{stem}.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        kept += 1

    (out / "data.yaml").write_text(yaml.safe_dump(
        {"path": str(out.resolve()), "train": "images/train", "val": "images/val", "names": dict(names)},
        allow_unicode=True, sort_keys=False), encoding="utf-8")
    summary = {"base": args.base, "split": args.split, "threshold": args.threshold, "weak": weak, "replay": others,
               "images": kept, "val_images": min(n_val, kept), "skipped_depiction": skipped_depiction,
               "per_label": {lab: {"images": len(images_per_label[lab]), "boxes": boxes_per_label[lab]}
                             for lab in weak + others}}
    (out / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"→ {out}: {kept} ảnh ({skipped_depiction} ảnh có tranh vẽ bị bỏ), data.yaml + summary.json")


if __name__ == "__main__":
    main()
