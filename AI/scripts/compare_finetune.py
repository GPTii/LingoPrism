"""Before / after of a fine-tuned Open Images model on the project's test set, with a stated rule for using it.

    python AI/scripts/quantize_onnx.py AI/runs/oiv7m-ft-v5/yolov8m-oiv7-ft-lingoprism.onnx
    python AI/scripts/eval_testset.py --model ft=AI/runs/oiv7m-ft-v5/yolov8m-oiv7-ft-lingoprism-int8.onnx
    python AI/scripts/compare_finetune.py --name ft --run AI/runs/oiv7m-ft-v5

Compares "<name>+coco-m-int8+clip" (the fine-tuned model in the server's own setup) with the setup the server runs now,
overall and on the weak classes the fine-tune targeted (summary.json of build_oiv7_finetune.py).
Rule: use it only if mAP50 over all classes does not drop by more than TOLERANCE and the weak classes' mean AP50 rises.
Writes AI/report/yolo/finetune_<name>.md (tables for the report) and prints the verdict.
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "AI" / "report" / "yolo"
ACTIVE = "oiv7m-int8+coco-m-int8+clip"
TOLERANCE = 0.005


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="ft")
    ap.add_argument("--run", required=True, help="thư mục giải nén từ Colab (có summary.json, report/)")
    args = ap.parse_args()

    run = Path(args.run)
    metrics = json.loads((REPORT / "testset" / "metrics.json").read_text(encoding="utf-8"))["setups"]
    new_key = f"{args.name}+coco-m-int8+clip"
    if new_key not in metrics:
        raise SystemExit(f"Chưa chấm {new_key}: chạy eval_testset.py --model {args.name}=... trước")
    old, new = metrics[ACTIVE], metrics[new_key]
    summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    weak = [c for c in summary["weak"] if c in old["per_class"] and c in new["per_class"]]

    def mean(setup, key="map50"):
        vals = [setup["per_class"][c][key] for c in weak]
        return sum(vals) / len(vals) if vals else 0.0

    rows = [
        ("Precision", "precision"),
        ("Recall", "recall"),
        ("F1", "f1"),
        ("mAP50", "map50"),
        ("mAP50-95", "map50_95"),
    ]
    lines = [
        f"# Fine-tune {args.name}: trước / sau trên tập test {old['images']} ảnh",
        "",
        f"Dữ liệu: {summary['images']} ảnh ({summary.get('images_open_images', summary['images'])} Open Images V7 *train*"
        + (f" + {summary['lvis']['images']} COCO train2017/LVIS" if summary.get("lvis") else "")
        + "; nhãn người vẽ"
        + (
            " + nhãn giả của model gốc cho phần chưa vẽ"
            if (Path(args.run) / "pseudo.json").exists() or summary.get("pseudo")
            else ""
        )
        + f"), {len(summary['weak'])} lớp yếu + {len(summary['replay'])} lớp ôn lại.",
        "",
        "| Chỉ số | Đang dùng | Sau fine-tune | Chênh |",
        "|---|---|---|---|",
    ]
    lines += [f"| {label} | {old[k]:.3f} | {new[k]:.3f} | {new[k] - old[k]:+.3f} |" for label, k in rows]
    lines += [
        f"| mAP50 trung bình {len(weak)} lớp yếu | {mean(old):.3f} | {mean(new):.3f} | {mean(new) - mean(old):+.3f} |",
        f"| Thời gian (ms / ảnh) | {old['ms_per_image']} | {new['ms_per_image']} | |",
        "",
        "## Từng lớp yếu (AP50)",
        "",
        "| Lớp | Đang dùng | Sau | Chênh | Recall trước → sau |",
        "|---|---|---|---|---|",
    ]
    for c in sorted(weak, key=lambda c: new["per_class"][c]["map50"] - old["per_class"][c]["map50"], reverse=True):
        o, n = old["per_class"][c], new["per_class"][c]
        lines.append(
            f"| {c} | {o['map50']:.3f} | {n['map50']:.3f} | {n['map50'] - o['map50']:+.3f} | "
            f"{o['recall']:.3f} → {n['recall']:.3f} |"
        )
    keep = new["map50"] >= old["map50"] - TOLERANCE and mean(new) > mean(old)
    verdict = (
        f"DÙNG model mới: lớp yếu tốt lên, mAP chung không giảm quá {TOLERANCE}."
        if keep
        else "KHÔNG dùng: "
        + ("mAP chung giảm quá ngưỡng." if new["map50"] < old["map50"] - TOLERANCE else "lớp yếu không tốt lên.")
    )
    lines += [
        "",
        f"**Kết luận (quy tắc: mAP50 chung không giảm quá {TOLERANCE}, trung bình lớp yếu phải tăng): {verdict}**",
    ]
    out = REPORT / f"finetune_{args.name}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[4:12]))
    print(verdict, "\n→", out)


if __name__ == "__main__":
    main()
