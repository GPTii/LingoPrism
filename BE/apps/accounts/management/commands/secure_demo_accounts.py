import secrets

from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.accounts.views import logout_everywhere

from .seed_demo_users import DEMO_PASSWORD


class Command(BaseCommand):
    help = ("Đổi mật khẩu ngẫu nhiên cho mọi tài khoản demo (@lingoprism.local) còn dùng mật khẩu chung công khai "
            "trong repo, và thu hồi mọi phiên đăng nhập của chúng. Chạy ở mỗi lần deploy production.")

    def handle(self, *args, **opts):
        for user in User.objects.filter(email__endswith="@lingoprism.local").order_by("id"):
            if not user.check_password(DEMO_PASSWORD):
                continue
            password = secrets.token_urlsafe(12)
            user.set_password(password)
            user.save(update_fields=["password"])
            logout_everywhere(user)
            self.stdout.write(f"{user.email}  {password}")
