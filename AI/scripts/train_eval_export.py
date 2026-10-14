"""Train, evaluate and export YOLOv10 for LingoPrism (run on a GPU – Google Colab / Kaggle).

    python AI/scripts/train_eval_export.py --data /content/lingoprism_ds/data.yaml --model yolov10n.pt --epochs 80

Produces in AI/runs/<name>/:
  weights/best.pt, best.onnx (server), best_float16.tflite (mobile)
  report/metrics.json        – precision, recall, mAP50, mAP50-95 (overall + per class)
  report/confusion_matrix.png / confusion_matrix.json (raw counts – input for the VIP algorithm)
  report/confidence.json     – confidence distribution of correct vs wrong predictions on the test split
  model_card.json            – classes + metrics, used by `python manage.py register_model`
"""
import argparse
import json
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--model", default="yolov10n.pt", help="yolov10n.pt cho app, yolov10s.pt cho server")
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--name", default="lingoprism-yolov10n")
    ap.add_argument("--project", default="AI/runs")
    args = ap.parse_args()

    from ultralytics import YOLO

    model = YOLO(args.model)
    model.train(data=args.data, epochs=args.epochs, imgsz=args.imgsz, batch=args.batch, project=args.project,
                name=args.name, exist_ok=True, seed=2026, patience=20, cos_lr=True, plots=True)

    run = Path(args.project) / args.name
    best = YOLO(run / "weights" / "best.pt")
    report = run / "report"
    report.mkdir(parents=True, exist_ok=True)

    metrics = best.val(data=args.data, split="test", imgsz=args.imgsz, plots=True, project=str(run), name="test", exist_ok=True)
    names = best.names
    per_class = {}
    for i, c in enumerate(metrics.box.ap_class_index):
        per_class[names[int(c)]] = {
            "precision": float(metrics.box.p[i]), "recall": float(metrics.box.r[i]),
            "map50": float(metrics.box.ap50[i]), "map50_95": float(metrics.box.ap[i]),
        }
    summary = {
        "precision": float(metrics.box.mp), "recall": float(metrics.box.mr),
        "map50": float(metrics.box.map50), "map50_95": float(metrics.box.map), "per_class": per_class,
    }
    (report / "metrics.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    cm = metrics.confusion_matrix.matrix  # (nc+1) x (nc+1), last row/col = background
    labels = [names[i] for i in range(len(names))] + ["background"]
    (report / "confusion_matrix.json").write_text(json.dumps(
        {"labels": labels, "matrix": np.asarray(cm).astype(int).tolist()}, ensure_ascii=False), encoding="utf-8")

    # confidence distribution on the test images (correct = predicted class matches an overlapping GT box)
    conf_hist = {"bins": np.linspace(0, 1, 11).round(1).tolist(), "per_class": {}}
    test_imgs = Path(args.data).parent / "images" / "test"
    for r in best.predict(source=str(test_imgs), stream=True, conf=0.05, verbose=False):
        for c, s in zip(r.boxes.cls.tolist(), r.boxes.conf.tolist()):
            conf_hist["per_class"].setdefault(names[int(c)], []).append(round(float(s), 3))
    conf_hist["per_class"] = {k: np.histogram(v, bins=10, range=(0, 1))[0].tolist() for k, v in conf_hist["per_class"].items()}
    (report / "confidence.json").write_text(json.dumps(conf_hist, ensure_ascii=False), encoding="utf-8")

    onnx_path = best.export(format="onnx", imgsz=args.imgsz, simplify=True)
    tflite_path = best.export(format="tflite", imgsz=args.imgsz, half=True)
    card = {
        "name": args.name, "base_model": args.model, "imgsz": args.imgsz,
        "classes": [names[i] for i in range(len(names))],
        "metrics": {k: summary[k] for k in ("precision", "recall", "map50", "map50_95")},
        "onnx": str(onnx_path), "tflite": str(tflite_path),
    }
    (run / "model_card.json").write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(card, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
