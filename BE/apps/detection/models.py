from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.vocab.models import Word


class ModelVersion(models.Model):
    name = models.CharField(max_length=60, unique=True, help_text="VD yolov10n-lingoprism-v1")
    file = models.CharField(max_length=300, help_text="Đường dẫn file .onnx trên server")
    classes = models.JSONField(default=list, help_text="Danh sách nhãn theo thứ tự lớp")
    input_size = models.PositiveSmallIntegerField(default=640)
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    map50 = models.FloatField(null=True, blank=True)
    map50_95 = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class Photo(models.Model):
    class Source(models.TextChoices):
        CAMERA = "camera", "Camera"
        GALLERY = "gallery", "Thư viện ảnh"
        WEB = "web", "Upload từ web"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="photos/%Y/%m/", null=True, blank=True)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    source = models.CharField(max_length=7, choices=Source.choices, default=Source.CAMERA)
    created_at = models.DateTimeField(default=timezone.now)


class Detection(models.Model):
    class Device(models.TextChoices):
        SERVER = "server", "Server (ONNX)"
        ON_DEVICE = "on_device", "Trên điện thoại (TFLite)"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="detections")
    photo = models.ForeignKey(Photo, null=True, blank=True, on_delete=models.SET_NULL, related_name="detections")
    model_version = models.ForeignKey(ModelVersion, null=True, blank=True, on_delete=models.SET_NULL)
    model_name = models.CharField(max_length=60)
    device = models.CharField(max_length=9, choices=Device.choices)
    inference_ms = models.PositiveIntegerField(null=True, blank=True)
    confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]


class DetectionItem(models.Model):
    """One detected object – confidence, top-k alternatives and user feedback feed the VIP algorithm (Phase 5)."""

    class Feedback(models.TextChoices):
        UNKNOWN = "unknown", "Chưa xác nhận"
        CORRECT = "correct", "Đúng"
        WRONG = "wrong", "Sai"

    detection = models.ForeignKey(Detection, on_delete=models.CASCADE, related_name="items")
    label = models.CharField(max_length=60, db_index=True)
    confidence = models.FloatField()
    bbox = models.JSONField(default=list, help_text="[x1, y1, x2, y2] chuẩn hoá 0–1")
    top_k = models.JSONField(default=list, help_text='[{"label": "...", "confidence": 0.31}, ...]')
    word = models.ForeignKey(Word, null=True, blank=True, on_delete=models.SET_NULL)
    selected = models.BooleanField(default=False)
    feedback = models.CharField(max_length=7, choices=Feedback.choices, default=Feedback.UNKNOWN)
    corrected_label = models.CharField(max_length=60, blank=True, help_text="Nhãn đúng do người dùng chọn khi sai")

    class Meta:
        ordering = ["-confidence"]
