from django.core.management.base import BaseCommand

from apps.accounts.models import User, UserGoal

DEMO_PASSWORD = "LingoPrism@2026"
DEMO_USERS = [
    {"email": "admin@lingoprism.local", "display_name": "Quản trị viên", "role": "admin", "is_staff": True, "is_superuser": True},
    {"email": "staff@lingoprism.local", "display_name": "Cô giáo Lan", "role": "staff"},
    {"email": "adult@lingoprism.local", "display_name": "Minh Anh", "role": "learner", "learner_type": "adult",
     "learning_languages": ["en", "zh"], "active_language": "zh", "zh_script": "hans"},
    {"email": "taiwan@lingoprism.local", "display_name": "Bảo Ngọc", "role": "learner", "learner_type": "adult",
     "learning_languages": ["zh"], "active_language": "zh", "zh_script": "hant", "show_zhuyin": True},
    {"email": "kid@lingoprism.local", "display_name": "Bé Na", "role": "learner", "learner_type": "kid",
     "learning_languages": ["vi", "en"], "active_language": "vi"},
]


class Command(BaseCommand):
    help = f"Tạo tài khoản demo (mật khẩu chung: {DEMO_PASSWORD}) – chỉ dùng cho môi trường dev/demo"

    def handle(self, *args, **opts):
        for data in DEMO_USERS:
            data = dict(data)
            email = data.pop("email")
            user, created = User.objects.get_or_create(email=email, defaults=data)
            if created:
                user.set_password(DEMO_PASSWORD)
                user.onboarding_completed = True
                user.save()
            UserGoal.objects.get_or_create(user=user)
            self.stdout.write(f"{'+' if created else '='} {email} ({user.role})")
        self.stdout.write(self.style.SUCCESS(f"Mật khẩu demo: {DEMO_PASSWORD}"))
