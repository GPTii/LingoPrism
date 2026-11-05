"""Weight-space average of the base model and a fine-tuned copy (WiSE-FT, Wortsman et al., CVPR 2022).

    w = (1 - alpha) * w_base + alpha * w_finetuned

Fine-tuning moved yolov8m-oiv7 towards the new photos but away from what it knew (AI/report/yolo/finetune_ft6.md);
interpolating the weights usually keeps most of both. Both ONNX files must come from the same export
(export_pretrained_oiv7.py / finetune_oiv7.py: same graph, same 236 folded labels) – checked here. BatchNorm is
already fused into the convolutions, so this averages the fused weights: close to, not exactly, averaging the
PyTorch weights.

    python AI/scripts/weight_average_onnx.py BE/models/yolov8m-oiv7-lingoprism.onnx \
        AI/runs/oiv7m-ft-v6/yolov8m-oiv7-ft-lingoprism.onnx --alpha 0.5 --out AI/runs/soup/ft6-a50.onnx
"""
import argparse
from pathlib import Path

import numpy as np
import onnx
from onnx import numpy_helper


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("finetuned")
    ap.add_argument("--alpha", type=float, required=True, help="0 = model gốc, 1 = model fine-tune")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    base, ft = onnx.load(args.base), onnx.load(args.finetuned)
    assert [n.op_type for n in base.graph.node] == [n.op_type for n in ft.graph.node], "hai model khác cấu trúc"
    assert {p.key: p.value for p in base.metadata_props}.get("names") == \
        {p.key: p.value for p in ft.metadata_props}.get("names"), "hai model khác danh sách nhãn"
    weights = {i.name: numpy_helper.to_array(i) for i in ft.graph.initializer}
    changed = 0
    for init in base.graph.initializer:
        w0, w1 = numpy_helper.to_array(init), weights[init.name]
        assert w0.shape == w1.shape, init.name
        if w0.dtype.kind != "f" or np.array_equal(w0, w1):
            continue
        mixed = ((1 - args.alpha) * w0.astype(np.float64) + args.alpha * w1.astype(np.float64)).astype(w0.dtype)
        init.CopyFrom(numpy_helper.from_array(mixed, init.name))
        changed += 1
    meta = {p.key: p for p in base.metadata_props}
    if "description" in meta:
        meta["description"].value += f" | weight average: {1 - args.alpha:.2f} base + {args.alpha:.2f} {Path(args.finetuned).parent.name}"
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(base, out)
    print(f"→ {out} ({changed} tensor trộn, alpha {args.alpha})")


if __name__ == "__main__":
    main()
