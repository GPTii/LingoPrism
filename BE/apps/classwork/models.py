"""Assignments inside a study group (bài tập trong nhóm).

No teacher role: the group's leaders (its creator and the members it promotes) give the work and mark it, the other
members do it. An assignment is either questions (multiple choice, fill-in, written answer, file to hand in), or only
instructions + an attached file (a worksheet), answered with text and / or a file.
"""

import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


def upload_to(instance, filename: str) -> str:
    """A random name: the files are served from /media, so the path must not be guessable."""
    return f"classwork/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{Path(filename).suffix.lower()[:8]}"


class Assignment(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Bản nháp"
        PUBLISHED = "published", "Đã giao"
        CLOSED = "closed", "Đã đóng"

    group = models.ForeignKey("community.Group", on_delete=models.CASCADE, related_name="assignments")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    title = models.CharField(max_length=150)
    instructions = models.TextField(blank=True)
    attachment = models.FileField(upload_to=upload_to, blank=True)
    attachment_name = models.CharField(max_length=200, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=9, choices=Status.choices, default=Status.DRAFT, db_index=True)
    points = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=10,
        help_text="Điểm tối đa khi bài không có câu hỏi (chỉ nộp bài làm / file)",
    )
    allow_late = models.BooleanField(default=True, help_text="Cho nộp sau hạn (đánh dấu nộp muộn)")
    show_answers = models.BooleanField(default=True, help_text="Cho xem đáp án đúng sau khi đã chấm")
    ai_generated = models.BooleanField(default=False, help_text="Câu hỏi do AI tách từ file")
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def max_score(self):
        qs = list(self.questions.all())
        return sum((q.points for q in qs), 0) if qs else self.points


class AssignmentQuestion(models.Model):
    class Kind(models.TextChoices):
        MCQ = "mcq", "Trắc nghiệm"
        FILL = "fill", "Điền từ"
        ESSAY = "essay", "Tự luận"
        FILE = "file", "Nộp file"

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="questions")
    order = models.PositiveSmallIntegerField(default=0)
    kind = models.CharField(max_length=5, choices=Kind.choices)
    prompt = models.TextField()
    options = models.JSONField(default=list, blank=True, help_text='Trắc nghiệm: [{"text": "...", "correct": true}]')
    accepted_answers = models.JSONField(default=list, blank=True, help_text="Điền từ: các đáp án đúng")
    points = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    explanation = models.TextField(blank=True)

    class Meta:
        ordering = ["order", "id"]

    @property
    def auto_graded(self) -> bool:
        return self.kind in (self.Kind.MCQ, self.Kind.FILL)


class AssignmentSubmission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Chờ chấm"
        GRADED = "graded", "Đã chấm"

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignment_submissions")
    status = models.CharField(max_length=9, choices=Status.choices, default=Status.SUBMITTED, db_index=True)
    submitted_at = models.DateTimeField(default=timezone.now)
    late = models.BooleanField(default=False)
    text = models.TextField(blank=True, help_text="Bài làm (bài không có câu hỏi)")
    attachment = models.FileField(upload_to=upload_to, blank=True)
    attachment_name = models.CharField(max_length=200, blank=True)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]
        constraints = [models.UniqueConstraint(fields=["assignment", "user"], name="one_submission_per_member")]

    @property
    def percent(self):
        return (
            round(float(self.score) / float(self.max_score) * 100, 1)
            if self.max_score and self.score is not None
            else None
        )


class AssignmentAnswer(models.Model):
    submission = models.ForeignKey(AssignmentSubmission, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(AssignmentQuestion, on_delete=models.CASCADE, related_name="answers")
    selected_option = models.SmallIntegerField(null=True, blank=True)
    text = models.TextField(blank=True)
    attachment = models.FileField(upload_to=upload_to, blank=True)
    attachment_name = models.CharField(max_length=200, blank=True)
    is_correct = models.BooleanField(null=True, help_text="Trống = chờ chấm tay")
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["submission", "question"], name="one_answer_per_question")]
