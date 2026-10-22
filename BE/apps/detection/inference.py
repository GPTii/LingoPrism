"""Server-side object detection with ONNX Runtime.

Supports both export formats:
  * YOLOv10 end-to-end (NMS-free): output [1, 300, 6] = x1, y1, x2, y2, score, class (input-pixel coords)
  * YOLOv8 / YOLO11 style:         output [1, 4 + nc, N] = cx, cy, w, h, class scores...  (needs NMS)
Class names are read from the ultralytics ONNX metadata ("names") or the active ModelVersion.
"""
import ast
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

CONF_THRESHOLD = 0.25
IOU_THRESHOLD = 0.45
TOP_K = 3

# Fallback for COCO-pretrained exports without class metadata (interim model before custom training).
COCO_CLASSES = [
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "airplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "chair",
    "couch",
    "potted plant",
    "bed",
    "dining table",
    "toilet",
    "tv",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "oven",
    "toaster",
    "sink",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "hair drier",
    "toothbrush",
]


@dataclass
class Box:
    label: str
    confidence: float
    bbox: list[float]  # normalized x1, y1, x2, y2
    top_k: list[dict]
    memory_id: int | None = None  # relabelled by detection.memory (an earlier learner's error report)


class DetectorUnavailable(Exception):
    pass


class Detector:
    def __init__(self, path: str, classes: list[str] | None = None, input_size: int = 640):
        import onnxruntime as ort

        self.path = path
        opts = ort.SessionOptions()
        # threads must not busy-wait after a run: with two models (EnsembleDetector) the idle session's spinning
        # threads starve the other one (measured ~800 ms instead of ~170 ms per photo)
        opts.add_session_config_entry("session.intra_op.allow_spinning", "0")
        self.session = ort.InferenceSession(path, opts, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        shape = self.session.get_inputs()[0].shape
        self.size = shape[2] if isinstance(shape[2], int) else input_size
        meta = self.session.get_modelmeta().custom_metadata_map
        if classes:
            self.classes = classes
        elif "names" in meta:
            names = ast.literal_eval(meta["names"])
            self.classes = [names[i] for i in sorted(names)]
        else:
            raise DetectorUnavailable("Model không có danh sách lớp")
        if all(c.isdigit() for c in self.classes) and len(self.classes) == len(COCO_CLASSES):
            self.classes = list(COCO_CLASSES)
        self.name = Path(path).stem

    def _letterbox(self, img: Image.Image):
        w, h = img.size
        scale = min(self.size / w, self.size / h)
        nw, nh = round(w * scale), round(h * scale)
        resized = img.resize((nw, nh), Image.BILINEAR)
        canvas = Image.new("RGB", (self.size, self.size), (114, 114, 114))
        pad_x, pad_y = (self.size - nw) // 2, (self.size - nh) // 2
        canvas.paste(resized, (pad_x, pad_y))
        arr = np.asarray(canvas, dtype=np.float32) / 255.0
        return arr.transpose(2, 0, 1)[None], scale, pad_x, pad_y

    def _to_norm(self, x1, y1, x2, y2, scale, pad_x, pad_y, w, h):
        return [
            float(np.clip((x1 - pad_x) / scale / w, 0, 1)), float(np.clip((y1 - pad_y) / scale / h, 0, 1)),
            float(np.clip((x2 - pad_x) / scale / w, 0, 1)), float(np.clip((y2 - pad_y) / scale / h, 0, 1)),
        ]

    def predict(self, image: Image.Image) -> tuple[list[Box], int]:
        image = ImageOps.exif_transpose(image).convert("RGB")
        w, h = image.size
        tensor, scale, pad_x, pad_y = self._letterbox(image)
        start = time.perf_counter()
        out = self.session.run(None, {self.input_name: tensor})[0]
        ms = int((time.perf_counter() - start) * 1000)
        if out.ndim == 3 and out.shape[2] == 6:
            boxes = self._decode_v10(out[0], scale, pad_x, pad_y, w, h)
        else:
            boxes = self._decode_v8(out[0], scale, pad_x, pad_y, w, h)
        return boxes, ms

    def _decode_v10(self, rows, scale, pad_x, pad_y, w, h):
        boxes = []
        for x1, y1, x2, y2, score, cls in rows:
            if score < CONF_THRESHOLD:
                continue
            label = self.classes[int(cls)]
            boxes.append(Box(label, float(score), self._to_norm(x1, y1, x2, y2, scale, pad_x, pad_y, w, h),
                             [{"label": label, "confidence": round(float(score), 4)}]))
        return sorted(boxes, key=lambda b: -b.confidence)

    def _decode_v8(self, pred, scale, pad_x, pad_y, w, h):
        pred = pred.T if pred.shape[0] < pred.shape[1] else pred  # -> [N, 4 + nc]
        scores = pred[:, 4:]
        best = scores.max(axis=1)
        keep = best >= CONF_THRESHOLD
        pred, scores, best = pred[keep], scores[keep], best[keep]
        if len(pred) == 0:
            return []
        cx, cy, bw, bh = pred[:, 0], pred[:, 1], pred[:, 2], pred[:, 3]
        xyxy = np.stack([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], axis=1)
        cls = scores.argmax(axis=1)
        order = _nms(xyxy, best, cls)
        boxes = []
        for i in order:
            top = np.argsort(-scores[i])[:TOP_K]
            boxes.append(Box(
                self.classes[int(cls[i])], float(best[i]), self._to_norm(*xyxy[i], scale, pad_x, pad_y, w, h),
                [{"label": self.classes[int(j)], "confidence": round(float(scores[i][j]), 4)} for j in top],
            ))
        return boxes


def _nms(xyxy, scores, classes):
    keep = []
    for c in np.unique(classes):
        idx = np.where(classes == c)[0]
        idx = idx[np.argsort(-scores[idx])]
        while len(idx):
            i = idx[0]
            keep.append(i)
            if len(idx) == 1:
                break
            rest = idx[1:]
            xx1 = np.maximum(xyxy[i, 0], xyxy[rest, 0])
            yy1 = np.maximum(xyxy[i, 1], xyxy[rest, 1])
            xx2 = np.minimum(xyxy[i, 2], xyxy[rest, 2])
            yy2 = np.minimum(xyxy[i, 3], xyxy[rest, 3])
            inter = np.clip(xx2 - xx1, 0, None) * np.clip(yy2 - yy1, 0, None)
            area = lambda b: (b[..., 2] - b[..., 0]) * (b[..., 3] - b[..., 1])  # noqa: E731
            iou = inter / (area(xyxy[i]) + area(xyxy[rest]) - inter + 1e-9)
            idx = rest[iou < IOU_THRESHOLD]
    return sorted(keep, key=lambda i: -scores[i])


_lock = threading.Lock()
_detector: Detector | None = None
_detector_key = None


def _iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


SAME_OBJECT_IOU = 0.7  # two boxes this close are one object, whatever labels the models gave it
SURE_UNKNOWN = 0.25  # = CONF_THRESHOLD: a box of a class COCO does not know vetoes COCO boxes from this confidence on


def _merge(boxes: list[Box]) -> list[Box]:
    """Keep the most confident label per object; the other labels become alternatives (top_k) for the learner."""
    kept: list[Box] = []
    for b in sorted(boxes, key=lambda b: -b.confidence):
        same = next((k for k in kept if _iou(k.bbox, b.bbox) >= SAME_OBJECT_IOU), None)
        if same is None:
            kept.append(b)
        elif b.label not in {t["label"] for t in same.top_k}:
            same.top_k = (same.top_k + [{"label": b.label, "confidence": round(b.confidence, 4)}])[:TOP_K]
    return kept


class EnsembleDetector:
    """The active LingoPrism model + the pretrained COCO model (settings.YOLO_BASE_MODEL_PATH).

    Both models answer and boxes of the same object are merged (most confident label wins, the others become
    alternatives). A COCO box lying on an object of a class COCO was never taught is dropped: COCO then picks
    the closest class it knows, very confidently (tiger -> zebra 0.95, lion -> bear 0.86, pig -> cow 0.80).
    Compare setups with AI/scripts/eval_photos.py. Drop YOLO_BASE_MODEL_PATH to serve the active model alone."""

    def __init__(self, primary: Detector, base: Detector):
        self.primary, self.base = primary, base
        self.classes = primary.classes
        self.name = f"{primary.name}+coco"
        self._base_classes = set(base.classes)

    def predict(self, image):
        b_base, t1 = self.base.predict(image)
        b_new, t2 = self.primary.predict(image)
        return self.combine(b_new, b_base), t1 + t2

    def combine(self, b_new: list[Box], b_base: list[Box]) -> list[Box]:
        """Merge both models' boxes (also used by AI/scripts/eval_testset.py on cached predictions).
        Only a confident box of a class unknown to COCO vetoes a COCO box: the same as the server's threshold, so an
        evaluation run with a lower threshold (for mAP) keeps the server's behaviour."""
        known = set(self.classes)
        unknown_to_base = [b for b in b_new if b.label not in self._base_classes and b.confidence >= SURE_UNKNOWN]
        b_base = [b for b in b_base if b.label in known
                  and not any(_iou(b.bbox, n.bbox) >= 0.5 for n in unknown_to_base)]
        return _merge([Box(b.label, b.confidence, b.bbox, list(b.top_k), b.memory_id) for b in b_base + b_new])


# CLIP may rename a box only when YOLO is unsure (confidence < CLIP_MAX_CONF) about an object big enough to see
# (>= CLIP_MIN_AREA of the photo), CLIP is sure of another label (>= CLIP_SURE) and gives YOLO's label < CLIP_DOUBT.
# Chosen so that the test set's mAP does not drop (renaming every box: word photos top-1 68% -> 90% but test mAP50
# 0.705 -> 0.653, CLIP is poor on small or hidden objects); see AI/report/yolo/ghi_chu.md.
CLIP_MAX_CONF = 0.6
CLIP_MIN_AREA = 0.1
CLIP_SURE = 0.6
CLIP_DOUBT = 0.1


class LabelVerifier:
    """Second opinion of CLIP (AI/scripts/export_clip.py) on the label of each box: YOLO mixes up look-alike objects
    (lemon -> orange, sandals -> shoes, violin -> guitar, nose -> face). The renamed box keeps YOLO's label as an
    alternative (top_k)."""

    def __init__(self, path: str):
        import onnxruntime as ort

        opts = ort.SessionOptions()
        opts.add_session_config_entry("session.intra_op.allow_spinning", "0")
        self.session = ort.InferenceSession(path, opts, providers=["CPUExecutionProvider"])
        meta = self.session.get_modelmeta().custom_metadata_map
        names = ast.literal_eval(meta["names"])
        self.labels = [names[i] for i in sorted(names)]
        self.index = {lab: i for i, lab in enumerate(self.labels)}
        self.size = int(meta.get("imgsz", 256))

    def _crop(self, img: Image.Image, bbox, pad=0.1) -> np.ndarray:
        w, h = img.size
        x1, y1, x2, y2 = bbox
        dx, dy = (x2 - x1) * pad, (y2 - y1) * pad
        c = img.crop((max(0, (x1 - dx) * w), max(0, (y1 - dy) * h), min(w, (x2 + dx) * w), min(h, (y2 + dy) * h)))
        s = self.size / min(c.size)  # shorter side to size, then the centre square (CLIP's own preprocessing)
        c = c.resize((max(self.size, round(c.size[0] * s)), max(self.size, round(c.size[1] * s))), Image.BILINEAR)
        left, top = (c.size[0] - self.size) // 2, (c.size[1] - self.size) // 2
        c = c.crop((left, top, left + self.size, top + self.size))
        return np.asarray(c, dtype=np.float32).transpose(2, 0, 1) / 255.0

    def check(self, image: Image.Image, boxes: list[Box]) -> tuple[list[Box], int]:
        todo = [i for i, b in enumerate(boxes) if b.label in self.index and CONF_THRESHOLD <= b.confidence < CLIP_MAX_CONF
                and (b.bbox[2] - b.bbox[0]) * (b.bbox[3] - b.bbox[1]) >= CLIP_MIN_AREA]
        if not todo:
            return boxes, 0
        image = ImageOps.exif_transpose(image).convert("RGB")  # the boxes are relative to the upright photo
        start = time.perf_counter()
        probs = self.session.run(None, {"crops": np.stack([self._crop(image, boxes[i].bbox) for i in todo])})[0]
        ms = int((time.perf_counter() - start) * 1000)
        out = list(boxes)
        for i, p in zip(todo, probs):
            b, j = boxes[i], int(p.argmax())
            if self.labels[j] != b.label and p[j] >= CLIP_SURE and p[self.index[b.label]] < CLIP_DOUBT:
                alt = [t for t in b.top_k if t["label"] != self.labels[j]]
                out[i] = Box(self.labels[j], b.confidence, b.bbox,
                             ([{"label": self.labels[j], "confidence": round(float(p[j]), 4)}] + alt)[:TOP_K], b.memory_id)
        return out, ms


class VerifiedDetector:
    """A detector whose labels are re-checked by CLIP (settings.DETECTION_CLIP_PATH)."""

    def __init__(self, detector, verifier: LabelVerifier):
        self.detector, self.verifier = detector, verifier
        self.classes = detector.classes
        self.name = f"{detector.name}+clip"

    def predict(self, image):
        boxes, ms = self.detector.predict(image)
        boxes, ms_clip = self.verifier.check(image, boxes)
        return boxes, ms + ms_clip


def with_verifier(detector):
    """Wrap `detector` with the CLIP check when settings.DETECTION_CLIP_PATH exists (missing = YOLO alone)."""
    from django.conf import settings

    path = getattr(settings, "DETECTION_CLIP_PATH", "")
    return VerifiedDetector(detector, LabelVerifier(path)) if path and Path(path).exists() else detector


def get_detector() -> Detector:
    """Load the active ModelVersion (or settings.YOLO_MODEL_PATH) once per process."""
    global _detector, _detector_key
    from django.conf import settings

    from .models import ModelVersion

    mv = ModelVersion.objects.filter(is_active=True).order_by("-created_at").first()
    path = mv.file if mv else settings.YOLO_MODEL_PATH
    key = (path, mv.id if mv else None)
    with _lock:
        if _detector is None or _detector_key != key:
            if not Path(path).exists():
                raise DetectorUnavailable("Server chưa có mô hình YOLOv10. Hãy dùng chế độ nhận diện trên điện thoại.")
            _detector = Detector(path, mv.classes if mv and mv.classes else None, mv.input_size if mv else 640)
            _detector.name = mv.name if mv else _detector.name
            base = getattr(settings, "YOLO_BASE_MODEL_PATH", "")
            if mv and base and Path(base).exists() and Path(base).resolve() != Path(path).resolve():
                _detector = EnsembleDetector(_detector, Detector(base))
            if mv:
                _detector = with_verifier(_detector)
            _detector_key = key
        return _detector
