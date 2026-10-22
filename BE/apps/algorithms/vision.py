"""Visual-confusion profile of the object classes – the vision input of VIP.

For every YOLO class c the profile stores
    mean_conf(c)   average confidence of correct detections of c (0 when c is missed),
    confusion(c)   {other class: share}, how often c is taken for another class,
    score(c)       Σ shares ∈ [0, 1]  (0 = never confused, 1 = always confused / missed).

Sources, best first:
  1. the confusion matrix written by AI/scripts/train_eval_export.py on the test split
     (Ultralytics layout: matrix[predicted][true], last row/column = background);
  2. otherwise the active model run on the reviewed photo of every word that has a YOLO class:
     the share of confidence going to boxes of *other* classes overlapping the object, or a miss;
  3. in both cases, learners' corrections in the app (DetectionItem.feedback = wrong / corrected_label) are added.
"""
import json
from collections import defaultdict
from pathlib import Path

from django.conf import settings
from PIL import Image

from apps.detection.models import DetectionItem
from apps.vocab.models import Word

from .models import ExperimentRun

IOU_SAME_OBJECT = 0.45


def _iou(a, b):
    x1, y1, x2, y2 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0


def from_confusion_matrix(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    labels, m = data["labels"], data["matrix"]
    out = {}
    for t, lab in enumerate(labels):
        if lab == "background":
            continue
        col = [m[p][t] for p in range(len(labels))]
        total = sum(col)
        if not total:
            continue
        conf = {labels[p]: col[p] / total for p in range(len(labels)) if p != t and col[p]}
        out[lab] = {"mean_conf": None, "confusion": conf, "score": min(1.0, sum(conf.values())), "samples": total}
    # confidence.json (same report folder): histogram of the confidences predicted for each class on the test set
    hist_path = Path(path).with_name("confidence.json")
    if hist_path.exists():
        hist = json.loads(hist_path.read_text(encoding="utf-8"))
        edges = hist["bins"]
        mids = [(edges[i] + edges[i + 1]) / 2 for i in range(len(edges) - 1)]
        for lab, counts in hist.get("per_class", {}).items():
            if lab in out and sum(counts):
                out[lab]["mean_conf"] = round(sum(m * c for m, c in zip(mids, counts)) / sum(counts), 4)
    return out


def from_photos() -> dict:
    """Run the active detector on the reviewed word photos (seed/images) – real model outputs."""
    from apps.detection.inference import get_detector

    detector = get_detector()
    folder = Path(settings.BASE_DIR) / "seed" / "images"
    out = {}
    known = set(detector.classes)  # a class the model was not trained on tells nothing about confusion
    for word in Word.objects.exclude(yolo_label="").filter(yolo_label__in=known).order_by("slug"):
        src = folder / f"{word.slug}.jpg"
        if not src.exists():
            continue
        boxes, _ = detector.predict(Image.open(src))
        own = [b for b in boxes if b.label == word.yolo_label]
        conf = defaultdict(float)
        if own:
            main = max(own, key=lambda b: b.confidence)
            for b in boxes:
                if b.label != main.label and _iou(b.bbox, main.bbox) >= IOU_SAME_OBJECT:
                    conf[b.label] = max(conf[b.label], b.confidence / (b.confidence + main.confidence))
            mean_conf = main.confidence
        else:  # missed: what the model saw instead (or background)
            for b in boxes[:3]:
                conf[b.label] = max(conf[b.label], b.confidence)
            if not conf:
                conf["background"] = 1.0
            mean_conf = 0.0
        out[word.yolo_label] = {"mean_conf": round(mean_conf, 4),
                                "confusion": {k: round(v, 4) for k, v in conf.items()},
                                "score": round(min(1.0, sum(conf.values()) if own else 1.0), 4), "samples": 1}
    return out


def add_user_feedback(profile: dict) -> dict:
    """Learners' corrections: an item marked wrong (optionally with the right label) counts as a confusion."""
    for it in DetectionItem.objects.filter(feedback=DetectionItem.Feedback.WRONG).values("label", "corrected_label"):
        true = it["corrected_label"] or None
        if not true:
            continue
        p = profile.setdefault(true, {"mean_conf": None, "confusion": {}, "score": 0.0, "samples": 0})
        n = p["samples"] or 1
        p["confusion"][it["label"]] = p["confusion"].get(it["label"], 0) + 1 / (n + 1)
        p["samples"] = n + 1
        p["score"] = min(1.0, sum(p["confusion"].values()))
    return profile


def build(confusion_matrix: str | None = None) -> dict:
    if confusion_matrix:
        source, profile = "confusion_matrix", from_confusion_matrix(Path(confusion_matrix))
    else:
        source, profile = "photos", from_photos()
    profile = add_user_feedback(profile)
    ExperimentRun.objects.create(kind="vision", results={"source": source, "classes": profile})
    return profile


def latest() -> dict:
    run = ExperimentRun.objects.filter(kind="vision").first()
    return run.results.get("classes", {}) if run else {}
