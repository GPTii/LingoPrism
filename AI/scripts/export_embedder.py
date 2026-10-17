"""Export the image embedder used by the detection correction memory (BE/apps/detection/memory.py).

MobileNetV3-Large pretrained on ImageNet (torchvision), classifier removed: a 224x224 RGB crop in [0, 1]
-> a 960-d L2-normalised vector. ImageNet normalisation is inside the graph, so the server only resizes.
Two crops of the same kind of object (this pig, that pig) land close together, a pig and a cow further apart:
that is what lets a correction reported by a learner fix the next similar photo without retraining YOLO.

    pip install torch torchvision onnx
    python AI/scripts/export_embedder.py --out BE/models/embedder.onnx
"""
import argparse
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[2] / "BE" / "models" / "embedder.onnx"))
    args = ap.parse_args()

    import onnx
    import torch
    from torchvision.models import MobileNet_V3_Large_Weights, mobilenet_v3_large

    net = mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.IMAGENET1K_V2).eval()

    class Embedder(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.features, self.pool = net.features, net.avgpool
            self.register_buffer("mean", torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
            self.register_buffer("std", torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))

        def forward(self, x):  # [N, 3, 224, 224] RGB in [0, 1]
            v = self.pool(self.features((x - self.mean) / self.std)).flatten(1)
            return torch.nn.functional.normalize(v, dim=1)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with torch.no_grad():
        torch.onnx.export(Embedder().eval(), torch.zeros(1, 3, 224, 224), str(out), input_names=["images"],
                          output_names=["embedding"], dynamic_axes={"images": {0: "n"}, "embedding": {0: "n"}},
                          opset_version=12, dynamo=False)
    m = onnx.load(str(out))
    entry = m.metadata_props.add()
    entry.key, entry.value = "description", "mobilenet_v3_large IMAGENET1K_V2 features, 960-d, L2-normalised"
    onnx.save(m, str(out))
    print(f"→ {out} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
