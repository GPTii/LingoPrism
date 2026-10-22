"""Training reports of the YOLOv10 models, kept for the thesis (admin → Thuật toán AI → Model YOLO).

For every training run folder (AI/runs/<name>/, the zip downloaded from the Colab notebook):
  * model_card.json / report/metrics.json – precision, recall, mAP50, mAP50-95, per-class AP;
  * results.csv – the curves per epoch (losses, precision, recall, mAP);
  * the plots written by Ultralytics (results.png, confusion matrix, PR/F1 curves, validation predictions),
    copied to MEDIA_ROOT/model_reports/<name>/ so the admin page can show them.
Plus a comparison on real photos (the reviewed photo of every word, never used in training, and AI/eval_photos/):
each model vs the pretrained COCO model vs both combined (detection.inference.EnsembleDetector). A pretrained model
has no labelled test split: the precision / recall measured on the photos are written to its ModelVersion.
"""
import csv
import json
import re
import shutil
import time
from pathlib import Path

from django.conf import settings
from PIL import Image

from apps.vocab.models import Word

from .models import ExperimentRun

RUNS = settings.BASE_DIR.parent / "AI" / "runs"
PLOTS = ["results.png", "test/confusion_matrix_normalized.png", "test/confusion_matrix.png", "test/BoxPR_curve.png",
         "test/BoxF1_curve.png", "test/BoxP_curve.png", "test/BoxR_curve.png", "test/val_batch0_pred.jpg",
         "test/val_batch0_labels.jpg", "test/val_batch1_pred.jpg", "test/val_batch2_pred.jpg"]


def _curves(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        rows = [{k.strip(): v for k, v in r.items()} for r in csv.DictReader(fh)]
    pick = {"epoch": "epoch", "map50": "metrics/mAP50(B)", "map50_95": "metrics/mAP50-95(B)",
            "precision": "metrics/precision(B)", "recall": "metrics/recall(B)", "train_box_loss": "train/box_loss",
            "train_cls_loss": "train/cls_loss", "val_box_loss": "val/box_loss", "val_cls_loss": "val/cls_loss"}
    return {k: [float(r[c]) for r in rows if r.get(c)] for k, c in pick.items()}


def import_run(folder: Path) -> dict:
    card = json.loads((folder / "model_card.json").read_text(encoding="utf-8"))
    name = card["name"]
    metrics = json.loads((folder / "report" / "metrics.json").read_text(encoding="utf-8")) if (folder / "report" / "metrics.json").exists() else {}
    args = {}
    if (folder / "args.yaml").exists():
        for line in (folder / "args.yaml").read_text(encoding="utf-8").splitlines():
            k, _, v = line.partition(":")
            if k in ("epochs", "imgsz", "batch", "model", "optimizer", "lr0", "patience"):
                args[k] = v.strip()
    out_dir = Path(settings.MEDIA_ROOT) / "model_reports" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    plots = []
    for rel in PLOTS:
        src = folder / rel
        if src.exists():
            shutil.copy2(src, out_dir / src.name)
            plots.append(f"{settings.MEDIA_URL}model_reports/{name}/{src.name}")
    per_class = metrics.get("per_class", {})
    return {
        "name": name, "base_model": card.get("base_model"), "classes": len(card.get("classes", [])),
        "train_args": args, "metrics": card.get("metrics", {}), "tflite": bool(card.get("tflite")),
        "per_class": [{"label": k, **(v if isinstance(v, dict) else {"map50": v})} for k, v in per_class.items()],
        "curves": _curves(folder / "results.csv") if (folder / "results.csv").exists() else {},
        "plots": plots,
    }


EVAL_DIR = settings.BASE_DIR.parent / "AI" / "eval_photos"  # learners' own photos, named after what they show
PHOTO_EXT = (".jpg", ".jpeg", ".png", ".webp")


def _aliases() -> dict:
    """'cup', 'potted-plant', 'potted plant', a word slug -> the YOLO label (for the names of the own photos)."""
    out = {}
    for slug, label in Word.objects.exclude(yolo_label="").values_list("slug", "yolo_label"):
        for key in (slug, label):
            out[key.lower().replace(" ", "-")] = label
    return out


def _expected(path: Path, aliases: dict) -> set:
    """cup.jpg, cup_2.jpg, cup+spoon+bowl.jpg, pillow/IMG_001.jpg -> the labels in the photo."""
    for name in (path.stem, path.parent.name):
        parts = [re.sub(r"_[A-Za-z0-9]{7}$|[_ ]\d+$", "", p).lower().replace(" ", "-") for p in name.split("+")]
        found = {aliases[p] for p in parts if p in aliases}
        if found:
            return found
    return set()


def photo_sets(classes) -> dict:
    """word_photos: the reviewed photo of every word with a YOLO class (one object, Wikimedia Commons, never trained on);
    own_photos: AI/eval_photos/ (real photos taken for the evaluation, several objects allowed)."""
    folder = settings.BASE_DIR / "seed" / "images"
    known = set(classes)
    words = [(folder / f"{slug}.jpg", {label}) for slug, label in
             Word.objects.exclude(yolo_label="").order_by("slug").values_list("slug", "yolo_label")
             if label in known and (folder / f"{slug}.jpg").exists()]
    own = []
    if EVAL_DIR.exists():
        aliases = _aliases()
        for p in sorted(EVAL_DIR.rglob("*")):
            if p.suffix.lower() in PHOTO_EXT and (exp := _expected(p, aliases) & known):
                own.append((p, exp))
    return {"word_photos": words, "own_photos": own}


def _score(det, photos, coco_classes) -> tuple[dict, list]:
    """top1: best box is an expected object; found: share of the expected objects found; precision: share of the boxes
    whose label is in the photo (another real object in the background counts as wrong: a lower bound)."""
    n = top1 = found = total = boxes_ok = boxes_all = top1_new = n_new = 0
    ms, per_photo = [], []
    for path, exp in photos:
        with Image.open(path) as im:
            boxes, t = det.predict(im.convert("RGB"))
        ms.append(t)
        got = {b.label for b in boxes}
        n += 1
        hit = bool(boxes) and boxes[0].label in exp
        top1 += hit
        found += len(exp & got)
        total += len(exp)
        boxes_ok += sum(b.label in exp for b in boxes)
        boxes_all += len(boxes)
        if not exp <= coco_classes:
            n_new += 1
            top1_new += hit
        per_photo.append({"photo": path.name, "expected": sorted(exp), "top1_ok": hit,
                          "boxes": [{"label": b.label, "confidence": round(b.confidence, 4),
                                     "bbox": [round(v, 4) for v in b.bbox]} for b in boxes[:8]]})

    def r(a, b):
        return round(a / b, 4) if b else None

    return ({"photos": n, "top1": r(top1, n), "found": r(found, total), "precision": r(boxes_ok, boxes_all),
             "wrong_boxes": boxes_all - boxes_ok, "top1_new_classes": r(top1_new, n_new), "new_class_photos": n_new,
             "ms_per_image": round(sum(ms) / len(ms), 1) if ms else None}, per_photo)


def compare_on_photos() -> dict:
    """Each model alone, the pretrained COCO model alone, and both combined (what the server runs), on the photo sets."""
    from apps.detection.inference import Detector, EnsembleDetector, with_verifier
    from apps.detection.models import ModelVersion

    base_path = getattr(settings, "YOLO_BASE_MODEL_PATH", "")
    coco = Detector(base_path) if base_path and Path(base_path).exists() else None
    coco_classes = set(coco.classes) if coco else set()
    out, details = [], {}
    for mv in ModelVersion.objects.order_by("created_at"):
        if not Path(mv.file).exists() or (coco and Path(mv.file).resolve() == Path(base_path).resolve()):
            continue
        trained = Detector(mv.file, mv.classes, mv.input_size)
        trained.name = mv.name
        candidates = [("trained", trained)]
        if coco:
            # combined = what the server runs: both models, then the CLIP re-check (when its model is there)
            candidates += [("coco", coco), ("combined", with_verifier(EnsembleDetector(trained, coco)))]
        sets = photo_sets(mv.classes)
        results = {name: {} for name in sets}
        for key, det in candidates:
            for name, photos in sets.items():
                if key == "coco":  # COCO alone is only asked about the classes it knows
                    photos = [(p, e) for p, e in photos if e <= coco_classes]
                if not photos:
                    continue
                results[name][key], per_photo = _score(det, photos, coco_classes)
                if mv.is_active and key == ("combined" if coco else "trained"):
                    details[name] = per_photo
        out.append({"model": mv.name, "map50": mv.map50, "active": mv.is_active,
                    "results": results["word_photos"], "own_photos": results["own_photos"]})
    return {"models": out, "active_per_photo": details,
            "note": "Ảnh từ vựng: mỗi từ một ảnh thật đã duyệt (Wikimedia Commons), không nằm trong dữ liệu train. "
                    "Ảnh tự chụp: AI/eval_photos/ (tên file = vật trong ảnh). 'combined' = cả hai model cùng chạy, "
                    "mỗi vật giữ nhãn tự tin nhất (cách server đang chạy). precision = box có nhãn đúng / mọi box."}


def apply_metrics(comparison: dict) -> dict | None:
    """Pretrained model (no labelled test split, map50 empty): its precision / recall in the admin are the ones
    measured on the photos, for the setup the server runs. A trained model keeps its test-split metrics."""
    from apps.detection.models import ModelVersion

    mv = ModelVersion.objects.filter(is_active=True).first()
    m = next((m for m in comparison["models"] if mv and m["model"] == mv.name), None)
    if not m or mv.map50 is not None:
        return None
    kind = "combined" if "combined" in m["results"] else "trained"
    rows = [r for r in (m["results"].get(kind), m["own_photos"].get(kind)) if r]
    photos = sum(r["photos"] for r in rows)
    if not photos:
        return None
    mv.precision = round(sum(r["precision"] * r["photos"] for r in rows) / photos, 4)
    mv.recall = round(sum(r["found"] * r["photos"] for r in rows) / photos, 4)
    mv.notes = (f"Đo trên {photos} ảnh thật ({kind}), {time.strftime('%d/%m/%Y')}: precision = box đúng nhãn / mọi box, "
                f"recall = vật tìm thấy / vật có trong ảnh. Model pretrained, không có tập test gắn box nên không có mAP.")
    mv.save(update_fields=["precision", "recall", "notes"])
    return {"model": mv.name, "precision": mv.precision, "recall": mv.recall, "photos": photos, "setup": kind,
            "notes": mv.notes}


def save_report(run: ExperimentRun, folder: Path) -> Path:
    """For the thesis: metrics.json and the photos with their boxes drawn (detections/<set>/dung, .../sai)."""
    from PIL import ImageDraw

    folder.mkdir(parents=True, exist_ok=True)
    comp = run.results["comparison"]
    (folder / "metrics.json").write_text(json.dumps({**comp, "applied_metrics": run.results.get("applied_metrics")},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    sources = {"word_photos": settings.BASE_DIR / "seed" / "images", "own_photos": EVAL_DIR}
    for name, rows in comp.get("active_per_photo", {}).items():
        for sub in ("dung", "sai"):
            shutil.rmtree(folder / "detections" / name / sub, ignore_errors=True)
            (folder / "detections" / name / sub).mkdir(parents=True, exist_ok=True)
        paths = {p.name: p for p in sources[name].rglob("*") if p.suffix.lower() in PHOTO_EXT}
        for r in rows:
            src = paths.get(r["photo"])
            if not src:
                continue
            with Image.open(src) as im:
                im = im.convert("RGB")
            im.thumbnail((800, 800))
            draw = ImageDraw.Draw(im)
            w, h = im.size
            for b in r["boxes"]:
                x1, y1, x2, y2 = b["bbox"]
                color = (22, 163, 74) if b["label"] in r["expected"] else (220, 38, 38)
                draw.rectangle([x1 * w, y1 * h, x2 * w, y2 * h], outline=color, width=3)
                text = f"{b['label']} {b['confidence']:.2f}"
                draw.rectangle([x1 * w, y1 * h, x1 * w + 7 * len(text) + 6, y1 * h + 16], fill=color)
                draw.text((x1 * w + 3, y1 * h + 2), text, fill=(255, 255, 255))
            draw.rectangle([0, h - 20, w, h], fill=(0, 0, 0))
            draw.text((6, h - 16), "dap an: " + ", ".join(r["expected"]), fill=(255, 255, 0))
            sub = "dung" if r["top1_ok"] else "sai"
            im.save(folder / "detections" / name / sub / f"{Path(r['photo']).stem}.jpg", quality=88)
    return folder


def run() -> ExperimentRun:
    t0 = time.time()
    runs = [import_run(f) for f in sorted(RUNS.glob("*")) if (f / "model_card.json").exists()]
    comparison = compare_on_photos()
    res = {"runs": runs, "comparison": comparison, "applied_metrics": apply_metrics(comparison)}
    return ExperimentRun.objects.create(kind="yolo", results=res, duration_s=round(time.time() - t0, 2))
