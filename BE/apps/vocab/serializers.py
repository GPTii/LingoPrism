from rest_framework import serializers

from .models import ErrorReport, ExampleSentence, Language, Topic, Word, WordTranslation


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["code", "name", "native_name", "tts_locale"]


class TopicSerializer(serializers.ModelSerializer):
    is_system = serializers.BooleanField(read_only=True)
    word_count = serializers.IntegerField(read_only=True, default=0)
    learned_count = serializers.IntegerField(read_only=True, default=0)
    saved_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Topic
        fields = [
            "id", "slug", "name_vi", "name_en", "name_zh_hans", "name_zh_hant", "icon", "image",
            "audience", "visibility", "is_system", "word_count", "learned_count", "saved_count", "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at"]


class TopicCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "name_vi", "icon", "visibility"]


class ErrorReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErrorReport
        fields = ["id", "word", "translation", "example", "reason", "details", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def validate(self, attrs):
        tr, word = attrs.get("translation"), attrs["word"]
        if tr and tr.word_id != word.id:
            raise serializers.ValidationError("Bản dịch không thuộc từ này")
        return attrs


# ------------------------------------------------------------------ admin

class AdminTranslationSerializer(serializers.ModelSerializer):
    word_slug = serializers.CharField(source="word.slug", read_only=True)

    class Meta:
        model = WordTranslation
        fields = [
            "id", "word", "word_slug", "language", "text", "ipa", "pinyin", "pinyin_numbered", "zhuyin",
            "measure_word", "accepted_variants", "regional_difference", "meaning_vi", "meaning_en", "level",
            "status", "issues", "sources", "verified_method", "verified_at", "verified_by", "updated_at",
        ]
        read_only_fields = ["id", "word_slug", "issues", "sources", "verified_method", "verified_at", "verified_by", "updated_at"]


class AdminExampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExampleSentence
        fields = ["id", "word", "language", "text", "transliteration", "translation_vi", "translation_en",
                  "source", "source_id", "license", "status"]


class AdminWordSerializer(serializers.ModelSerializer):
    translations = AdminTranslationSerializer(many=True, read_only=True)
    topics = serializers.PrimaryKeyRelatedField(many=True, queryset=Topic.objects.all(), required=False)
    flagged_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Word
        fields = ["id", "slug", "image", "image_url", "yolo_label", "part_of_speech", "difficulty", "audience",
                  "topics", "translations", "flagged_count", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated):
        topics = validated.pop("topics", [])
        word = super().create(validated)
        word.topics.set(topics)
        return word

    def update(self, instance, validated):
        topics = validated.pop("topics", None)
        word = super().update(instance, validated)
        if topics is not None:
            word.topics.set(topics)
        return word


class AdminErrorReportSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    word_slug = serializers.CharField(source="word.slug", read_only=True)
    translation_text = serializers.CharField(source="translation.text", read_only=True, default=None)

    class Meta:
        model = ErrorReport
        fields = ["id", "user_email", "word", "word_slug", "translation", "translation_text", "example",
                  "reason", "details", "status", "handled_by", "handled_at", "created_at"]
        read_only_fields = ["id", "user_email", "word", "word_slug", "translation", "translation_text", "example",
                            "reason", "details", "handled_by", "handled_at", "created_at"]
