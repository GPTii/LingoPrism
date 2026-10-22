"""Correction memory: learners' detection error reports fix the detector's next answers without retraining.

Report (confirm with "wrong" + the right object, or "not an object")
  -> the object's crop is embedded (BE/models/embedder.onnx, MobileNetV3 features) and stored as CorrectionMemory.
Next detection
  -> a box is relabelled only if the detector makes the *same* mistake (same predicted label) on an object that
     *looks like* a reported one (cosine >= MATCH_SIMILARITY). A real cow is not turned into a pig because someone
     once corrected a pig photo: the cow does not look like that pig.
Who it applies to
  -> the reporter at once; everyone once CONSENSUS_USERS different learners reported the same mistake or staff
     approved it. Learners who mark an automatic fix as wrong count as disputes; DISPUTE_LIMIT rejects it.
Approved reports are exported as YOLO training data (AdminCorrectionViewSet.export) for the next training run.
"""
import io
import threading
from pathlib import Path

import numpy as np
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from PIL import Image, ImageOps

MATCH_SIMILARITY = 0.75
CONSENSUS_USERS = 3
DISPUTE_LIMIT = 2
CROP_MARGIN = 0.05  # widen the box a little: the model's box is often tight
_SIZE = 224

_lock = threading.Lock()
_session = None
_session_path = None


def _embedder():
    global _session, _session_path
    path = getattr(settings, "DETECTION_EMBEDDER_PATH", "")
    if not path or not Path(path).exists():
        return None
    with _lock:
        if _session is None or _session_path != path:
            import onnxruntime as ort

            opts = ort.SessionOptions()
            opts.add_session_config_entry("session.intra_op.allow_spinning", "0")
            _session, _session_path = ort.InferenceSession(path, opts, providers=["CPUExecutionProvider"]), path
        return _session


def available() -> bool:
    return _embedder() is not None


def crop(image: Image.Image, bbox) -> Image.Image:
    w, h = image.size
    x1, y1, x2, y2 = bbox
    mx, my = (x2 - x1) * CROP_MARGIN, (y2 - y1) * CROP_MARGIN
    box = (max(0, (x1 - mx) * w), max(0, (y1 - my) * h), min(w, (x2 + mx) * w), min(h, (y2 + my) * h))
    if box[2] - box[0] < 2 or box[3] - box[1] < 2:
        return image
    return image.crop(tuple(round(v) for v in box))


def embed(crops: list[Image.Image]) -> np.ndarray:
    """[n, d] L2-normalised float32; empty array when the embedder is missing."""
    session = _embedder()
    if session is None or not crops:
        return np.zeros((0, 0), dtype=np.float32)
    batch = np.stack([np.asarray(c.convert("RGB").resize((_SIZE, _SIZE), Image.BILINEAR), dtype=np.float32) / 255.0
                      for c in crops]).transpose(0, 3, 1, 2)
    return session.run(None, {session.get_inputs()[0].name: batch})[0].astype(np.float32)


def _active(user, labels):
    from .models import CorrectionMemory

    qs = CorrectionMemory.objects.filter(wrong_label__in=labels).exclude(status=CorrectionMemory.Status.REJECTED)
    return list(qs.filter(Q(status=CorrectionMemory.Status.APPROVED) | Q(user=user)).only(
        "id", "wrong_label", "correct_label", "embedding"))


def apply(user, image: Image.Image, boxes: list) -> list:
    """Relabel (or drop) boxes the detector got wrong before on a similar-looking object."""
    if not boxes:
        return boxes
    memories = _active(user, {b.label for b in boxes})
    if not memories:
        return boxes
    image = ImageOps.exif_transpose(image).convert("RGB")
    vectors = embed([crop(image, b.bbox) for b in boxes])
    if vectors.size == 0:
        return boxes
    out = []
    for b, v in zip(boxes, vectors):
        best, score = None, MATCH_SIMILARITY
        for m in memories:
            if m.wrong_label != b.label:
                continue
            s = float(np.frombuffer(bytes(m.embedding), dtype=np.float32) @ v)
            if s >= score:
                best, score = m, s
        if best is None:
            out.append(b)
            continue
        if not best.correct_label:  # reported as "not an object": do not show it again
            continue
        b.top_k = [{"label": best.correct_label, "confidence": round(score, 4)}] + [
            t for t in b.top_k if t["label"] != best.correct_label][:2]
        b.label, b.memory_id = best.correct_label, best.id
        out.append(b)
    return out


def remember(item, user) -> bool:
    """Store the learner's correction of a detection item (needs the photo and the embedder)."""
    from .models import CorrectionMemory

    photo = item.detection.photo
    if not (photo and photo.image) or not available() or len(item.bbox) != 4:
        return False
    with photo.image.open("rb") as f:
        image = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
    piece = crop(image, item.bbox)
    vector = embed([piece])[0]
    thumb = piece.copy()
    thumb.thumbnail((256, 256))
    buf = io.BytesIO()
    thumb.save(buf, "JPEG", quality=85)
    wrong = item.label
    if item.learned_from_id:  # the automatic fix was wrong: the model's own answer is the one to remember
        wrong = item.learned_from.wrong_label
    memory, _ = CorrectionMemory.objects.update_or_create(item=item, defaults={
        "user": user, "wrong_label": wrong, "correct_label": item.corrected_label,
        "embedding": vector.tobytes(), "status": CorrectionMemory.Status.PENDING,
    })
    memory.crop.save(f"{item.id}.jpg", ContentFile(buf.getvalue()), save=True)
    _consensus(memory.wrong_label, memory.correct_label)
    return True


def _consensus(wrong: str, correct: str):
    """Approve a mistake for everyone once enough different learners reported it."""
    from .models import CorrectionMemory

    same = CorrectionMemory.objects.filter(wrong_label=wrong, correct_label=correct,
                                           status=CorrectionMemory.Status.PENDING, reviewed_by__isnull=True)
    if same.values("user").distinct().count() >= CONSENSUS_USERS:
        same.update(status=CorrectionMemory.Status.APPROVED, reviewed_at=timezone.now())


def dispute(memory):
    """A learner marked an automatic fix as wrong; enough disputes reject it (unless staff approved it)."""
    from .models import CorrectionMemory

    with transaction.atomic():
        m = CorrectionMemory.objects.select_for_update().get(pk=memory.pk)
        m.disputes += 1
        if m.disputes >= DISPUTE_LIMIT and m.reviewed_by_id is None:
            m.status = CorrectionMemory.Status.REJECTED
        m.save(update_fields=["disputes", "status"])
