"""Score every detector setup on the labelled test set (AI/testset, built by build_testset.py) through the server's
own inference code: confusion matrix, accuracy, precision / recall / F1, AP per class, mAP50, mAP50-95.

    python AI/scripts/eval_testset.py              # prints the table, writes AI/report/yolo/testset/ (+ the model card)
    python AI/scripts/eval_testset.py --model v4=BE/models/lingoprism-yolov8s-ft.onnx   # + a new model, alone and with COCO
    python AI/scripts/eval_testset.py --base coco-s=AI/runs/coco/yolov10s.onnx         # + another COCO partner
    A setup whose name ends in "+clip" also runs the CLIP re-check of the server (inference.LabelVerifier).
    (notebook 07 imports this module and draws the figures)

Definitions (IoU = overlap of a predicted and a true box):
  * precision / recall / F1      at the server's confidence threshold 0.25, a prediction is correct when IoU >= 0.5
                                 with a true box of the same class (each true box matched once);
  * mAP50 / mAP50-95             mean over classes of the area under the precision-recall curve (COCO 101-point),
                                 predictions down to confidence 0.01, IoU 0.5 / averaged over 0.5:0.95;
  * accuracy (nhãn)              of the true objects the model located (IoU >= 0.45 with any prediction), the share
                                 given the right label: "when it finds the object, does it name it right?";
  * accuracy (phát hiện)         TP / (TP + FP + FN) at 0.25: every mistake (wrong label, false alarm, miss) counts;
  * confusion matrix             Ultralytics layout matrix[predicted][true], last row / column = background
                                 (a true object nothing matched / a prediction on no true object).
Predictions of a class the image's source did not label are ignored (see build_testset.py).
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "BE"))
from apps.detection import inference  # noqa: E402
from apps.detection.inference import Box, Detector, EnsembleDetector, _iou  # noqa: E402

TESTSET = ROOT / "AI" / "testset"
CACHE = TESTSET / "predictions"
REPORT = ROOT / "AI" / "report" / "yolo" / "testset"
MODELS = ROOT / "BE" / "models"
LOW_CONF = 0.01  # predictions kept for the precision-recall curves (mAP)
SERVE_CONF = 0.25  # the server's threshold (inference.CONF_THRESHOLD)
IOU_TP = 0.5
IOU_CONFUSION = 0.45
IOU_RANGE = np.arange(0.5, 0.96, 0.05)

BASE = {"v1": "lingoprism-yolov10n.onnx", "coco": "yolov10n.onnx", "oiv7": "yolov8s-oiv7-lingoprism.onnx",
        "oiv7-78": "yolov8s-oiv7-78.onnx", "oiv7m": "yolov8m-oiv7-lingoprism.onnx", "coco-m": "yolov10m.onnx",
        "oiv7m-int8": "yolov8m-oiv7-lingoprism-int8.onnx", "coco-m-int8": "yolov10m-int8.onnx"}
CLIP = MODELS / "clip-mobileclip2-s2.onnx"
SETUPS = {  # name -> (primary, base or None, title)
    "v1": ("v1", None, "v1 tự train"),
    "coco": ("coco", None, "COCO yolov10n"),
    "v1+coco": ("v1", "coco", "v1 + COCO"),
    # history of the served setup: 78 folded classes (a bouquet came out as broccoli) -> 232 -> medium models
    "oiv7-78+coco": ("oiv7-78", "coco", "OIV7 s 78 lớp + COCO n (cũ)"),
    "oiv7": ("oiv7", None, "OIV7 yolov8s"),
    "oiv7+coco": ("oiv7", "coco", "OIV7 s + COCO n (cũ)"),
    "coco-m": ("coco-m", None, "COCO yolov10m"),
    "oiv7m": ("oiv7m", None, "OIV7 yolov8m"),
    "oiv7m+coco-m": ("oiv7m", "coco-m", "OIV7 m + COCO m"),
    "oiv7m+coco-m+clip": ("oiv7m", "coco-m", "OIV7 m + COCO m + CLIP"),
    "oiv7m-int8+coco-m-int8": ("oiv7m-int8", "coco-m-int8", "OIV7 m + COCO m, INT8"),
    "oiv7m-int8+coco-m-int8+clip": ("oiv7m-int8", "coco-m-int8", "OIV7 m + COCO m, INT8 + CLIP (đang dùng)"),
}
ACTIVE = "oiv7m-int8+coco-m-int8+clip"


def load():
    return json.loads((TESTSET / "annotations.json").read_text(encoding="utf-8"))


def add_model(name: str, onnx: str):
    """Score another model too (e.g. the one trained on Colab), alone and combined with COCO."""
    BASE[name] = str(Path(onnx).resolve())
    SETUPS[name] = (name, None, name)
    SETUPS[f"{name}+coco"] = (name, "coco", f"{name} + COCO")


def add_base(name: str, onnx: str):
    """Another COCO model as the ensemble partner (e.g. yolov10s): alone and with every Open Images model."""
    BASE[name] = str(Path(onnx).resolve())
    SETUPS[name] = (name, None, name)
    for primary in [p for p, b, _ in list(SETUPS.values()) if b == "coco"]:
        SETUPS[f"{primary}+{name}"] = (primary, name, f"{SETUPS[primary][2] if primary in SETUPS else primary} + {name}")


def _predict_all(name: str, images: list) -> list:
    """Raw boxes of one model on every test image, cached in AI/testset/predictions/<name>.json."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}.json"
    file = MODELS / BASE[name]  # an absolute path stays as it is
    det = Detector(str(file))
    stamp = f"{file.stat().st_mtime_ns}-{len(images)}-{LOW_CONF}"
    if path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        if cached.get("stamp") == stamp:
            return [[Box(**b) for b in boxes] for boxes in cached["boxes"]], cached["ms"], det.classes
    old = inference.CONF_THRESHOLD
    inference.CONF_THRESHOLD = LOW_CONF
    try:
        out, ms = [], []
        for i, im in enumerate(images):
            with Image.open(TESTSET / "images" / im["file"]) as img:
                boxes, t = det.predict(img)
            out.append(boxes)
            ms.append(t)
            if (i + 1) % 500 == 0:
                print(f"   {name}: {i + 1}/{len(images)}")
    finally:
        inference.CONF_THRESHOLD = old
    path.write_text(json.dumps({"stamp": stamp, "ms": ms, "boxes": [[b.__dict__ for b in boxes] for boxes in out]}),
                    encoding="utf-8")
    return out, ms, det.classes


def _clip_check(setup: str, images: list, preds: list) -> tuple[list, list]:
    """The server's CLIP re-check on the boxes it would show (confidence >= 0.25), cached like _predict_all."""
    verifier = inference.LabelVerifier(str(CLIP))
    path = CACHE / f"clip-{setup.replace('+', '_')}.json"
    stamp = (f"{CLIP.stat().st_mtime_ns}-{len(images)}-{inference.CLIP_MAX_CONF}-{inference.CLIP_MIN_AREA}-"
             f"{inference.CLIP_SURE}-{inference.CLIP_DOUBT}-{sum(len(p) for p in preds)}")
    if path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        if cached.get("stamp") == stamp:
            return [[Box(**b) for b in boxes] for boxes in cached["boxes"]], cached["ms"]
    out, ms = [], []
    for im, boxes in zip(images, preds):
        with Image.open(TESTSET / "images" / im["file"]) as img:
            checked, t = verifier.check(img, boxes)
        out.append(checked)
        ms.append(t)
    path.write_text(json.dumps({"stamp": stamp, "ms": ms, "boxes": [[b.__dict__ for b in boxes] for boxes in out]}),
                    encoding="utf-8")
    return out, ms


def _ap(tp: np.ndarray, conf: np.ndarray, n_gt: int) -> float:
    """Area under the precision-recall curve, COCO 101-point interpolation."""
    if n_gt == 0 or len(tp) == 0:
        return 0.0
    order = np.argsort(-conf)
    tpc = np.cumsum(tp[order])
    fpc = np.cumsum(1 - tp[order])
    recall = tpc / n_gt
    precision = tpc / (tpc + fpc)
    mpre = np.concatenate(([1.0], precision, [0.0]))
    mrec = np.concatenate(([0.0], recall, [1.0]))
    mpre = np.flip(np.maximum.accumulate(np.flip(mpre)))
    x = np.linspace(0, 1, 101)
    return float(np.trapezoid(np.interp(x, mrec, mpre), x)) if hasattr(np, "trapezoid") else float(np.trapz(np.interp(x, mrec, mpre), x))


def _match(preds: list, gts: list, iou_thr: float) -> np.ndarray:
    """For predictions sorted by confidence: 1 if it matches a not yet matched true box of the same class."""
    used = [False] * len(gts)
    tp = np.zeros(len(preds))
    for i, p in enumerate(preds):
        best, best_j = iou_thr, -1
        for j, g in enumerate(gts):
            if used[j] or g["label"] != p.label:
                continue
            v = _iou(p.bbox, g["bbox"])
            if v >= best:
                best, best_j = v, j
        if best_j >= 0:
            used[best_j] = True
            tp[i] = 1
    return tp


def score(images: list, preds: list, classes: list, scope: set) -> dict:
    """Every metric for one setup; `scope` = the classes this setup is asked about."""
    labels = list(classes)
    idx = {c: i for i, c in enumerate(labels)}
    bg = len(labels)
    cm = np.zeros((bg + 1, bg + 1), dtype=int)
    per_class = {c: {"tp": [[] for _ in IOU_RANGE], "conf": [], "n_gt": 0, "conf_ok": []} for c in labels}
    tp25 = fp25 = fn25 = 0
    located = located_ok = 0
    curve = {"conf": [], "tp": []}  # micro precision-recall / F1 curves (IoU 0.5)
    n_gt_all = 0
    for im, boxes in zip(images, preds):
        ev = set(im["evaluable"]) & scope
        gts = [g for g in im["boxes"] if g["label"] in ev]
        ps = sorted((b for b in boxes if b.label in ev), key=lambda b: -b.confidence)
        n_gt_all += len(gts)
        for g in gts:
            per_class[g["label"]]["n_gt"] += 1
        for k, thr in enumerate(IOU_RANGE):
            tp = _match(ps, gts, thr)
            for p, t in zip(ps, tp):
                per_class[p.label]["tp"][k].append(t)
                if k == 0:
                    per_class[p.label]["conf"].append(p.confidence)
                    curve["conf"].append(p.confidence)
                    curve["tp"].append(t)
                    if t:
                        per_class[p.label]["conf_ok"].append(p.confidence)
        # at the server's threshold
        served = [p for p in ps if p.confidence >= SERVE_CONF]
        tp = _match(served, gts, IOU_TP)
        tp25 += int(tp.sum())
        fp25 += int(len(served) - tp.sum())
        fn25 += int(len(gts) - tp.sum())
        # confusion matrix: one-to-one, highest IoU first, any class
        pairs = sorted(((_iou(p.bbox, g["bbox"]), i, j) for i, p in enumerate(served) for j, g in enumerate(gts)),
                       reverse=True)
        mp, mg = set(), set()
        for v, i, j in pairs:
            if v < IOU_CONFUSION:
                break
            if i in mp or j in mg:
                continue
            mp.add(i)
            mg.add(j)
            cm[idx[served[i].label], idx[gts[j]["label"]]] += 1
            located += 1
            located_ok += served[i].label == gts[j]["label"]
        for j, g in enumerate(gts):
            if j not in mg:
                cm[bg, idx[g["label"]]] += 1
        for i, p in enumerate(served):
            if i not in mp:
                cm[idx[p.label], bg] += 1
    rows = {}
    for c, d in per_class.items():
        if d["n_gt"] == 0:
            continue
        conf = np.array(d["conf"])
        aps = [_ap(np.array(t), conf, d["n_gt"]) for t in d["tp"]]
        tp_at = np.array(d["tp"][0])
        served_mask = conf >= SERVE_CONF if len(conf) else np.array([], dtype=bool)
        tp_s = float(tp_at[served_mask].sum()) if len(conf) else 0.0
        n_s = int(served_mask.sum()) if len(conf) else 0
        p = tp_s / n_s if n_s else 0.0
        r = tp_s / d["n_gt"]
        rows[c] = {"n_gt": d["n_gt"], "precision": round(p, 4), "recall": round(r, 4),
                   "f1": round(2 * p * r / (p + r), 4) if p + r else 0.0,
                   "map50": round(aps[0], 4), "map50_95": round(float(np.mean(aps)), 4)}
    conf = np.array(curve["conf"])
    tpv = np.array(curve["tp"])
    thresholds = np.linspace(0, 1, 101)
    pr_curve = []
    for t in thresholds:
        m = conf >= t
        n, k = int(m.sum()), float(tpv[m].sum())
        p = k / n if n else 1.0
        r = k / n_gt_all if n_gt_all else 0.0
        pr_curve.append({"conf": round(float(t), 2), "precision": round(p, 4), "recall": round(r, 4),
                         "f1": round(2 * p * r / (p + r), 4) if p + r else 0.0})
    p = tp25 / (tp25 + fp25) if tp25 + fp25 else 0.0
    r = tp25 / (tp25 + fn25) if tp25 + fn25 else 0.0
    hist_bins = [round(x, 1) for x in np.linspace(0, 1, 11)]
    return {
        "images": len(images), "objects": n_gt_all, "classes": len(rows),
        "precision": round(p, 4), "recall": round(r, 4), "f1": round(2 * p * r / (p + r), 4) if p + r else 0.0,
        "map50": round(float(np.mean([v["map50"] for v in rows.values()])), 4) if rows else 0.0,
        "map50_95": round(float(np.mean([v["map50_95"] for v in rows.values()])), 4) if rows else 0.0,
        "accuracy_label": round(located_ok / located, 4) if located else 0.0,
        "accuracy_detection": round(tp25 / (tp25 + fp25 + fn25), 4) if tp25 + fp25 + fn25 else 0.0,
        "tp": tp25, "fp": fp25, "fn": fn25,
        "per_class": rows, "curve": pr_curve,
        "confusion_matrix": {"labels": labels + ["background"], "matrix": cm.tolist()},
        "confidence": {"bins": hist_bins, "per_class": {
            c: np.histogram(d["conf_ok"], bins=hist_bins)[0].tolist() for c, d in per_class.items() if d["conf_ok"]}},
    }


def evaluate(setups=tuple(SETUPS)) -> dict:
    data = load()
    images, classes = data["images"], data["classes"]
    raw, ms, model_classes = {}, {}, {}
    for name in {SETUPS[s][0] for s in setups} | {SETUPS[s][1] for s in setups if SETUPS[s][1]}:
        t0 = time.time()
        raw[name], ms[name], model_classes[name] = _predict_all(name, images)
        print(f"   {name}: {len(images)} ảnh, {time.time() - t0:.0f}s")
    coco_scope = {c for c in classes if c in set(model_classes["coco"])} if "coco" in model_classes else set()
    out = {"testset": {"images": len(images), "coco": sum(i["source"] == "coco" for i in images),
                       "oi": sum(i["source"] == "oi" for i in images),
                       "objects": sum(len(i["boxes"]) for i in images)},
           "setups": {}, "coco_classes": sorted(coco_scope)}
    for s in setups:
        primary, base, title = SETUPS[s]
        if base:
            ens = EnsembleDetector.__new__(EnsembleDetector)
            ens.classes, ens._base_classes = model_classes[primary], set(model_classes[base])
            preds = [ens.combine(a, b) for a, b in zip(raw[primary], raw[base])]
            t = [a + b for a, b in zip(ms[primary], ms[base])]
        else:
            preds, t = raw[primary], ms[primary]
        if s.endswith("+clip"):
            preds, t_clip = _clip_check(s, images, preds)
            t = [a + b for a, b in zip(t, t_clip)]
        scope = coco_scope if s == "coco" else set(model_classes[primary])
        res = score(images, preds, classes, scope & set(classes))
        res["title"] = title
        res["ms_per_image"] = round(float(np.mean(t)), 1)
        # the same setup on the COCO classes only / on the others: fair comparison with COCO alone
        if s != "coco" and coco_scope:
            sub = lambda sc: {k: v for k, v in score(images, preds, classes, sc).items() if not isinstance(v, (dict, list))}  # noqa: E731
            res["on_coco_classes"] = sub(scope & coco_scope)
            res["on_other_classes"] = sub(scope - coco_scope)
        out["setups"][s] = res
        print(f"   {title:26} P {res['precision']:.3f}  R {res['recall']:.3f}  F1 {res['f1']:.3f}  "
              f"mAP50 {res['map50']:.3f}  mAP50-95 {res['map50_95']:.3f}  acc(nhãn) {res['accuracy_label']:.3f}")
    return out


def save(results: dict) -> Path:
    """AI/report/yolo/testset/metrics.json + confusion matrices; the active model's run folder gets the same files as a
    trained run (report/metrics.json, confusion_matrix.json, confidence.json) so notebooks 3 (VIP) and 7 use them."""
    REPORT.mkdir(parents=True, exist_ok=True)
    slim = {**results, "setups": {k: {kk: vv for kk, vv in v.items() if kk not in ("confusion_matrix", "confidence")}
                                  for k, v in results["setups"].items()}}
    (REPORT / "metrics.json").write_text(json.dumps(slim, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in results["setups"].items():
        (REPORT / f"confusion_matrix_{k.replace('+', '_')}.json").write_text(json.dumps(v["confusion_matrix"]), encoding="utf-8")
    a = results["setups"].get(ACTIVE)
    if a:
        run = ROOT / "AI" / "runs" / "oiv7-pretrained"
        (run / "report").mkdir(parents=True, exist_ok=True)
        (run / "report" / "confusion_matrix.json").write_text(json.dumps(a["confusion_matrix"]), encoding="utf-8")
        (run / "report" / "confidence.json").write_text(json.dumps(a["confidence"]), encoding="utf-8")
        (run / "report" / "metrics.json").write_text(json.dumps({"per_class": a["per_class"]}, ensure_ascii=False),
                                                     encoding="utf-8")
        card_path = run / "model_card.json"
        card = json.loads(card_path.read_text(encoding="utf-8"))
        card["metrics"] = {k: a[k] for k in ("precision", "recall", "map50", "map50_95")}
        card["metrics_note"] = (f"Đo cho cách server chạy ({a['title'].replace(' (đang dùng)', '')}) trên tập test {results['testset']['images']} ảnh "
                                f"(COCO-2017 val + Open Images V7 val, không model nào train trên đó), "
                                f"{time.strftime('%d/%m/%Y')}: P/R ở ngưỡng 0,25, IoU 0,5.")
        card_path.write_text(json.dumps(card, ensure_ascii=False, indent=1), encoding="utf-8")
    return REPORT


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--model", action="append", default=[], help="tên=đường_dẫn.onnx – chấm thêm model này")
    ap.add_argument("--base", action="append", default=[], help="tên=đường_dẫn.onnx – thử model COCO khác để ghép")
    args = ap.parse_args()
    for spec in args.model:
        add_model(*spec.split("=", 1))
    for spec in args.base:
        add_base(*spec.split("=", 1))
    res = evaluate(tuple(SETUPS))
    print("Đã lưu", save(res))
