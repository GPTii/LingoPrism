"""Approved error reports -> YOLO training data for the next run (merged by AI/scripts/merge_feedback.py).

One image per reported photo with every object of that photo:
  * the object a learner corrected            -> the corrected label
  * an object reported as "not an object"     -> no box (background, which is the truth)
  * an object confirmed correct               -> its label
  * an object nobody gave feedback on         -> kept when the detector was fairly sure (>= KEEP_UNREVIEWED),
                                                 otherwise the photo would teach "this is background"
Labels are written by name (names.txt), so the zip does not depend on the class order of any model.
"""
import io
import zipfile

from PIL import Image, ImageOps

from .models import CorrectionMemory, DetectionItem

KEEP_UNREVIEWED = 0.5
MAX_SIDE = 640


def _yolo_line(index: int, bbox) -> str:
    x1, y1, x2, y2 = bbox
    return f"{index} {(x1 + x2) / 2:.6f} {(y1 + y2) / 2:.6f} {x2 - x1:.6f} {y2 - y1:.6f}"


def build_feedback_zip() -> tuple[bytes, int]:
    detections = {m.item.detection for m in CorrectionMemory.objects.filter(status="approved").select_related(
        "item__detection__photo") if m.item.detection.photo and m.item.detection.photo.image}
    names: list[str] = []
    buf = io.BytesIO()
    n = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for det in sorted(detections, key=lambda d: d.id):
            lines = []
            for it in det.items.all():
                if it.feedback == DetectionItem.Feedback.WRONG:
                    label = it.corrected_label  # "" = not an object / unknown truth -> no box
                elif it.feedback == DetectionItem.Feedback.CORRECT or it.confidence >= KEEP_UNREVIEWED:
                    label = it.label
                else:
                    label = ""
                if not label or len(it.bbox) != 4:
                    continue
                if label not in names:
                    names.append(label)
                lines.append(_yolo_line(names.index(label), it.bbox))
            with det.photo.image.open("rb") as f:
                image = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
            image.thumbnail((MAX_SIDE, MAX_SIDE))
            img = io.BytesIO()
            image.save(img, "JPEG", quality=90)
            z.writestr(f"images/fb_{det.id}.jpg", img.getvalue())
            z.writestr(f"labels/fb_{det.id}.txt", "\n".join(lines) + ("\n" if lines else ""))
            n += 1
        z.writestr("names.txt", "\n".join(names) + "\n")
    return buf.getvalue(), n
