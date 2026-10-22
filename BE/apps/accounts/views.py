import logging
import secrets

from django.conf import settings
from django.db import transaction
from django.db.models import ProtectedError
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.permissions import IsAdminRole
from apps.core.throttles import EmailRateThrottle

from . import serializers as s
from .models import AuthProvider, PasswordResetCode, User, UserGoal
from .tasks import send_reset_code

security_log = logging.getLogger("security")
# default limits + one per target e-mail (a password guess or reset-code flood spread over many IPs)
EMAIL_THROTTLED = [*api_settings.DEFAULT_THROTTLE_CLASSES, EmailRateThrottle]


def _client_ip(request):
    # same IP the rate limits use (X-Forwarded-For from nginx when NUM_PROXIES is set)
    return UserRateThrottle().get_ident(request)


def logout_everywhere(user):
    """Revoke every refresh token of the user (password changed/reset: a stolen session must not survive)."""
    for token in OutstandingToken.objects.filter(user=user).exclude(blacklistedtoken__isnull=False):
        BlacklistedToken.objects.get_or_create(token=token)


def _auth_response(user, status_code=status.HTTP_200_OK):
    return Response({"user": s.UserSerializer(user).data, "tokens": s.tokens_for(user)}, status=status_code)


@extend_schema(tags=["auth"])
class RegisterView(APIView):
    serializer_class = s.RegisterSerializer
    permission_classes = [AllowAny]
    throttle_scope = "register"

    @extend_schema(request=s.RegisterSerializer)
    def post(self, request):
        ser = s.RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return _auth_response(user, status.HTTP_201_CREATED)


@extend_schema(tags=["auth"])
class LoginView(APIView):
    serializer_class = s.LoginSerializer
    permission_classes = [AllowAny]
    throttle_scope = "login"
    throttle_classes = EMAIL_THROTTLED

    @extend_schema(request=s.LoginSerializer)
    def post(self, request):
        ser = s.LoginSerializer(data=request.data)
        if not ser.is_valid():
            security_log.warning("login failed email=%s ip=%s", str(request.data.get("email", ""))[:120], _client_ip(request))
            raise ValidationError(ser.errors)
        user = ser.validated_data["user"]
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        return _auth_response(user)


@extend_schema(tags=["auth"])
class GoogleLoginView(APIView):
    """Verify a Google ID token (from Flutter google_sign_in or Google Identity on web)."""

    serializer_class = s.GoogleLoginSerializer
    permission_classes = [AllowAny]
    throttle_scope = "login"

    @extend_schema(request=s.GoogleLoginSerializer)
    def post(self, request):
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token as google_id_token

        ser = s.GoogleLoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if not settings.GOOGLE_CLIENT_IDS:
            return Response({"detail": "Đăng nhập Google chưa được cấu hình", "errors": {}}, status=503)
        try:
            info = google_id_token.verify_oauth2_token(ser.validated_data["id_token"], google_requests.Request())
        except ValueError:
            return Response({"detail": "Google token không hợp lệ", "errors": {}}, status=400)
        if info.get("aud") not in settings.GOOGLE_CLIENT_IDS or not info.get("email_verified"):
            return Response({"detail": "Google token không hợp lệ", "errors": {}}, status=400)

        with transaction.atomic():
            link = AuthProvider.objects.select_related("user").filter(
                provider=AuthProvider.Provider.GOOGLE, provider_uid=info["sub"]
            ).first()
            if link:
                user = link.user
            else:
                user = User.objects.filter(email=info["email"].lower()).first()
                if user is None:
                    user = User.objects.create_user(email=info["email"], display_name=info.get("name", ""))
                    UserGoal.objects.create(user=user)
                AuthProvider.objects.create(user=user, provider=AuthProvider.Provider.GOOGLE, provider_uid=info["sub"])
        if user.status == User.Status.LOCKED:
            return Response({"detail": "Tài khoản đã bị khóa", "errors": {}}, status=403)
        return _auth_response(user)


@extend_schema(tags=["auth"])
class GoogleConfigView(APIView):
    """The public Web client ID for the "Sign in with Google" button; null when Google sign-in is off."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses={200: None})
    def get(self, request):
        return Response({"client_id": settings.GOOGLE_WEB_CLIENT_ID or None})


@extend_schema(tags=["auth"])
class LogoutView(APIView):
    serializer_class = s.LogoutSerializer
    @extend_schema(request=s.LogoutSerializer, responses={205: None})
    def post(self, request):
        ser = s.LogoutSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            RefreshToken(ser.validated_data["refresh"]).blacklist()
        except TokenError:
            pass
        return Response(status=status.HTTP_205_RESET_CONTENT)


@extend_schema(tags=["auth"])
class ForgotPasswordView(APIView):
    serializer_class = s.ForgotPasswordSerializer
    permission_classes = [AllowAny]
    throttle_scope = "password_reset"
    throttle_classes = EMAIL_THROTTLED

    @extend_schema(request=s.ForgotPasswordSerializer)
    def post(self, request):
        ser = s.ForgotPasswordSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = User.objects.filter(email=ser.validated_data["email"].lower(), is_active=True).first()
        if user:
            reset = PasswordResetCode.issue(user)
            # sent by the Celery worker: a slow mail server must not hold the request (and a server thread)
            send_reset_code.delay(user.email, reset.code)
        # Always the same answer so emails cannot be enumerated.
        return Response({"detail": "Nếu email tồn tại, mã xác minh đã được gửi."})


@extend_schema(tags=["auth"])
class VerifyResetCodeView(APIView):
    serializer_class = s.VerifyResetCodeSerializer
    permission_classes = [AllowAny]
    throttle_scope = "password_reset"
    throttle_classes = EMAIL_THROTTLED

    @extend_schema(request=s.VerifyResetCodeSerializer)
    def post(self, request):
        ser = s.VerifyResetCodeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        reset = (
            PasswordResetCode.objects.filter(
                user__email=ser.validated_data["email"].lower(), used_at__isnull=True
            )
            .order_by("-created_at")
            .first()
        )
        invalid = Response({"detail": "Mã xác minh không đúng hoặc đã hết hạn", "errors": {}}, status=400)
        if reset is None or reset.is_expired or reset.attempts >= PasswordResetCode.MAX_ATTEMPTS:
            return invalid
        if not secrets.compare_digest(reset.code, ser.validated_data["code"]):
            security_log.warning("reset code wrong email=%s ip=%s", reset.user.email, _client_ip(request))
            reset.attempts += 1
            reset.save(update_fields=["attempts"])
            return invalid
        reset.reset_token = secrets.token_urlsafe(32)
        reset.save(update_fields=["reset_token"])
        return Response({"reset_token": reset.reset_token})


@extend_schema(tags=["auth"])
class ResetPasswordView(APIView):
    serializer_class = s.ResetPasswordSerializer
    permission_classes = [AllowAny]
    throttle_scope = "password_reset"

    @extend_schema(request=s.ResetPasswordSerializer)
    def post(self, request):
        ser = s.ResetPasswordSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        reset = PasswordResetCode.objects.filter(
            reset_token=ser.validated_data["reset_token"], used_at__isnull=True
        ).select_related("user").first()
        if reset is None or reset.is_expired:
            return Response({"detail": "Phiên đặt lại mật khẩu đã hết hạn", "errors": {}}, status=400)
        reset.user.set_password(ser.validated_data["new_password"])
        reset.user.save(update_fields=["password"])
        logout_everywhere(reset.user)
        reset.used_at = timezone.now()
        reset.save(update_fields=["used_at"])
        return Response({"detail": "Đặt lại mật khẩu thành công"})


@extend_schema(tags=["auth"])
class ChangePasswordView(APIView):
    serializer_class = s.ChangePasswordSerializer
    @extend_schema(request=s.ChangePasswordSerializer)
    def post(self, request):
        ser = s.ChangePasswordSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        request.user.set_password(ser.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        logout_everywhere(request.user)
        return Response({"detail": "Bạn đã đổi mật khẩu."})


@extend_schema(tags=["me"])
class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = s.UserSerializer

    def get_object(self):
        return self.request.user


@extend_schema(tags=["me"])
class MyGoalView(generics.RetrieveUpdateAPIView):
    serializer_class = s.UserGoalSerializer

    def get_object(self):
        goal, _ = UserGoal.objects.get_or_create(user=self.request.user)
        return goal


@extend_schema(tags=["users"])
class PublicUserView(generics.RetrieveAPIView):
    serializer_class = s.PublicUserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.filter(is_active=True)


@extend_schema(tags=["admin-users"])
class AdminUserViewSet(viewsets.ModelViewSet):
    serializer_class = s.AdminUserSerializer
    permission_classes = [IsAdminRole]
    queryset = User.objects.all()
    filterset_fields = ["role", "status", "learner_type", "active_language"]
    search_fields = ["email", "display_name"]
    ordering_fields = ["created_at", "last_login", "email"]

    def _guard_self(self, user, data):
        if user.pk == self.request.user.pk and (
            data.get("role", user.role) != user.role or data.get("status", user.status) != user.status
        ):
            raise ValidationError("Không thể tự đổi vai trò hoặc khóa tài khoản của chính mình")

    def _sync_flags(self, user):
        user.is_staff = user.role == User.Role.ADMIN
        user.save(update_fields=["is_staff"])

    def perform_create(self, serializer):
        self._sync_flags(serializer.save())

    def perform_update(self, serializer):
        self._guard_self(serializer.instance, serializer.validated_data)
        self._sync_flags(serializer.save())

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user.pk == request.user.pk:
            raise ValidationError("Không thể xóa tài khoản đang đăng nhập")
        if user.role == User.Role.ADMIN and not User.objects.filter(role=User.Role.ADMIN).exclude(pk=user.pk).exists():
            raise ValidationError("Phải còn ít nhất một quản trị viên")
        try:
            with transaction.atomic():
                user.delete()
        except ProtectedError:
            return Response({"detail": "Tài khoản đang được dữ liệu khác tham chiếu – hãy khóa thay vì xóa."},
                            status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_204_NO_CONTENT)


