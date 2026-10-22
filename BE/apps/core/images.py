"""Sanitise images users upload, before they are written to MEDIA_ROOT (served publicly by nginx under /media/).

* EXIF is dropped: phone photos carry the GPS position of where they were taken (often the learner's home,
  and some learners are children); orientation is applied to the pixels first so nothing turns sideways.
* the file gets a random name: "IMG_1234.jpg" style names make other people's photos guessable.
* the image is re-encoded and downscaled: a crafted file cannot smuggle anything else, and storage stays bounded.
* decompression bombs (a small file declaring 100 000 x 100 000 px) are refused: Image.MAX_IMAGE_PIXELS.
"""
import io
import uuid

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

MAX_PIXELS = 60_000_000  # PIL raises DecompressionBombError above 2x this (warning above 1x)
MAX_SIDE = {"avatar": 1024}
DEFAULT_MAX_SIDE = 2048


def sanitize(fieldfile, max_side: int = DEFAULT_MAX_SIDE):
    """Re-encode a newly assigned (not yet saved) ImageField file in place."""
    if not fieldfile or getattr(fieldfile, "_committed", True):
        return
    f = fieldfile.file
    f.seek(0)
    try:
        with Image.open(f) as im:
            if im.width * im.height > MAX_PIXELS:
                raise ValidationError("Ảnh quá lớn")
            im = ImageOps.exif_transpose(im)
            has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
            im = im.convert("RGBA" if has_alpha else "RGB")
            im.thumbnail((max_side, max_side))
            out = io.BytesIO()
            if has_alpha:
                im.save(out, "PNG", optimize=True)  # no exif/pnginfo passed -> metadata dropped
                ext = "png"
            else:
                im.save(out, "JPEG", quality=88)
                ext = "jpg"
    except (Image.DecompressionBombError, OSError) as e:
        raise ValidationError("Ảnh không hợp lệ") from e
    name = f"{uuid.uuid4().hex}.{ext}"
    fieldfile.file = ContentFile(out.getvalue(), name=name)
    fieldfile.name = name


def sanitize_fields(*fields):
    """pre_save receiver sanitising the given ImageFields of the instance."""

    def receiver(sender, instance, **kwargs):
        for field in fields:
            sanitize(getattr(instance, field), MAX_SIDE.get(field, DEFAULT_MAX_SIDE))

    return receiver
