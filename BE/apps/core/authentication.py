import re

from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication


def can_sign_in(user) -> bool:
    """SIMPLE_JWT rule for logging in and refreshing: active and not locked by an admin."""
    return user is not None and user.is_active and user.status != "locked"


# what a child's account may reach before a parent agreed: its profile (onboarding), signing out, the consent
# itself, deleting the account, and the public pages
BEFORE_PARENT_CONSENT = re.compile(
    r"^/api/v1/(me/$|me/goal/$|me/parent-consent/|me/delete/$|auth/|releases/$|health/$)")


class LockAwareJWTAuthentication(JWTAuthentication):
    """A locked account is cut off at once, not when its tokens expire (access 60 min, refresh 30 days).
    A child's account (kid mode or under 16) reaches nothing but BEFORE_PARENT_CONSENT until a parent or guardian
    agreed (Decree 13/2023): every API view authenticates here, so none can forget the check."""

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is not None:
            user = result[0]
            if user.parent_consent_status in ("missing", "pending") and not BEFORE_PARENT_CONSENT.match(request.path):
                raise PermissionDenied("Cần phụ huynh đồng ý trước khi dùng tài khoản trẻ em", code="parent_consent_required")
        return result

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if user.status == "locked":
            raise AuthenticationFailed("Tài khoản đã bị khóa", code="user_locked")
        return user
