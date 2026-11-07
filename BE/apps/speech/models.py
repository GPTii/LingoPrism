from django.conf import settings
from django.db import models
from django.utils import timezone


class PronunciationAttempt(models.Model):
    """One recording scored phone by phone (apps.speech.assess). The recording itself is not kept."""

    class Kind(models.TextChoices):
        WORD = "word", "Từ"
        SENTENCE = "sentence", "Câu"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pronunciation_attempts")
    language = models.CharField(max_length=8, help_text="en | vi | zh-Hans | zh-Hant")
    kind = models.CharField(max_length=8, choices=Kind.choices)
    translation = models.ForeignKey(
        "vocab.WordTranslation", null=True, blank=True, on_delete=models.SET_NULL, related_name="pronunciation_attempts"
    )
    sentence = models.ForeignKey(
        "vocab.ExampleSentence", null=True, blank=True, on_delete=models.SET_NULL, related_name="pronunciation_attempts"
    )
    text = models.CharField(max_length=300)
    score = models.PositiveSmallIntegerField()
    phone_score = models.PositiveSmallIntegerField()
    tone_score = models.PositiveSmallIntegerField(null=True, blank=True)
    completeness = models.PositiveSmallIntegerField()
    heard_ipa = models.CharField(max_length=500, blank=True)
    error_codes = models.JSONField(default=list, blank=True, help_text="Mã lỗi (tips.py) – thống kê âm hay sai")
    result = models.JSONField(default=dict, help_text="Kết quả đầy đủ: từng âm tiết, từng âm, mẹo sửa")
    ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "language", "-created_at"])]

    def __str__(self):
        return f"{self.user_id} {self.text} {self.score}"
