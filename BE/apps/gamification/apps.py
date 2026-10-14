from django.apps import AppConfig


class GamificationConfig(AppConfig):
    name = "apps.gamification"
    label = "gamification"
    verbose_name = "Game hóa"

    def ready(self):
        from . import receivers  # noqa: F401
