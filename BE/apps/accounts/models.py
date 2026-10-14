import secrets
from datetime import timedelta

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("Email là bắt buộc")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("role", User.Role.LEARNER)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.update(role=User.Role.ADMIN, is_staff=True, is_superuser=True)
        return self._create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    class Role(models.TextChoices):
        ADMIN = "admin", "Quản trị viên"
        STAFF = "staff", "Giáo viên / Hỗ trợ"
        LEARNER = "learner", "Học viên"

    class LearnerType(models.TextChoices):
        KID = "kid", "Trẻ em"
        ADULT = "adult", "Người lớn"

    class ZhScript(models.TextChoices):
        HANS = "hans", "Giản thể (Trung Quốc đại lục)"
        HANT = "hant", "Phồn thể (Đài Loan)"

    class Status(models.TextChoices):
        ACTIVE = "active", "Hoạt động"
        LOCKED = "locked", "Bị khóa"

    class Gender(models.TextChoices):
        MALE = "male", "Nam"
        FEMALE = "female", "Nữ"
        OTHER = "other", "Khác"

    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=80, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.CharField(max_length=200, blank=True)

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.LEARNER, db_index=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    # learning profile (survey / onboarding)
    learner_type = models.CharField(max_length=10, choices=LearnerType.choices, default=LearnerType.ADULT)
    learning_languages = models.JSONField(default=list, blank=True, help_text='VD ["en", "zh"]')
    active_language = models.CharField(max_length=5, default="en", help_text="Ngôn ngữ đang học: vi | en | zh")
    zh_script = models.CharField(max_length=4, choices=ZhScript.choices, default=ZhScript.HANS)
    show_zhuyin = models.BooleanField(default=False)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    purpose = models.CharField(max_length=30, blank=True, help_text="communication | work | study | friends | none")
    daily_minutes = models.PositiveSmallIntegerField(default=10)
    onboarding_completed = models.BooleanField(default=False)
    timezone = models.CharField(max_length=40, default="Asia/Ho_Chi_Minh")

    # wallet (gamification currencies)
    scales_balance = models.PositiveIntegerField(default=0, help_text="Vảy")
    gems_balance = models.PositiveIntegerField(default=0, help_text="Ngọc")

    is_staff = models.BooleanField(default=False, help_text="Được vào Django Admin")
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    @property
    def is_staff_role(self):
        return self.role in (self.Role.ADMIN, self.Role.STAFF)

    @property
    def zh_language_code(self):
        return "zh-Hant" if self.zh_script == self.ZhScript.HANT else "zh-Hans"


class UserGoal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="goal")
    daily_new_target = models.PositiveSmallIntegerField(default=10)
    daily_review_target = models.PositiveSmallIntegerField(default=20)
    remind_morning = models.TimeField(null=True, blank=True)
    remind_evening = models.TimeField(null=True, blank=True)
    smart_remind = models.BooleanField(default=True)

    def __str__(self):
        return f"Goal<{self.user_id}>"


class AuthProvider(models.Model):
    class Provider(models.TextChoices):
        GOOGLE = "google", "Google"
        FACEBOOK = "facebook", "Facebook"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="auth_providers")
    provider = models.CharField(max_length=20, choices=Provider.choices)
    provider_uid = models.CharField(max_length=255)
    linked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("provider", "provider_uid")]


class PasswordResetCode(models.Model):
    """6-digit code sent by email (forgot password flow)."""

    TTL = timedelta(minutes=15)
    MAX_ATTEMPTS = 5

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_codes")
    code = models.CharField(max_length=6)
    reset_token = models.CharField(max_length=64, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def issue(cls, user):
        cls.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
        return cls.objects.create(user=user, code=f"{secrets.randbelow(10**6):06d}")

    @property
    def is_expired(self):
        return timezone.now() > self.created_at + self.TTL
