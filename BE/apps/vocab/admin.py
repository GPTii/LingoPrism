from django.contrib import admin

from .models import ErrorReport, ExampleSentence, Language, Topic, TopicWord, Word, WordTranslation


class TranslationInline(admin.TabularInline):
    model = WordTranslation
    extra = 0
    fields = ["language", "text", "ipa", "pinyin", "zhuyin", "measure_word", "status"]


class TopicWordInline(admin.TabularInline):
    model = TopicWord
    extra = 0


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ["slug", "yolo_label", "part_of_speech", "audience", "difficulty"]
    search_fields = ["slug", "yolo_label", "translations__text"]
    list_filter = ["audience", "part_of_speech", "topics"]
    inlines = [TranslationInline, TopicWordInline]


@admin.register(WordTranslation)
class WordTranslationAdmin(admin.ModelAdmin):
    list_display = ["word", "language", "text", "pinyin", "status", "verified_method"]
    list_filter = ["language", "status", "regional_difference"]
    search_fields = ["text", "word__slug"]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["slug", "name_vi", "audience", "owner", "order"]
    list_filter = ["audience", "visibility"]


admin.site.register(Language)
admin.site.register(ExampleSentence)
admin.site.register(ErrorReport)
