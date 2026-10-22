from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


def can_sign_in(user) -> bool:
    """SIMPLE_JWT rule for logging in and refreshing: active and not locked by an admin."""
    return user is not None and user.is_active and user.status != "locked"


class LockAwareJWTAuthentication(JWTAuthentication):
    """A locked account is cut off at once, not when its tokens expire (access 60 min, refresh 30 days)."""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if user.status == "locked":
            raise AuthenticationFailed("Tài khoản đã bị khóa", code="user_locked")
        return user
