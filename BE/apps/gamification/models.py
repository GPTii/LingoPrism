from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class UserStats(models.Model):
    """Denormalized counters for fast home / profile / leaderboard queries."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stats")
    lifetime_xp = models.PositiveIntegerField(default=0)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)
    freezes_used = models.PositiveIntegerField(default=0)
    words_learned = models.PositiveIntegerField(default=0)
    words_mastered = models.PositiveIntegerField(default=0)
    detections = models.PositiveIntegerField(default=0)
    posts = models.PositiveIntegerField(default=0)

    @property
    def level(self) -> int:
        return 1 + self.lifetime_xp // 1000


class XpTransaction(models.Model):
    class Source(models.TextChoices):
        LEARN = "learn", "Học từ mới"
        REVIEW = "review", "Ôn tập"
        PRACTICE = "practice", "Luyện tập"
        EXAM = "exam", "Bài kiểm tra"
        QUEST = "quest", "Nhiệm vụ"
        CAMERA = "camera", "Nhận diện ảnh"
        COMMUNITY = "community", "Cộng đồng"
        ADMIN = "admin", "Điều chỉnh"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="xp_transactions")
    source = models.CharField(max_length=10, choices=Source.choices)
    source_id = models.CharField(max_length=40, blank=True)
    base_amount = models.IntegerField()
    multiplier = models.FloatField(default=1.0)
    amount = models.IntegerField(help_text="XP thực nhận (sau boost và giới hạn ngày)")
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]


class DailyProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_progress")
    date = models.DateField()
    new_target = models.PositiveSmallIntegerField(default=10)
    review_target = models.PositiveSmallIntegerField(default=20)
    new_learned = models.PositiveIntegerField(default=0)
    reviews_done = models.PositiveIntegerField(default=0)
    xp = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=False)
    freeze_used = models.BooleanField(default=False)

    class Meta:
        unique_together = [("user", "date")]
        ordering = ["-date"]


class Badge(models.Model):
    class Condition(models.TextChoices):
        XP = "xp", "Tổng XP"
        STREAK = "streak", "Chuỗi ngày học"
        WORDS_LEARNED = "words_learned", "Số từ đã học"
        WORDS_MASTERED = "words_mastered", "Số từ đã thuộc"
        DETECTIONS = "detections", "Số lần nhận diện ảnh"
        POSTS = "posts", "Số bài đăng"

    code = models.SlugField(unique=True)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=200, blank=True)
    icon = models.CharField(max_length=200, blank=True, help_text="Đường dẫn ảnh trong app (assets/...)")
    sticker = models.CharField(max_length=200, blank=True)
    condition = models.CharField(max_length=16, choices=Condition.choices)
    threshold = models.PositiveIntegerField()
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["condition", "threshold"]

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("user", "badge")]


class DailyQuest(models.Model):
    class Kind(models.TextChoices):
        SAVE_WORDS = "save_words", "Lưu 5 từ mới qua hình ảnh"
        REACH_LEARN_GOAL = "reach_learn_goal", "Đạt mục tiêu học từ mới hôm nay"
        REACH_REVIEW_GOAL = "reach_review_goal", "Đạt mục tiêu ôn tập từ hôm nay"
        POST_COMMUNITY_IMAGE = "post_community_image", "Đăng 1 hình ảnh lên cộng đồng"
        ENGAGE_COMMUNITY = "engage_community", "Bình luận hoặc thả tim 5 bài viết"

    REWARD_SCALES = 15

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_quests")
    date = models.DateField()
    kind = models.CharField(max_length=24, choices=Kind.choices)
    target = models.PositiveSmallIntegerField()
    progress = models.PositiveSmallIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    reward_claimed = models.BooleanField(default=False)

    class Meta:
        unique_together = [("user", "date", "kind")]
        ordering = ["date", "id"]

    @property
    def completed(self):
        return self.progress >= self.target


class MonthlyQuest(models.Model):
    TARGET = 20
    REWARD_GEMS = 2

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="monthly_quests")
    month = models.CharField(max_length=7, help_text="YYYY-MM")
    completed_count = models.PositiveSmallIntegerField(default=0)
    reward_claimed = models.BooleanField(default=False)
    reward_claimed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("user", "month")]


class LeagueTier(models.Model):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=40)
    order = models.PositiveSmallIntegerField(unique=True)
    icon = models.CharField(max_length=200, blank=True)
    promote_top = models.PositiveSmallIntegerField(default=5)
    demote_bottom = models.PositiveSmallIntegerField(default=5)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class LeagueCycle(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Đang diễn ra"
        CLOSED = "closed", "Đã kết thúc"

    tier = models.ForeignKey(LeagueTier, on_delete=models.CASCADE, related_name="cycles")
    group_index = models.PositiveSmallIntegerField(default=0, help_text="Mỗi hạng chia nhóm tối đa 30 người")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=6, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["-start_at"]


class LeagueMember(models.Model):
    cycle = models.ForeignKey(LeagueCycle, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="league_memberships")
    weekly_xp = models.PositiveIntegerField(default=0)
    rank = models.PositiveSmallIntegerField(null=True, blank=True)
    result = models.CharField(max_length=10, blank=True, help_text="promoted | stayed | demoted")

    class Meta:
        unique_together = [("cycle", "user")]
        ordering = ["-weekly_xp", "id"]


class Item(models.Model):
    class Effect(models.TextChoices):
        STREAK_FREEZE = "streak_freeze", "Giữ streak khi nghỉ 1 ngày"
        XP_DOUBLE_15M = "xp_double_15m", "x2 XP trong 15 phút"
        XP_PLUS25_24H = "xp_plus25_24h", "+25% XP trong 24 giờ"
        STICKER = "sticker", "Sticker chat & bình luận"

    code = models.SlugField(unique=True)
    name = models.CharField(max_length=60)
    description = models.CharField(max_length=200)
    image = models.CharField(max_length=200, help_text="Đường dẫn asset")
    effect = models.CharField(max_length=16, choices=Effect.choices)
    cost_scales = models.PositiveIntegerField(null=True, blank=True)
    cost_gems = models.PositiveIntegerField(null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class UserInventory(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inventory")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("user", "item")]


class ActiveBoost(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="boosts")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    multiplier = models.FloatField()
    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(db_index=True)
