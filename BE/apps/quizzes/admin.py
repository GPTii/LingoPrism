from django.contrib import admin

from .models import Answer, Exam, ExamQuestion, Question, Submission


class ExamQuestionInline(admin.TabularInline):
    model = ExamQuestion
    extra = 0


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ["title", "language", "is_published", "created_at"]
    inlines = [ExamQuestionInline]


admin.site.register(Question)
admin.site.register(Submission)
admin.site.register(Answer)
