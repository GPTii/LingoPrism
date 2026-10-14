from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import AuthProvider, User, UserGoal


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-created_at"]
    list_display = ["email", "display_name", "role", "learner_type", "active_language", "status", "created_at"]
    list_filter = ["role", "status", "learner_type", "active_language"]
    search_fields = ["email", "display_name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Hồ sơ", {"fields": ("display_name", "avatar", "bio", "birth_date", "gender")}),
        ("Học tập", {"fields": ("learner_type", "learning_languages", "active_language", "zh_script", "show_zhuyin",
                                "purpose", "daily_minutes", "onboarding_completed")}),
        ("Ví", {"fields": ("scales_balance", "gems_balance")}),
        ("Quyền", {"fields": ("role", "status", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "role")}),)


admin.site.register(UserGoal)
admin.site.register(AuthProvider)
