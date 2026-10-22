from django.conf import settings
from django.db import models
from django.utils import timezone


class GroupMessage(models.Model):
    class Kind(models.TextChoices):
        TEXT = "text", "Chữ"
        STICKER = "sticker", "Sticker"
        BADGE = "badge", "Khoe huy hiệu"
        SYSTEM = "system", "Hệ thống"

    group = models.ForeignKey("community.Group", on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    kind = models.CharField(max_length=7, choices=Kind.choices, default=Kind.TEXT)
    content = models.CharField(max_length=1000, blank=True)
    sticker = models.CharField(max_length=40, blank=True)
    badge = models.ForeignKey("gamification.Badge", null=True, blank=True, on_delete=models.SET_NULL)
    client_id = models.CharField(max_length=40, blank=True, help_text="ID tạm do client sinh để khử trùng lặp")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["created_at", "id"]


class SupportConversation(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Đang mở"
        CLOSED = "closed", "Đã đóng"

    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="support_conversations")
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_conversations")
    subject = models.CharField(max_length=120, default="Hỗ trợ học tập")
    status = models.CharField(max_length=6, choices=Status.choices, default=Status.OPEN, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_message_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-last_message_at"]


class SupportMessage(models.Model):
    conversation = models.ForeignKey(SupportConversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.CharField(max_length=2000)
    client_id = models.CharField(max_length=40, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["created_at", "id"]


class DirectThread(models.Model):
    """A private conversation between two learners (stored once per pair: user_a has the smaller id)."""

    user_a = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    user_b = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    created_at = models.DateTimeField(default=timezone.now)
    last_message_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-last_message_at"]
        constraints = [models.UniqueConstraint(fields=["user_a", "user_b"], name="direct_thread_pair")]

    def other(self, user):
        return self.user_b if user.id == self.user_a_id else self.user_a


class DirectMessage(models.Model):
    thread = models.ForeignKey(DirectThread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.CharField(max_length=1000)
    client_id = models.CharField(max_length=40, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["created_at", "id"]
