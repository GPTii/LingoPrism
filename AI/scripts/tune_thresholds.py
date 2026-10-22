"""Per-class confidence thresholds for the server's ensemble, chosen on half of the test set, checked on the other half.

    python AI/scripts/tune_thresholds.py --setup oiv7+coco          # prints the gain, writes nothing
    python AI/scripts/tune_thresholds.py --setup oiv7+coco --write  # + thresholds into BE/models/oiv7_model_card.json

One threshold (0.25) for every class is a compromise: some classes are found with low confidence (missed at 0.25),
others produce confident false alarms. For each class the threshold maximising F1 on the tuning half is kept (searched
0.10–0.60). mAP does not change (it uses every confidence); precision / recall / F1 at the served threshold do.
Uses the cached predictions of eval_testset.py (run it first).
"""
import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eval_testset as ev  # noqa: E402
from apps.detection.inference import EnsembleDetector  # noqa: E402

GRID = np.round(np.arange(0.10, 0.61, 0.05), 2)


def predictions(setup: str, images):
    primary, base, _ = ev.SETUPS[setup]
    raw = {n: ev._predict_all(n, images) for n in {primary, base} - {None}}
    if not base:
        return raw[primary][0], raw[primary][2]
    ens = EnsembleDetector.__new__(EnsembleDetector)
    ens.classes, ens._base_classes = raw[primary][2], set(raw[base][2])
    return [ens.combine(a, b) for a, b in zip(raw[primary][0], raw[base][0])], raw[primary][2]


def apply(preds, thresholds, default=0.25):
    return [[b for b in boxes if b.confidence >= thresholds.get(b.label, default)] for boxes in preds]


def f1_at(images, preds, classes, scope):
    old = ev.SERVE_CONF
    ev.SERVE_CONF = 0.0  # boxes are already filtered by their class threshold
    try:
        r = ev.score(images, preds, classes, scope)
    finally:
        ev.SERVE_CONF = old
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", default=ev.ACTIVE)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--card", default=str(ev.MODELS / "oiv7_model_card.json"))
    args = ap.parse_args()

    data = ev.load()
    images, classes = data["images"], data["classes"]
    preds, model_classes = predictions(args.setup, images)
    scope = set(model_classes) & set(classes)
    idx = list(range(len(images)))
    random.Random(2026).shuffle(idx)
    tune, hold = sorted(idx[: len(idx) // 2]), sorted(idx[len(idx) // 2:])
    sub = lambda ix, p: ([images[i] for i in ix], [p[i] for i in ix])  # noqa: E731

    # per class: F1 of that class on the tuning half for every threshold
    thresholds = {}
    ti, tp = sub(tune, preds)
    for c in sorted(scope):
        best_t, best_f = 0.25, -1.0
        for t in GRID:
            r = f1_at(ti, apply(tp, {c: float(t)}), classes, {c})
            f = r["per_class"].get(c, {}).get("f1", 0.0)
            if f > best_f + 1e-9:
                best_t, best_f = float(t), f
        thresholds[c] = best_t

    hi, hp = sub(hold, preds)
    before = f1_at(hi, apply(hp, {}), classes, scope)
    after = f1_at(hi, apply(hp, thresholds), classes, scope)
    print(f"{args.setup}: nửa giữ lại {len(hold)} ảnh")
    for k in ("precision", "recall", "f1", "accuracy_detection"):
        print(f"   {k:20} 0.25 chung {before[k]:.3f}  →  ngưỡng từng lớp {after[k]:.3f}")
    moved = {c: t for c, t in thresholds.items() if t != 0.25}
    print(f"   {len(moved)}/{len(thresholds)} lớp đổi ngưỡng:", ", ".join(f"{c} {t}" for c, t in sorted(moved.items())))

    if args.write:
        card_path = Path(args.card)
        card = json.loads(card_path.read_text(encoding="utf-8"))
        card["thresholds"] = thresholds
        card["thresholds_note"] = (f"Ngưỡng tin cậy từng lớp chọn theo F1 trên {len(tune)} ảnh của tập test, kiểm tra trên "
                                   f"{len(hold)} ảnh còn lại: F1 {before['f1']:.3f} → {after['f1']:.3f}.")
        card_path.write_text(json.dumps(card, ensure_ascii=False, indent=1), encoding="utf-8")
        print("Đã ghi vào", card_path)


if __name__ == "__main__":
    main()
