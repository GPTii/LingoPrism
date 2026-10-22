from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class Language(models.Model):
    """vi, en, zh-Hans (giản thể – đại lục), zh-Hant (phồn thể – Đài Loan)."""

    code = models.CharField(max_length=8, primary_key=True)
    name = models.CharField(max_length=60)
    native_name = models.CharField(max_length=60)
    tts_locale = models.CharField(max_length=10, help_text="vi-VN, en-US, zh-CN, zh-TW")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.code


class Audience(models.TextChoices):
    ALL = "all", "Tất cả"
    KID = "kid", "Trẻ em"
    ADULT = "adult", "Người lớn"


class Topic(TimeStampedModel):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Công khai"
        PRIVATE = "private", "Riêng tư"

    slug = models.SlugField(max_length=60, unique=True)
    name_vi = models.CharField(max_length=80)
    name_en = models.CharField(max_length=80, blank=True)
    name_zh_hans = models.CharField(max_length=40, blank=True)
    name_zh_hant = models.CharField(max_length=40, blank=True)
    icon = models.CharField(max_length=16, blank=True, help_text="Emoji")
    image = models.ImageField(upload_to="topics/", blank=True, null=True)
    audience = models.CharField(max_length=5, choices=Audience.choices, default=Audience.ALL)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="topics",
        help_text="Trống = chủ đề hệ thống",
    )
    visibility = models.CharField(max_length=7, choices=Visibility.choices, default=Visibility.PUBLIC)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name_vi"]

    def __str__(self):
        return self.name_vi

    @property
    def is_system(self):
        return self.owner_id is None


class Word(TimeStampedModel):
    """A vocabulary *concept* (e.g. "cat"), translated into every language."""

    class PartOfSpeech(models.TextChoices):
        NOUN = "noun", "Danh từ"
        VERB = "verb", "Động từ"
        ADJ = "adj", "Tính từ"
        ADV = "adv", "Trạng từ"
        PHRASE = "phrase", "Cụm từ"
        OTHER = "other", "Khác"

    slug = models.SlugField(max_length=80, unique=True)
    image = models.ImageField(upload_to="words/", blank=True, null=True)
    image_url = models.URLField(blank=True)
    image_credit = models.CharField(max_length=300, blank=True, help_text="Tác giả · giấy phép của ảnh (seed/concepts/images.csv)")
    levels = models.JSONField(default=dict, blank=True,
                              help_text='Cấp độ 1–4 theo ngôn ngữ học, VD {"en": 1, "zh": 2, "vi": 1} – seed/concepts/levels.csv')
    image_source = models.URLField(max_length=500, blank=True, help_text="Trang gốc của ảnh trên Wikimedia Commons")
    emoji = models.CharField(max_length=16, blank=True, help_text="Hình minh họa (emoji Unicode) cho trẻ em – seed/concepts/emoji.csv")
    yolo_label = models.CharField(max_length=60, blank=True, db_index=True, help_text="Tên lớp YOLOv10 tương ứng")
    part_of_speech = models.CharField(max_length=6, choices=PartOfSpeech.choices, default=PartOfSpeech.NOUN)
    difficulty = models.PositiveSmallIntegerField(default=1, help_text="1 (dễ) – 5 (khó)")
    audience = models.CharField(max_length=5, choices=Audience.choices, default=Audience.ALL)
    topics = models.ManyToManyField(Topic, through="TopicWord", related_name="words", blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return self.slug

    def save(self, *args, **kwargs):
        # every word sits on the 4-level path; a word added by hand starts at the level of its difficulty
        self.levels = {lang: (self.levels or {}).get(lang) or min(max(self.difficulty, 1), 4) for lang in ("en", "zh", "vi")}
        if kwargs.get("update_fields") is not None and "levels" not in kwargs["update_fields"]:
            kwargs["update_fields"] = [*kwargs["update_fields"], "levels"]
        super().save(*args, **kwargs)


class TopicWord(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("topic", "word")]
        ordering = ["order", "id"]


class ReviewStatus(models.TextChoices):
    DRAFT = "draft", "Nháp"
    VERIFIED = "verified", "Đã kiểm tra"
    FLAGGED = "flagged", "Cần xem lại"
    REJECTED = "rejected", "Loại bỏ"


class WordTranslation(TimeStampedModel):
    """The word in one language. Learners only ever see status = verified."""

    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="translations")
    language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name="translations")
    text = models.CharField(max_length=120)
    ipa = models.CharField(max_length=120, blank=True, help_text="Tiếng Anh – giọng Mỹ")
    pinyin = models.CharField(max_length=120, blank=True, help_text="Có dấu thanh, VD: mǎ líng shǔ")
    pinyin_numbered = models.CharField(max_length=120, blank=True, help_text="VD: ma3 ling2 shu3")
    zhuyin = models.CharField(max_length=120, blank=True)
    measure_word = models.CharField(max_length=20, blank=True, help_text="Lượng từ, VD 隻 / 只")
    accepted_variants = models.JSONField(default=list, blank=True, help_text="Dạng viết khác được chấp nhận khi chấm")
    regional_difference = models.BooleanField(default=False, help_text="Từ giản/phồn khác nhau theo vùng (VD 土豆/馬鈴薯)")
    meaning_vi = models.CharField(max_length=255, blank=True)
    meaning_en = models.CharField(max_length=255, blank=True)
    level = models.CharField(max_length=20, blank=True, help_text="HSK / TOCFL / CEFR")
    audio = models.FileField(upload_to="audio/", blank=True, null=True)

    status = models.CharField(max_length=8, choices=ReviewStatus.choices, default=ReviewStatus.DRAFT, db_index=True)
    sources = models.JSONField(default=dict, blank=True, help_text="Dữ liệu đối chiếu từ các nguồn")
    issues = models.JSONField(default=list, blank=True, help_text="Lỗi phát hiện bởi bộ kiểm tra tự động")
    verified_method = models.CharField(max_length=10, blank=True, help_text="auto | manual")
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = [("word", "language")]
        indexes = [models.Index(fields=["language", "text"])]

    def __str__(self):
        return f"{self.language_id}:{self.text}"

    def mark(self, status, method="auto", user=None):
        self.status = status
        self.verified_method = method if status == ReviewStatus.VERIFIED else ""
        self.verified_at = timezone.now() if status == ReviewStatus.VERIFIED else None
        self.verified_by = user if status == ReviewStatus.VERIFIED else None


class ExampleSentence(TimeStampedModel):
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="examples")
    language = models.ForeignKey(Language, on_delete=models.PROTECT)
    text = models.CharField(max_length=300)
    transliteration = models.CharField(max_length=400, blank=True, help_text="Pinyin của câu (nếu có)")
    translation_vi = models.CharField(max_length=300, blank=True)
    translation_en = models.CharField(max_length=300, blank=True)
    source = models.CharField(max_length=30, default="manual", help_text="tatoeba | manual")
    source_id = models.CharField(max_length=40, blank=True)
    license = models.CharField(max_length=40, blank=True)
    status = models.CharField(max_length=8, choices=ReviewStatus.choices, default=ReviewStatus.DRAFT, db_index=True)
    tokens = models.JSONField(default=list, blank=True,
                              help_text='Từ đã tách: [{"t": "我们", "p": "wǒ men", "z": "ㄨㄛˇ ˙ㄇㄣ"}, {"t": "。", "x": 1}]')
    target_tokens = models.JSONField(default=list, blank=True, help_text="Vị trí các token là từ vựng `word`")
    checks = models.JSONField(default=dict, blank=True, help_text="errors / warnings của bộ kiểm tra tự động")

    class Meta:
        ordering = ["id"]
        constraints = [models.UniqueConstraint(fields=["word", "language", "source", "source_id"],
                                               condition=~models.Q(source_id=""), name="uniq_example_source")]

    def __str__(self):
        return self.text


class ErrorReport(TimeStampedModel):
    class Reason(models.TextChoices):
        WRONG_CHARACTER = "wrong_character", "Sai mặt chữ"
        WRONG_PRONUNCIATION = "wrong_pronunciation", "Sai phiên âm / phát âm"
        WRONG_MEANING = "wrong_meaning", "Sai nghĩa"
        WRONG_EXAMPLE = "wrong_example", "Câu ví dụ sai"
        WRONG_IMAGE = "wrong_image", "Ảnh không đúng"
        OTHER = "other", "Khác"

    class Status(models.TextChoices):
        OPEN = "open", "Chờ xử lý"
        RESOLVED = "resolved", "Đã sửa"
        REJECTED = "rejected", "Không phải lỗi"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="error_reports")
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="error_reports")
    translation = models.ForeignKey(WordTranslation, null=True, blank=True, on_delete=models.CASCADE)
    example = models.ForeignKey(ExampleSentence, null=True, blank=True, on_delete=models.CASCADE)
    reason = models.CharField(max_length=24, choices=Reason.choices)
    details = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.OPEN, db_index=True)
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="handled_reports"
    )
    handled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class WordCandidate(TimeStampedModel):
    """A new word proposed from the HSK list (CC-CEDICT + Vietnamese Wiktionary), waiting for a teacher.

    Machine suggestions are often the wrong sense (打 → "dozen"), so nothing reaches learners before a person
    approves it – and approval still runs the same source checks as seed/concepts/words.csv."""

    class Status(models.TextChoices):
        PENDING = "pending", "Chờ duyệt"
        APPROVED = "approved", "Đã duyệt"
        REJECTED = "rejected", "Bỏ qua"

    zh_hans = models.CharField(max_length=40, unique=True)
    zh_hant = models.CharField(max_length=40)
    pinyin = models.CharField(max_length=120, blank=True)
    hsk_level = models.PositiveSmallIntegerField(db_index=True)
    glosses = models.JSONField(default=list, help_text="Nghĩa tiếng Anh trong CC-CEDICT")
    en = models.CharField(max_length=80, blank=True)
    vi = models.CharField(max_length=80, blank=True)
    vi_options = models.JSONField(default=list, help_text="Gợi ý nghĩa Việt (Wiktionary tiếng Việt)")
    part_of_speech = models.CharField(max_length=6, default="noun")
    topics = models.CharField(max_length=120, blank=True, help_text="slug chủ đề, phân cách bằng |")
    audience = models.CharField(max_length=5, default="all")
    confidence = models.CharField(max_length=6, default="low", help_text="high = nghĩa chính khớp cả 3 chiều")
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING, db_index=True)
    checks = models.JSONField(default=dict, blank=True, help_text="Kết quả kiểm tra nguồn lần gần nhất")
    note = models.CharField(max_length=300, blank=True)
    word = models.ForeignKey(Word, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["hsk_level", "-confidence", "id"]

    def __str__(self):
        return f"{self.zh_hans} ({self.status})"
