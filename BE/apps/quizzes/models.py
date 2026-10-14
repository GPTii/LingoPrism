from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.vocab.models import Language, Topic, Word


class Question(TimeStampedModel):
    class Kind(models.TextChoices):
        MCQ = "mcq", "Trắc nghiệm"
        FILL = "fill", "Điền từ"
        ESSAY = "essay", "Tự luận"

    kind = models.CharField(max_length=5, choices=Kind.choices)
    language = models.ForeignKey(Language, on_delete=models.PROTECT, help_text="Ngôn ngữ của câu hỏi (vi, en, zh-Hans, zh-Hant)")
    topic = models.ForeignKey(Topic, null=True, blank=True, on_delete=models.SET_NULL)
    word = models.ForeignKey(Word, null=True, blank=True, on_delete=models.SET_NULL)
    prompt = models.TextField()
    image_url = models.CharField(max_length=300, blank=True)
    options = models.JSONField(default=list, blank=True, help_text='MCQ: [{"text": "...", "correct": true}, ...]')
    accepted_answers = models.JSONField(default=list, blank=True, help_text="Điền từ: các đáp án đúng")
    explanation = models.TextField(blank=True)
    difficulty = models.PositiveSmallIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.prompt[:60]


class Exam(TimeStampedModel):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    language = models.ForeignKey(Language, on_delete=models.PROTECT)
    topic = models.ForeignKey(Topic, null=True, blank=True, on_delete=models.SET_NULL)
    audience = models.CharField(max_length=5, default="all", help_text="all | kid | adult")
    time_limit_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    pass_percent = models.PositiveSmallIntegerField(default=60)
    is_published = models.BooleanField(default=False)
    questions = models.ManyToManyField(Question, through="ExamQuestion", related_name="exams")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ExamQuestion(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="exam_questions")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0)
    points = models.DecimalField(max_digits=5, decimal_places=2, default=1)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("exam", "question")]


class Submission(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "Đang làm"
        SUBMITTED = "submitted", "Chờ chấm tự luận"
        GRADED = "graded", "Đã chấm"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="submissions")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.IN_PROGRESS, db_index=True)
    started_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="graded_submissions")
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    @property
    def percent(self):
        return round(float(self.score) / float(self.max_score) * 100, 1) if self.max_score else 0


class Answer(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="answers")
    exam_question = models.ForeignKey(ExamQuestion, on_delete=models.CASCADE)
    selected_option = models.SmallIntegerField(null=True, blank=True)
    text = models.TextField(blank=True)
    is_correct = models.BooleanField(null=True, help_text="Trống = chờ chấm tay")
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)

    class Meta:
        unique_together = [("submission", "exam_question")]
