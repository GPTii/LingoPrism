from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.vocab.models import Word


class Post(TimeStampedModel):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Công khai"
        FOLLOWERS = "followers", "Người theo dõi"

    class Status(models.TextChoices):
        ACTIVE = "active", "Hiển thị"
        HIDDEN = "hidden", "Bị ẩn (kiểm duyệt)"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    image = models.ImageField(upload_to="posts/%Y/%m/")
    caption = models.CharField(max_length=500, blank=True)
    topic_label = models.CharField(max_length=50, blank=True)
    visibility = models.CharField(max_length=10, choices=Visibility.choices, default=Visibility.PUBLIC)
    status = models.CharField(max_length=6, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    save_count = models.PositiveIntegerField(default=0)
    detection = models.ForeignKey("detection.Detection", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-created_at"]


class PostWord(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="words")
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = [("post", "word")]
        ordering = ["order"]


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("post", "user")]


class PostComment(models.Model):
    class Kind(models.TextChoices):
        TEXT = "text", "Chữ"
        STICKER = "sticker", "Sticker"

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kind = models.CharField(max_length=7, choices=Kind.choices, default=Kind.TEXT)
    content = models.CharField(max_length=500, blank=True)
    sticker = models.CharField(max_length=40, blank=True)
    hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at"]


class PostReport(TimeStampedModel):
    class Reason(models.TextChoices):
        SPAM = "spam", "Spam"
        INAPPROPRIATE = "inappropriate", "Nội dung không phù hợp"
        WRONG_VOCAB = "wrong_vocab", "Từ vựng sai"
        HARASSMENT = "harassment", "Quấy rối"
        OTHER = "other", "Khác"

    class Status(models.TextChoices):
        PENDING = "pending", "Chờ xử lý"
        RESOLVED = "resolved", "Đã xử lý (ẩn bài)"
        DISMISSED = "dismissed", "Bỏ qua"

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reports")
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.CharField(max_length=14, choices=Reason.choices)
    details = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=9, choices=Status.choices, default=Status.PENDING, db_index=True)
    handled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        unique_together = [("post", "reporter")]
        ordering = ["-created_at"]


class UserFollow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following_set")
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="follower_set")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("follower", "following")]


class Group(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Hoạt động"
        HIDDEN = "hidden", "Bị ẩn"

    name = models.CharField(max_length=80)
    description = models.CharField(max_length=300, blank=True)
    icon = models.CharField(max_length=200, blank=True)
    require_approval = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_groups")
    status = models.CharField(max_length=6, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["-created_at"]


class GroupMember(models.Model):
    class Role(models.TextChoices):
        LEADER = "leader", "Trưởng nhóm"
        MEMBER = "member", "Thành viên"

    class Status(models.TextChoices):
        PENDING = "pending", "Chờ duyệt"
        ACTIVE = "active", "Đã tham gia"

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_memberships")
    role = models.CharField(max_length=6, choices=Role.choices, default=Role.MEMBER)
    status = models.CharField(max_length=7, choices=Status.choices, default=Status.ACTIVE)
    request_message = models.CharField(max_length=200, blank=True)
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("group", "user")]
