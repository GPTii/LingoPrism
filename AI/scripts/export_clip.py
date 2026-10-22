"""Export the CLIP label checker used by the server after YOLO (BE/apps/detection/inference.py, LabelVerifier).

MobileCLIP2-S2 (OpenCLIP, pretrained on DFN-2B, not fine-tuned) compares a crop of a box with a sentence for every
LingoPrism label ("a photo of a lemon.", ...). The sentences are encoded once here and stored inside the graph,
so the server only runs the image encoder:  crop [N, 3, 256, 256] RGB in [0, 1]  ->  probabilities [N, labels].
YOLO mixes up look-alike objects (lemon -> orange, sandals -> shoes, violin -> guitar, nose -> face); CLIP, trained
on 2 billion image-text pairs, tells them apart better, but only on a box big enough to see (see the gates there).

    pip install open_clip_torch onnx
    python AI/scripts/export_clip.py                       # labels of AI/runs/oiv7-pretrained/model_card.json
    -> BE/models/clip-mobileclip2-s2.onnx
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ["a photo of a {}.", "a close-up photo of a {}.", "a photo of the {}, a type of object."]
# the label alone is ambiguous or not what a person would write
NAMES = {"mouse": "computer mouse", "mouse animal": "mouse, the animal", "tv": "television", "glasses": "eyeglasses",
         "remote": "remote control", "hair drier": "hair dryer", "sports ball": "ball", "cell phone": "mobile phone"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="MobileCLIP2-S2")
    ap.add_argument("--pretrained", default="dfndr2b")
    ap.add_argument("--card", default=str(ROOT / "AI" / "runs" / "oiv7-pretrained" / "model_card.json"))
    ap.add_argument("--out", default=str(ROOT / "BE" / "models" / "clip-mobileclip2-s2.onnx"))
    args = ap.parse_args()

    import onnx
    import open_clip
    import torch

    labels = json.loads(Path(args.card).read_text(encoding="utf-8"))["classes"]
    model, _, preprocess = open_clip.create_model_and_transforms(args.model, pretrained=args.pretrained)
    model.eval()
    size = next(t.size for t in preprocess.transforms if type(t).__name__ == "CenterCrop")
    size = size[0] if isinstance(size, (tuple, list)) else size
    norm = next(t for t in preprocess.transforms if type(t).__name__ == "Normalize")
    tok = open_clip.get_tokenizer(args.model)
    with torch.no_grad():
        text = []
        for lab in labels:
            t = model.encode_text(tok([s.format(NAMES.get(lab, lab)) for s in TEMPLATES]))
            t = (t / t.norm(dim=-1, keepdim=True)).mean(0)
            text.append(t / t.norm())
        text = torch.stack(text)

    class Checker(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.visual = model.visual
            self.register_buffer("text", text)
            self.register_buffer("mean", torch.tensor(norm.mean).view(1, 3, 1, 1))
            self.register_buffer("std", torch.tensor(norm.std).view(1, 3, 1, 1))

        def forward(self, x):
            f = self.visual((x - self.mean) / self.std)
            f = f / f.norm(dim=-1, keepdim=True)
            return (100 * f @ self.text.T).softmax(-1)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with torch.no_grad():
        torch.onnx.export(Checker().eval(), torch.zeros(1, 3, size, size), str(out), input_names=["crops"],
                          output_names=["probs"], dynamic_axes={"crops": {0: "n"}, "probs": {0: "n"}},
                          opset_version=17, dynamo=False)
    m = onnx.load(str(out))
    for k, v in {"names": str(dict(enumerate(labels))), "imgsz": str(size),
                 "description": f"{args.model} ({args.pretrained}) zero-shot over the LingoPrism labels"}.items():
        e = m.metadata_props.add()
        e.key, e.value = k, v
    onnx.save(m, str(out))
    print(f"→ {out} ({out.stat().st_size / 1e6:.1f} MB), {len(labels)} nhãn, ảnh {size}px")


if __name__ == "__main__":
    main()
