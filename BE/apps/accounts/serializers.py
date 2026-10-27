from django.contrib.auth import authenticate, password_validation
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, UserGoal

LANGUAGE_CHOICES = ("vi", "en", "zh")


def tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class UserGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGoal
        fields = ["daily_new_target", "daily_review_target", "remind_morning", "remind_evening", "smart_remind"]

    def validate_daily_new_target(self, value):
        if value < 1:
            raise serializers.ValidationError("Số từ vựng học mỗi ngày phải lớn hơn 0")
        return value

    def validate_daily_review_target(self, value):
        if value < 1:
            raise serializers.ValidationError("Số từ vựng ôn tập mỗi ngày phải lớn hơn 0")
        return value


class UserSerializer(serializers.ModelSerializer):
    goal = UserGoalSerializer(read_only=True)
    mascot = serializers.SerializerMethodField()

    def get_mascot(self, obj):
        from apps.gamification.mascot import look

        return look(obj)

    class Meta:
        model = User
        fields = [
            "id", "public_id", "email", "display_name", "avatar", "avatar_preset", "bio", "role", "status",
            "learner_type", "learning_languages", "active_language", "zh_script", "show_zhuyin",
            "birth_date", "gender", "purpose", "daily_minutes", "onboarding_completed", "timezone",
            "scales_balance", "gems_balance", "goal", "mascot", "created_at",
        ]
        read_only_fields = ["id", "public_id", "email", "role", "status", "scales_balance", "gems_balance", "created_at"]

    def validate_learning_languages(self, value):
        bad = [v for v in value if v not in LANGUAGE_CHOICES]
        if bad:
            raise serializers.ValidationError(f"Ngôn ngữ không hỗ trợ: {', '.join(bad)}")
        return list(dict.fromkeys(value))

    def validate_active_language(self, value):
        if value not in LANGUAGE_CHOICES:
            raise serializers.ValidationError("Ngôn ngữ không hỗ trợ")
        return value


class PublicUserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    mascot = serializers.SerializerMethodField()

    def get_mascot(self, obj):
        from apps.gamification.mascot import look

        return look(obj)

    class Meta:
        model = User
        fields = ["id", "display_name", "avatar", "mascot", "bio", "learner_type", "created_at"]

    def get_avatar(self, obj):
        return obj.avatar_url(self.context.get("request"))


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    display_name = serializers.CharField(max_length=80, required=False, allow_blank=True)

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email đã được sử dụng")
        return value

    def validate(self, attrs):
        password_validation.validate_password(attrs["password"], User(email=attrs["email"]))
        return attrs

    def create(self, validated):
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=validated["email"],
                    password=validated["password"],
                    display_name=validated.get("display_name") or validated["email"].split("@")[0],
                )
                UserGoal.objects.create(user=user)
        except IntegrityError:  # the same e-mail sent twice at once (double tap): the other request created it
            raise serializers.ValidationError({"email": ["Email đã được sử dụng"]})
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(email=attrs["email"].lower(), password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("Email hoặc mật khẩu không đúng")
        if user.status == User.Status.LOCKED:
            raise serializers.ValidationError("Tài khoản đã bị khóa")
        attrs["user"] = user
        return attrs


class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyResetCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)


class ResetPasswordSerializer(serializers.Serializer):
    reset_token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError({"old_password": "Mật khẩu hiện tại không đúng"})
        password_validation.validate_password(attrs["new_password"], user)
        return attrs


class AdminUserSerializer(serializers.ModelSerializer):
    """Used by the admin web to create, edit and delete accounts."""

    password = serializers.CharField(write_only=True, required=False, allow_blank=True, min_length=8,
                                     help_text="Bắt buộc khi tạo; để trống khi sửa nếu không đổi mật khẩu")

    class Meta:
        model = User
        fields = [
            "id", "email", "password", "display_name", "avatar", "role", "status", "learner_type",
            "learning_languages", "active_language", "zh_script", "scales_balance", "gems_balance",
            "last_login", "created_at",
        ]
        read_only_fields = ["id", "avatar", "last_login", "created_at"]

    validate_learning_languages = UserSerializer.validate_learning_languages
    validate_active_language = UserSerializer.validate_active_language

    def validate_email(self, value):
        value = User.objects.normalize_email(value).lower()
        if User.objects.filter(email__iexact=value).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError("Email đã được sử dụng")
        return value

    def validate_password(self, value):
        if value:
            password_validation.validate_password(value)
        return value

    def validate(self, attrs):
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError({"password": "Cần nhập mật khẩu cho tài khoản mới"})
        active = attrs.get("active_language", getattr(self.instance, "active_language", "en"))
        langs = attrs.get("learning_languages", getattr(self.instance, "learning_languages", []))
        if langs and active not in langs:
            attrs["learning_languages"] = [*langs, active]
        return attrs

    def create(self, validated):
        password = validated.pop("password")
        validated.setdefault("learning_languages", [validated.get("active_language", "en")])
        user = User.objects.create_user(password=password, onboarding_completed=True, **validated)
        UserGoal.objects.create(user=user)
        return user

    def update(self, instance, validated):
        password = validated.pop("password", "")
        user = super().update(instance, validated)
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])
        return user
