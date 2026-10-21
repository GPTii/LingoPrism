from django.apps import AppConfig


class PushConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.push"
    verbose_name = "Thông báo đẩy (FCM)"

    def ready(self):
        from . import signals  # noqa: F401  (connects the sender to new notifications)
