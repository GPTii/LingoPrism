from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "apps.core"
    label = "core"

    def ready(self):
        from django.db.models.signals import pre_save
        from PIL import Image

        from apps.accounts.models import User
        from apps.community.models import Post
        from apps.detection.models import Photo

        from .images import MAX_PIXELS, sanitize_fields

        Image.MAX_IMAGE_PIXELS = MAX_PIXELS
        # images uploaded by users: strip EXIF (GPS), random name, re-encode (apps/core/images.py)
        pre_save.connect(sanitize_fields("image"), sender=Photo, weak=False, dispatch_uid="sanitize-photo")
        pre_save.connect(sanitize_fields("image"), sender=Post, weak=False, dispatch_uid="sanitize-post")
        pre_save.connect(sanitize_fields("avatar"), sender=User, weak=False, dispatch_uid="sanitize-avatar")
