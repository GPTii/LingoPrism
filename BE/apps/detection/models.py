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
    corrected_label = models.CharField(max_length=80, blank=True, help_text="Nhãn đúng do người dùng chọn khi sai")
    corrected_word = models.ForeignKey(Word, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
                                       help_text="Từ người dùng chọn sau khi gõ tên tiếng Việt")
    corrected_text = models.CharField(max_length=80, blank=True, help_text="Tên tiếng Việt người dùng gõ")
    manual = models.BooleanField(default=False, help_text="Đồ vật model bỏ sót, người dùng tự thêm (không có khung)")

    class Meta:
        ordering = ["-confidence"]
    learned_from = models.ForeignKey("CorrectionMemory", null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name="applied", help_text="Nhãn đã được sửa tự động theo báo lỗi trước đó")


class CorrectionMemory(models.Model):
    """A detection error reported by a learner, remembered by what the object looks like (image embedding).

    The next time the detector makes the same mistake on a similar-looking object, the server answers with the
    corrected word instead – no retraining. A report applies to its reporter at once and to everyone once approved
    (CONSENSUS_USERS learners reported the same mistake, or staff approved it). Approved reports are exported as
    training data for the next YOLO run (AI/scripts/merge_feedback.py)."""

    class Status(models.TextChoices):
        PENDING = "pending", "Chờ duyệt (chỉ áp dụng cho người báo)"
        APPROVED = "approved", "Đã duyệt (áp dụng cho mọi người)"
        REJECTED = "rejected", "Bị từ chối"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="correction_reports")
    item = models.OneToOneField(DetectionItem, on_delete=models.CASCADE, related_name="report")
    wrong_label = models.CharField(max_length=60, db_index=True, help_text="Nhãn model đã đoán")
    correct_label = models.CharField(max_length=80, blank=True, help_text="Nhãn đúng; rỗng = không phải đồ vật nào")
    embedding = models.BinaryField(help_text="float32 vector của vùng ảnh (BE/models/embedder.onnx)")
    crop = models.ImageField(upload_to="corrections/%Y/%m/", null=True, blank=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING, db_index=True)
    disputes = models.PositiveIntegerField(default=0, help_text="Số lần người khác báo lần sửa tự động này là sai")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="+")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    exported_at = models.DateTimeField(null=True, blank=True, help_text="Đã xuất làm dữ liệu train")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.wrong_label} → {self.correct_label or '(không phải đồ vật)'}"
