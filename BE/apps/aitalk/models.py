from django.conf import settings
from django.db import models
from django.utils import timezone


class PhotoDialogue(models.Model):
    """A short practice dialogue written by an AI model around the words of one photo.

    AI-made text: shown with an "AI tạo" label, never copied into the verified vocabulary. Kept so that
    opening the same photo again costs nothing."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="photo_dialogues")
    detection = models.ForeignKey("detection.Detection", on_delete=models.CASCADE, related_name="dialogues")
    language = models.CharField(max_length=8, help_text="en | zh-Hans | zh-Hant | vi")
    words = models.JSONField(default=list, help_text="Các từ đã kiểm duyệt đưa cho AI")
    title_vi = models.CharField(max_length=200, blank=True)
    lines = models.JSONField(default=list, help_text='[{"speaker": "A", "text": "...", "reading": "...", "translation": "..."}]')
    model_name = models.CharField(max_length=60)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["detection", "language"], name="one_dialogue_per_photo_language")]
