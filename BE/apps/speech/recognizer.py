"""Phone recogniser: wav2vec2 XLSR-53 espeak (ONNX INT8), loaded once per process (the Celery worker in production)."""

import json
import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from django.conf import settings

FRAME_S = 0.02  # one output frame = 20 ms of audio

_lock = threading.Lock()
_model = None


class RecogniserUnavailable(Exception):
    pass


@dataclass
class Heard:
    token: str
    frame: int  # first frame of the token
    end: int  # last frame (inclusive)
    prob: float  # mean posterior of the token over its frames


class Recogniser:
    def __init__(self, path: Path, vocab_path: Path):
        import onnxruntime as ort

        opts = ort.SessionOptions()
        opts.add_session_config_entry("session.intra_op.allow_spinning", "0")
        self.session = ort.InferenceSession(str(path), opts, providers=["CPUExecutionProvider"])
        meta = json.loads(vocab_path.read_text(encoding="utf-8"))
        self.vocab = {int(k): t for k, t in meta["vocab"].items()}
        self.blank = int(meta.get("pad", 0))
        self.ignore = {i for i, t in self.vocab.items() if t.startswith("<") or t in ("??",)} | {self.blank}

    def posteriors(self, audio: np.ndarray) -> np.ndarray:
        """[frames, vocab] probabilities."""
        logits = self.session.run(None, {"audio": audio[None].astype(np.float32)})[0][0]
        logits = logits - logits.max(axis=-1, keepdims=True)
        p = np.exp(logits)
        return p / p.sum(axis=-1, keepdims=True)

    def decode(self, post: np.ndarray) -> list[Heard]:
        """Greedy CTC: runs of the same non-blank token = one phone."""
        ids = post.argmax(axis=-1)
        out: list[Heard] = []
        i = 0
        while i < len(ids):
            j = i
            while j + 1 < len(ids) and ids[j + 1] == ids[i]:
                j += 1
            if int(ids[i]) not in self.ignore:
                out.append(Heard(self.vocab[int(ids[i])], i, j, float(post[i : j + 1, ids[i]].mean())))
            i = j + 1
        return out


def get() -> Recogniser:
    global _model
    with _lock:
        if _model is None:
            path = Path(getattr(settings, "SPEECH_MODEL_PATH", ""))
            vocab = Path(getattr(settings, "SPEECH_VOCAB_PATH", ""))
            if not path.exists() or not vocab.exists():
                raise RecogniserUnavailable("Server chưa có mô hình chấm phát âm")
            _model = Recogniser(path, vocab)
        return _model


def available() -> bool:
    return (
        Path(getattr(settings, "SPEECH_MODEL_PATH", "")).exists()
        and Path(getattr(settings, "SPEECH_VOCAB_PATH", "")).exists()
    )
