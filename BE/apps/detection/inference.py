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


class DetectorUnavailable(Exception):
    pass


class Detector:
    def __init__(self, path: str, classes: list[str] | None = None, input_size: int = 640):
        import onnxruntime as ort

        self.path = path
        self.session = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
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
            _detector_key = key
        return _detector
