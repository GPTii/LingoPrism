"""Export the multilingual phoneme recogniser used by speaking practice (BE/apps/speech) to ONNX INT8.

Model: facebook/wav2vec2-xlsr-53-espeak-cv-ft (Xu, Baevski & Auli 2021, "Simple and Effective Zero-shot Cross-lingual
Phoneme Recognition"): wav2vec2 XLSR-53 fine-tuned with CTC on CommonVoice to output espeak-style IPA phones. It hears
the phones that were *said*, not the nearest real word as a speech-to-text engine does.

    pip install torch transformers onnx onnxruntime
    python AI/scripts/export_phoneme_model.py --out BE/models

Writes <out>/phoneme-xlsr53-int8.onnx (input "audio" float32 [1, samples] 16 kHz, output "logits" [1, frames, vocab],
one frame = 20 ms) and <out>/phoneme-vocab.json (id -> IPA token).
"""
import argparse
import json
from pathlib import Path

MODEL = "facebook/wav2vec2-xlsr-53-espeak-cv-ft"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="BE/models")
    ap.add_argument("--model", default=MODEL)
    args = ap.parse_args()

    import torch
    from onnxruntime.quantization import QuantType, quantize_dynamic
    from huggingface_hub import hf_hub_download
    from transformers import Wav2Vec2ForCTC

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    model = Wav2Vec2ForCTC.from_pretrained(args.model).eval()
    # the vocabulary file directly: the phoneme tokenizer class would also want the phonemizer / espeak backend
    tokens = json.loads(Path(hf_hub_download(args.model, "vocab.json")).read_text(encoding="utf-8"))
    vocab = {i: t for t, i in tokens.items()}
    (out / "phoneme-vocab.json").write_text(json.dumps({"model": args.model, "pad": model.config.pad_token_id,
                                                       "vocab": vocab}, ensure_ascii=False, indent=0), encoding="utf-8")

    class Wrapped(torch.nn.Module):
        def __init__(self, m):
            super().__init__()
            self.m = m

        def forward(self, audio):  # the processor's normalisation, inside the graph
            audio = (audio - audio.mean(dim=-1, keepdim=True)) / torch.sqrt(audio.var(dim=-1, keepdim=True) + 1e-7)
            return self.m(audio).logits

    fp32 = out / "phoneme-xlsr53.onnx"
    torch.onnx.export(Wrapped(model), torch.zeros(1, 32000), str(fp32), input_names=["audio"], output_names=["logits"],
                      dynamic_axes={"audio": {1: "samples"}, "logits": {1: "frames"}}, opset_version=14, dynamo=False)
    int8 = out / "phoneme-xlsr53-int8.onnx"
    quantize_dynamic(str(fp32), str(int8), weight_type=QuantType.QInt8)
    fp32.unlink()
    for f in fp32.parent.glob(fp32.name + ".data"):
        f.unlink()
    print(f"→ {int8} ({int8.stat().st_size / 1e6:.0f} MB), {len(vocab)} tokens")


if __name__ == "__main__":
    main()
