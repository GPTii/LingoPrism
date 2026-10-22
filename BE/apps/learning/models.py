from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.vocab.models import ExampleSentence, Topic, Word

from .scheduling import CardState


class LearningLanguage(models.TextChoices):
    VI = "vi", "Tiếng Việt"
    EN = "en", "Tiếng Anh"
    ZH = "zh", "Tiếng Trung"


class PersonalWord(TimeStampedModel):
    """A word in a learner's library, with its spaced-repetition state (per language)."""

    class Status(models.TextChoices):
        NEW = "new", "Chưa học"
        LEARNING = "learning", "Đang học"
        MASTERED = "mastered", "Đã thuộc"

    class Source(models.TextChoices):
        TOPIC = "topic", "Chủ đề"
        CAMERA = "camera", "Nhận diện ảnh"
        MANUAL = "manual", "Tự thêm"
        COMMUNITY = "community", "Cộng đồng"
        LOCATION = "location", "Gợi ý theo vị trí"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="personal_words")
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="learners")
    language = models.CharField(max_length=2, choices=LearningLanguage.choices)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.NEW, db_index=True)
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.TOPIC)
    topic = models.ForeignKey(Topic, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    source_ref = models.CharField(max_length=64, blank=True, help_text="VD id ảnh nhận diện / bài đăng")

    # spaced repetition state
    stage = models.PositiveSmallIntegerField(default=0)
    ease = models.FloatField(default=2.5)
    interval_days = models.PositiveIntegerField(default=0)
    repetitions = models.PositiveIntegerField(default=0)
    lapses = models.PositiveIntegerField(default=0)
    wrong_streak = models.PositiveIntegerField(default=0)
    fsrs_difficulty = models.FloatField(default=0, help_text="FSRS D (1–10)")
    fsrs_stability = models.FloatField(default=0, help_text="FSRS S (ngày)")
    due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    first_learned_at = models.DateTimeField(null=True, blank=True)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("user", "word", "language")]
        indexes = [models.Index(fields=["user", "language", "due_at"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id}:{self.word_id}:{self.language}"

    @property
    def state(self) -> CardState:
        return CardState(self.stage, self.ease, self.interval_days, self.repetitions, self.lapses, self.wrong_streak,
                         self.fsrs_difficulty, self.fsrs_stability)

    def apply_state(self, state: CardState, due_at):
        self.stage, self.ease, self.interval_days = state.stage, state.ease, state.interval_days
        self.repetitions, self.lapses, self.wrong_streak = state.repetitions, state.lapses, state.wrong_streak
        self.fsrs_difficulty, self.fsrs_stability = state.difficulty, state.stability
        self.due_at = due_at
        now = timezone.now()
        self.last_reviewed_at = now
        self.first_learned_at = self.first_learned_at or now
        self.status = self.Status.MASTERED if state.stage >= 2 else self.Status.LEARNING


class StudySession(TimeStampedModel):
    class Kind(models.TextChoices):
        LEARN = "learn", "Học từ mới"
        REVIEW = "review", "Ôn tập"
        PRACTICE = "practice", "Luyện tập chủ đề"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="study_sessions")
    language = models.CharField(max_length=2, choices=LearningLanguage.choices)
    script = models.CharField(max_length=4, blank=True, help_text="hans | hant khi học tiếng Trung")
    kind = models.CharField(max_length=8, choices=Kind.choices)
    topic = models.ForeignKey(Topic, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    scheduler = models.CharField(max_length=20, default="leitner")
    planned_count = models.PositiveSmallIntegerField(default=0)
    completed_count = models.PositiveSmallIntegerField(default=0)
    correct_first_try = models.PositiveSmallIntegerField(default=0)
    xp_earned = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]


class SessionItem(models.Model):
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name="items")
    personal_word = models.ForeignKey(PersonalWord, on_delete=models.CASCADE, related_name="+")
    order = models.PositiveSmallIntegerField(default=0)
    answered = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]
        unique_together = [("session", "personal_word")]


class ReviewLog(models.Model):
    """One answer of a learner — the raw data for SM-2 / FSRS / GA experiments (Phase 5)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_logs")
    personal_word = models.ForeignKey(PersonalWord, on_delete=models.CASCADE, related_name="logs")
    session = models.ForeignKey(StudySession, null=True, blank=True, on_delete=models.SET_NULL, related_name="logs")
    language = models.CharField(max_length=2, choices=LearningLanguage.choices)
    script = models.CharField(max_length=4, blank=True)
    question_type = models.CharField(max_length=30)
    correct = models.BooleanField()
    first_try = models.BooleanField(default=True)
    rating = models.PositiveSmallIntegerField(default=0, help_text="0–5 (SM-2 quality)")
    response_ms = models.PositiveIntegerField(null=True, blank=True)
    answer = models.CharField(max_length=200, blank=True)
    scheduler = models.CharField(max_length=20)
    state_before = models.JSONField(default=dict)
    state_after = models.JSONField(default=dict)
    elapsed_days = models.FloatField(null=True, blank=True, help_text="Số ngày kể từ lần ôn trước")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "created_at"])]


class SentenceAttempt(models.Model):
    """One answer to a sentence exercise (arrange / listen / fill / meaning) – data for later analysis."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sentence_attempts")
    sentence = models.ForeignKey(ExampleSentence, on_delete=models.CASCADE, related_name="attempts")
    language = models.CharField(max_length=2, choices=LearningLanguage.choices)
    script = models.CharField(max_length=4, blank=True)
    exercise = models.CharField(max_length=10)
    correct = models.BooleanField()
    answer = models.CharField(max_length=300, blank=True)
    response_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]


class LearnerLevel(TimeStampedModel):
    """Where a learner is on the 4-level path of one language (levels of the words: Word.levels)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="levels")
    language = models.CharField(max_length=5, choices=LearningLanguage.choices)
    current = models.PositiveSmallIntegerField(default=1, help_text="Cấp đang học (người học tự chọn trong các cấp đã mở)")
    passed_test = models.PositiveSmallIntegerField(default=1, help_text="Cấp cao nhất đã mở nhờ bài kiểm tra vượt cấp")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "language"], name="uniq_learner_level")]

    def __str__(self):
        return f"{self.user_id} {self.language} cấp {self.current}"
