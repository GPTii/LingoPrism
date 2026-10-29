"""Approved error reports -> YOLO training data for the next run (merged by AI/scripts/merge_feedback.py).

One image per reported photo with every object of that photo:
  * the object a learner corrected            -> the corrected label
  * an object reported as "not an object"     -> no box (background, which is the truth)
  * an object confirmed correct               -> its label
  * an object nobody gave feedback on         -> kept when the detector was fairly sure (>= KEEP_UNREVIEWED),
                                                 otherwise the photo would teach "this is background"
Labels are written by name (names.txt), so the zip does not depend on the class order of any model. A name may be a
class the detector does not have yet: the learner typed the object's Vietnamese name and picked a word without a
yolo_label, so the label is the word's slug – merge_feedback.py adds such classes with --add-classes.

A photo with an object the detector missed (the learner added it by name, no box) is not a YOLO image: its unboxed
object would be learnt as background. It goes to missed/ with missed.csv (file, label, typed name), to be boxed by
hand (e.g. in Label Studio) before training.
"""
import csv
import io
import zipfile

from PIL import Image, ImageOps

from .models import CorrectionMemory, DetectionItem

KEEP_UNREVIEWED = 0.5
MAX_SIDE = 640


def _yolo_line(index: int, bbox) -> str:
    x1, y1, x2, y2 = bbox
    return f"{index} {(x1 + x2) / 2:.6f} {(y1 + y2) / 2:.6f} {x2 - x1:.6f} {y2 - y1:.6f}"


def _jpeg(photo) -> bytes:
    with photo.image.open("rb") as f:
        image = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
    image.thumbnail((MAX_SIDE, MAX_SIDE))
    out = io.BytesIO()
    image.save(out, "JPEG", quality=90)
    return out.getvalue()


def build_feedback_zip() -> tuple[bytes, int]:
    detections = {m.item.detection for m in CorrectionMemory.objects.filter(status="approved").select_related(
        "item__detection__photo") if m.item.detection.photo and m.item.detection.photo.image}
    missed = list(DetectionItem.objects.filter(manual=True, detection__photo__isnull=False).exclude(
        detection__photo__image="").select_related("detection__photo").order_by("detection_id", "id"))
    with_missed = {it.detection_id for it in missed}
    names: list[str] = []
    buf = io.BytesIO()
    n = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for det in sorted(detections, key=lambda d: d.id):
            if det.id in with_missed:
                continue  # an object without a box: goes to missed/ below
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
            z.writestr(f"images/fb_{det.id}.jpg", _jpeg(det.photo))
            z.writestr(f"labels/fb_{det.id}.txt", "\n".join(lines) + ("\n" if lines else ""))
            n += 1
        z.writestr("names.txt", "\n".join(names) + "\n")
        if missed:
            table = io.StringIO()
            rows = csv.writer(table)
            rows.writerow(["file", "label", "typed"])
            written = set()
            for it in missed:
                name = f"missed/fb_{it.detection_id}.jpg"
                if it.detection_id not in written:
                    z.writestr(name, _jpeg(it.detection.photo))
                    written.add(it.detection_id)
                rows.writerow([name, it.label, it.corrected_text])
            z.writestr("missed.csv", table.getvalue())
            n += len(written)
    return buf.getvalue(), n
