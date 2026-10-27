from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS, BasePermission

UNVERIFIED_EMAIL = "Hãy xác minh email trước (mã 6 số đã gửi tới hộp thư của bạn) để dùng tính năng cộng đồng."


def require_verified_email(user):
    """Posting, commenting, friend requests, groups and messages need an address the learner proved is theirs:
    a sign-up bot cannot reach other learners. Everything else (learning) works before that."""
    if not getattr(user, "email_verified", True):
        raise PermissionDenied(UNVERIFIED_EMAIL)


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


class IsStaffRole(BasePermission):
    """Admin or staff (teacher / supporter)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ("admin", "staff"))


class IsStaffOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return IsStaffRole().has_permission(request, view)
