"""Export the Ultralytics YOLOv8 model pretrained on Open Images V7 (601 classes) as a LingoPrism model – no training.

The 601 Open Images scores are folded into our labels inside the ONNX graph (score of a label = max over its
Open Images classes, the other classes are dropped), so the server sees an ordinary YOLOv8-style model whose
"names" metadata are LingoPrism labels. Served next to the COCO model (settings.YOLO_BASE_MODEL_PATH):
COCO answers for the classes it knows, this model for the rest (helmet, pig, pen, door, pillow...).

    pip install ultralytics onnx
    python AI/scripts/export_pretrained_oiv7.py --out AI/runs/oiv7-pretrained
    cd BE && python manage.py register_model --onnx ../AI/runs/oiv7-pretrained/yolov8s-oiv7-lingoprism.onnx \
        --card ../AI/runs/oiv7-pretrained/model_card.json
"""
import argparse
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# Open Images classes beyond the one in classes.yaml (training uses one source class, detection can take several:
# Open Images labels "Man"/"Woman" rather than "Person", a mug and a coffee cup are both a cup, ...)
EXTRA = {
    "person": ["Person", "Man", "Woman", "Boy", "Girl"],
    "bird": ["Bird"],
    "helmet": ["Helmet", "Football helmet"],
    "glasses": ["Sunglasses"],
    "hat": ["Sun hat", "Fedora", "Cowboy hat", "Sombrero"],
    "cup": ["Coffee cup"],
    "knife": ["Knife"],
    "dining table": ["Kitchen & dining room table", "Coffee table"],
    "couch": ["Sofa bed", "Studio couch"],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default="yolov8s-oiv7.pt", help="yolov8n/s/m-oiv7.pt (tự tải từ Ultralytics)")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--out", default=str(ROOT / "runs" / "oiv7-pretrained"))
    ap.add_argument("--tflite", action="store_true", help="xuất thêm TFLite float16 cho điện thoại")
    args = ap.parse_args()

    import onnx
    import torch
    from ultralytics import YOLO

    data = yaml.safe_load((ROOT / "classes.yaml").read_text(encoding="utf-8"))
    classes = data["classes"] + data.get("extra", [])  # extra: objects with a word but no training images
    yolo = YOLO(args.weights)
    oi_index = {name: i for i, name in yolo.names.items()}

    labels, groups = [], []
    for c in classes:
        oi = c.get("oi") or []
        names = (oi if isinstance(oi, list) else [oi]) + EXTRA.get(c["label"], [])
        idx = [oi_index[n] for n in names if n in oi_index]
        missing = [n for n in names if n not in oi_index]
        if missing:
            print(f"[cảnh báo] {c['label']}: không có trong model: {missing}")
        if idx:
            labels.append(c["label"])
            groups.append(idx)
    print(f"{len(labels)}/{len(classes)} lớp LingoPrism có trong Open Images V7")

    class Folded(torch.nn.Module):
        def __init__(self, model):
            super().__init__()
            self.model = model
            self.groups = [torch.tensor(g) for g in groups]

        def forward(self, x):
            y = self.model(x)
            y = y[0] if isinstance(y, (list, tuple)) else y  # [1, 4 + 601, N]: cx, cy, w, h, class scores
            scores = torch.stack([y[:, 4:][:, g].amax(1) for g in self.groups], 1)
            return torch.cat([y[:, :4], scores], 1)  # [1, 4 + len(labels), N]

    model = yolo.model.fuse().eval()
    for p in model.parameters():
        p.requires_grad = False
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    name = f"{Path(args.weights).stem}-lingoprism"
    onnx_path = out / f"{name}.onnx"
    dummy = torch.zeros(1, 3, args.imgsz, args.imgsz)
    with torch.no_grad():
        torch.onnx.export(Folded(model), dummy, str(onnx_path), input_names=["images"], output_names=["output0"],
                          opset_version=12, dynamo=False)
    m = onnx.load(str(onnx_path))
    for k, v in {"names": str(dict(enumerate(labels))), "imgsz": str([args.imgsz, args.imgsz]),
                 "description": f"{args.weights} (Open Images V7) folded to LingoPrism labels"}.items():
        entry = m.metadata_props.add()
        entry.key, entry.value = k, v
    onnx.save(m, str(onnx_path))

    tflite = export_tflite(onnx_path, out, name, labels) if args.tflite else None

    card = {
        "name": name, "base_model": args.weights, "imgsz": args.imgsz, "classes": labels,
        "metrics": {}, "onnx": str(onnx_path), "tflite": str(tflite) if tflite else None,
        "note": "Pretrained on Open Images V7 by Ultralytics, not fine-tuned; Open Images class groups below.",
        "oi_classes": {lab: [yolo.names[i] for i in g] for lab, g in zip(labels, groups)},
    }
    (out / "model_card.json").write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"→ {onnx_path} ({onnx_path.stat().st_size / 1e6:.1f} MB)")


def export_tflite(onnx_path: Path, out: Path, name: str, labels: list[str]) -> Path:
    """ONNX -> TFLite (weights float16, compute float32: onnx2tf's default flatbuffer backend emits float16
    activations that the stock TFLite CONV_2D kernel rejects, hence --tflite_backend tf_converter)."""
    import shutil
    import subprocess
    import sys

    import onnx
    import onnxslim

    work = out / "tflite_work"
    work.mkdir(exist_ok=True)
    slim = work / "model.onnx"
    onnx.save(onnxslim.slim(onnx.load(str(onnx_path))), str(slim))
    subprocess.run([sys.executable, "-m", "onnx2tf", "-i", str(slim), "-o", str(work), "-nuo",
                    "-tb", "tf_converter"], check=True)
    tflite = out / f"{name}_float16.tflite"
    shutil.copy(work / "model_float16.tflite", tflite)
    (out / "labels.txt").write_text("\n".join(labels) + "\n", encoding="utf-8")
    shutil.rmtree(work)
    print(f"→ {tflite} ({tflite.stat().st_size / 1e6:.1f} MB) + labels.txt – input [1, H, W, 3], output [1, 4 + nc, N]")
    return tflite


if __name__ == "__main__":
    main()
