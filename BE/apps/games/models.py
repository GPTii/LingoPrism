from django.conf import settings
from django.db import models


class GameNode(models.Model):
    """A learner's result on one stop of the game map: a round, a chest or a level's boss round.

    Progress is kept per language and track (words: the vocabulary path; reading: the reading course for children
    learning Vietnamese), so a learner of English and Chinese has two maps."""

    class Track(models.TextChoices):
        WORDS = "words", "Từ vựng"
        READING = "reading", "Học đọc"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="game_nodes")
    language = models.CharField(max_length=2)
    track = models.CharField(max_length=8, choices=Track.choices)
    node = models.CharField(max_length=16, help_text="L1-r3 (vòng) | L1-c1 (rương) | L1-boss")
    stars = models.PositiveSmallIntegerField(default=0, help_text="0–3, kết quả tốt nhất")
    best_percent = models.PositiveSmallIntegerField(default=0)
    plays = models.PositiveIntegerField(default=0)
    passed_at = models.DateTimeField(null=True, blank=True, help_text="Lần đầu qua màn / mở rương")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "language", "track", "node"], name="uniq_game_node")]

    def __str__(self):
        return f"{self.user_id} {self.language}/{self.track} {self.node}"
