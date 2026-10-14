from django.contrib import admin

from .models import PersonalWord, ReviewLog, StudySession


@admin.register(PersonalWord)
class PersonalWordAdmin(admin.ModelAdmin):
    list_display = ["user", "word", "language", "status", "stage", "due_at"]
    list_filter = ["language", "status", "source"]


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ["user", "kind", "language", "planned_count", "completed_count", "started_at", "ended_at"]


@admin.register(ReviewLog)
class ReviewLogAdmin(admin.ModelAdmin):
    list_display = ["user", "personal_word", "question_type", "correct", "rating", "created_at"]
    list_filter = ["question_type", "correct", "language"]
