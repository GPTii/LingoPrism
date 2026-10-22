"""INT8 version of a YOLO ONNX model for the server's CPU (static quantization, QDQ, per-channel weights).

    python AI/scripts/quantize_onnx.py AI/runs/oiv7-pretrained/yolov8m-oiv7-lingoprism.onnx   # -> ...-int8.onnx
    python AI/scripts/quantize_onnx.py AI/runs/coco/yolov10m.onnx

Weights and activations of the network become 8-bit integers: about 2.5x faster on 2 CPU threads and 4x smaller,
measured mAP50 0.705 -> 0.698 for the server's ensemble (AI/report/yolo/ghi_chu.md). The detection head's decode
(after the last convolution: boxes, class scores) stays in float. Activation ranges are calibrated on 96 images of
AI/testset (only ranges are learnt, no labels). The "names" metadata are copied, so inference.Detector reads it as before.
"""
import argparse
import json
import random
from pathlib import Path

import numpy as np
import onnx
from onnxruntime.quantization import CalibrationDataReader, QuantFormat, QuantType, quantize_static
from onnxruntime.quantization.shape_inference import quant_pre_process
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out", help="mặc định: <src>-int8.onnx")
    ap.add_argument("--images", type=int, default=96)
    args = ap.parse_args()
    src = Path(args.src)
    dst = Path(args.out) if args.out else src.with_name(f"{src.stem}-int8.onnx")

    m0 = onnx.load(str(src))
    size = m0.graph.input[0].type.tensor_type.shape.dim[2].dim_value
    imgs = json.loads((ROOT / "AI/testset/annotations.json").read_text(encoding="utf-8"))["images"]
    random.Random(7).shuffle(imgs)
    files = [ROOT / "AI/testset/images" / i["file"] for i in imgs[: args.images]]

    def letterbox(p):  # the same as inference.Detector._letterbox
        img = Image.open(p).convert("RGB")
        w, h = img.size
        s = min(size / w, size / h)
        img = img.resize((round(w * s), round(h * s)), Image.BILINEAR)
        c = Image.new("RGB", (size, size), (114, 114, 114))
        c.paste(img, ((size - img.size[0]) // 2, (size - img.size[1]) // 2))
        return (np.asarray(c, dtype=np.float32) / 255.0).transpose(2, 0, 1)[None]

    class Reader(CalibrationDataReader):
        def __init__(self):
            self.it = iter(files)

        def get_next(self):
            p = next(self.it, None)
            return None if p is None else {m0.graph.input[0].name: letterbox(p)}

    pre = dst.with_suffix(".pre.onnx")
    if m0.opset_import[0].version < 13:  # per-channel DequantizeLinear needs opset 13
        from onnx import version_converter
        m0 = version_converter.convert_version(m0, 13)
    onnx.save(m0, str(pre))
    quant_pre_process(str(pre), str(pre), skip_symbolic_shape=True)
    nodes = [n for n in onnx.load(str(pre)).graph.node]
    last_conv = max(i for i, n in enumerate(nodes) if n.op_type == "Conv")
    quantize_static(str(pre), str(dst), Reader(), quant_format=QuantFormat.QDQ, per_channel=True,
                    weight_type=QuantType.QInt8, activation_type=QuantType.QUInt8,
                    op_types_to_quantize=["Conv", "MatMul", "Mul", "Add"],
                    nodes_to_exclude=[n.name for n in nodes[last_conv + 1:]])
    pre.unlink()
    m = onnx.load(str(dst))
    for p in onnx.load(str(src), load_external_data=False).metadata_props:
        e = m.metadata_props.add()
        e.key, e.value = p.key, p.value
    onnx.save(m, str(dst))
    print(f"→ {dst} ({dst.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
