from django.conf import settings
from django.db import models
from django.utils import timezone


class LiteracyProgress(models.Model):
    """Best result of a child on one lesson of the reading – writing course."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="literacy_progress")
    lesson = models.PositiveSmallIntegerField()
    best_percent = models.PositiveSmallIntegerField(default=0)
    stars = models.PositiveSmallIntegerField(default=0, help_text="0–3")
    times_completed = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("user", "lesson")]
        ordering = ["lesson"]


class LiteracyAttempt(models.Model):
    """One answer – data for analysing which sounds / rhymes / tones children confuse."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="literacy_attempts")
    session = models.CharField(max_length=16, db_index=True)
    lesson = models.PositiveSmallIntegerField()
    unit = models.CharField(max_length=20, help_text="am:b | thanh:huyen | van:an | review")
    exercise = models.CharField(max_length=16)
    index = models.PositiveSmallIntegerField(default=0)
    correct = models.BooleanField()
    expected = models.CharField(max_length=200)
    answer = models.CharField(max_length=200, blank=True)
    response_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
