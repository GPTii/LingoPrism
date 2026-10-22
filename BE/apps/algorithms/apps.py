from django.apps import AppConfig


class AlgorithmsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.algorithms"
    verbose_name = "Thuật toán nghiên cứu (SM-2, FSRS, VIP, Smart Distractor, Proximity, GA)"

    def ready(self):
        from django.db.models.signals import post_delete, post_save

        from apps.gis.models import Poi

        from .proximity import invalidate

        post_save.connect(invalidate, sender=Poi, dispatch_uid="poi-grid-save")
        post_delete.connect(invalidate, sender=Poi, dispatch_uid="poi-grid-delete")
