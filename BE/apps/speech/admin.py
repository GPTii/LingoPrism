from django.contrib import admin

from .models import PronunciationAttempt


@admin.register(PronunciationAttempt)
class PronunciationAttemptAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "language", "kind", "text", "score", "phone_score", "tone_score", "ms")
    list_filter = ("language", "kind")
    search_fields = ("text", "user__email")
    readonly_fields = [f.name for f in PronunciationAttempt._meta.fields]
