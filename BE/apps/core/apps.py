from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "apps.core"
    label = "core"

    def ready(self):
        from django.db.models.signals import post_delete, pre_save
        from PIL import Image

        from apps.accounts.models import User
        from apps.community.models import Post
        from apps.detection.models import CorrectionMemory, Photo

        from .images import MAX_PIXELS, delete_files_with, sanitize_fields

        Image.MAX_IMAGE_PIXELS = MAX_PIXELS
        # images uploaded by users: strip EXIF (GPS), random name, re-encode (apps/core/images.py)
        pre_save.connect(sanitize_fields("image"), sender=Photo, weak=False, dispatch_uid="sanitize-photo")
        pre_save.connect(sanitize_fields("image"), sender=Post, weak=False, dispatch_uid="sanitize-post")
        pre_save.connect(sanitize_fields("avatar"), sender=User, weak=False, dispatch_uid="sanitize-avatar")
        # and their files go with them (deleting a photo, a post or a whole account)
        post_delete.connect(delete_files_with("image"), sender=Photo, weak=False, dispatch_uid="files-photo")
        post_delete.connect(delete_files_with("image"), sender=Post, weak=False, dispatch_uid="files-post")
        post_delete.connect(delete_files_with("avatar"), sender=User, weak=False, dispatch_uid="files-avatar")
        post_delete.connect(delete_files_with("crop"), sender=CorrectionMemory, weak=False, dispatch_uid="files-crop")
