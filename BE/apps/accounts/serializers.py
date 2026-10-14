from django.contrib.auth import authenticate, password_validation
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

    class Meta:
        model = User
        fields = [
            "id", "email", "display_name", "avatar", "avatar_preset", "bio", "role", "status",
            "learner_type", "learning_languages", "active_language", "zh_script", "show_zhuyin",
            "birth_date", "gender", "purpose", "daily_minutes", "onboarding_completed", "timezone",
            "scales_balance", "gems_balance", "goal", "created_at",
        ]
        read_only_fields = ["id", "email", "role", "status", "scales_balance", "gems_balance", "created_at"]

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

    class Meta:
        model = User
        fields = ["id", "display_name", "avatar", "bio", "learner_type", "created_at"]

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
        user = User.objects.create_user(
            email=validated["email"],
            password=validated["password"],
            display_name=validated.get("display_name") or validated["email"].split("@")[0],
        )
        UserGoal.objects.create(user=user)
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
    """Used by the admin web to manage accounts and roles."""

    class Meta:
        model = User
        fields = [
            "id", "email", "display_name", "avatar", "role", "status", "learner_type",
            "learning_languages", "active_language", "zh_script", "scales_balance", "gems_balance",
            "last_login", "created_at",
        ]
        read_only_fields = ["id", "email", "last_login", "created_at"]
