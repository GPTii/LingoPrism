"""Fine-tune the server's Open Images V7 model (yolov8m-oiv7) on build_oiv7_finetune.py's dataset, then export it the
way the server reads it. Run on a GPU (Google Colab: AI/notebooks/finetune_oiv7_colab.ipynb).

    python AI/scripts/finetune_oiv7.py --data /content/oiv7_ft/data.yaml --project /content/drive/MyDrive/lingoprism_runs

  * same 601 classes as the base model -> Ultralytics transfers every weight, the head included (nothing re-learnt
    from zero); the backbone is frozen (--freeze 10) and the learning rate small: the model is nudged, not retrained;
  * resumes from <project>/<name>/weights/last.pt when a Colab session was cut;
  * before / after on the same held-out images (val split, 601-class mAP), so the gain is measured on equal terms;
  * export: export_pretrained_oiv7.py folds the 601 scores into the LingoPrism labels inside the ONNX graph, exactly
    like the model the server runs now -> <project>/<name>/export/yolov8m-oiv7-ft-lingoprism.onnx + model_card.json.
The final verdict is the project's own test set on the developer machine (eval_testset.py, see the notebook).
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def metrics(res) -> dict:
    b = res.box
    return {
        "precision": round(float(b.mp), 4),
        "recall": round(float(b.mr), 4),
        "map50": round(float(b.map50), 4),
        "map50_95": round(float(b.map), 4),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--base", default="yolov8m-oiv7.pt")
    ap.add_argument("--project", required=True)
    ap.add_argument("--name", default="oiv7m-ft-v5")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--hours", type=float, default=4.0, help="giới hạn cứng (Colab miễn phí ngắt sau vài giờ)")
    ap.add_argument("--freeze", type=int, default=10, help="số lớp đầu giữ nguyên (backbone YOLOv8 = 10)")
    ap.add_argument("--lr0", type=float, default=0.002)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--patience", type=int, default=8)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    from ultralytics import YOLO

    run = Path(args.project) / args.name
    report = run / "report"
    report.mkdir(parents=True, exist_ok=True)
    common = {
        "data": args.data,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "workers": args.workers,
        "device": args.device,
    }

    before_file = report / "val_before.json"
    if not before_file.exists():  # the base model on the same held-out images
        before = metrics(YOLO(args.base).val(**common, project=str(run), name="val_before", exist_ok=True))
        before_file.write_text(json.dumps(before, indent=1), encoding="utf-8")

    last, done = run / "weights" / "last.pt", run / "TRAINED"
    if not done.exists():
        if last.exists():  # a Colab session was cut: carry on from the last epoch
            YOLO(str(last)).train(resume=True)
        else:
            YOLO(args.base).train(
                **common,
                epochs=args.epochs,
                time=args.hours,
                patience=args.patience,
                freeze=args.freeze,
                optimizer="SGD",
                lr0=args.lr0,
                lrf=0.1,
                momentum=0.9,
                warmup_epochs=1,
                cos_lr=True,
                close_mosaic=5,
                project=args.project,
                name=args.name,
                exist_ok=True,
            )
        done.write_text("ok", encoding="utf-8")

    best = run / "weights" / "best.pt"
    after = metrics(YOLO(str(best)).val(**common, project=str(run), name="val_after", exist_ok=True))
    (report / "val_after.json").write_text(json.dumps(after, indent=1), encoding="utf-8")
    before = json.loads(before_file.read_text(encoding="utf-8"))
    print("Trước:", before, "\nSau:  ", after)

    weights = run / "export" / "yolov8m-oiv7-ft.pt"
    weights.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(best, weights)
    subprocess.run(
        [
            sys.executable,
            str(HERE / "export_pretrained_oiv7.py"),
            "--weights",
            str(weights),
            "--imgsz",
            str(args.imgsz),
            "--out",
            str(weights.parent),
        ],
        check=True,
    )
    summary = {
        "base": args.base,
        "data": args.data,
        "val_before": before,
        "val_after": after,
        "settings": {k: getattr(args, k) for k in ("epochs", "hours", "freeze", "lr0", "batch", "imgsz")},
    }
    (report / "finetune_summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print("→", weights.parent / "yolov8m-oiv7-ft-lingoprism.onnx")


if __name__ == "__main__":
    main()
