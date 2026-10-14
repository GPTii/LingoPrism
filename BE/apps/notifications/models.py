from django.conf import settings
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    class Kind(models.TextChoices):
        SYSTEM = "system", "Hệ thống"
        REMINDER = "reminder", "Nhắc học"
        ACHIEVEMENT = "achievement", "Thành tựu"
        LEAGUE = "league", "Giải đấu"
        XP_MILESTONE = "xp_milestone", "Mốc XP"
        FOLLOW = "follow", "Theo dõi"
        COMMENT = "comment", "Bình luận"
        LIKE = "like", "Thả tim"
        MESSAGE = "message", "Tin nhắn"
        EXAM = "exam", "Bài kiểm tra"
        LOCATION = "location", "Gợi ý theo vị trí"
        BROADCAST = "broadcast", "Thông báo từ quản trị"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField(max_length=14, choices=Kind.choices)
    title = models.CharField(max_length=120)
    body = models.CharField(max_length=300, blank=True)
    image = models.CharField(max_length=200, blank=True)
    data = models.JSONField(default=dict, blank=True, help_text="Điều hướng: {route, id, ...}")
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "read_at"])]


class NotificationSetting(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_setting")
    push_enabled = models.BooleanField(default=True)
    morning_time = models.TimeField(null=True, blank=True)
    evening_time = models.TimeField(null=True, blank=True)
    contextual_allowed = models.BooleanField(default=True, help_text="Cho phép gợi ý theo vị trí")
    social_enabled = models.BooleanField(default=True)


class DeviceToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="device_tokens")
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=10, help_text="android | ios | web")
    last_active_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
