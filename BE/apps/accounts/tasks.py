from celery import shared_task
from django.core.mail import send_mail


@shared_task(autoretry_for=(OSError,), retry_backoff=30, max_retries=3)
def send_reset_code(email: str, code: str):
    send_mail(
        "LingoPrism - Mã đặt lại mật khẩu",
        f"Mã xác minh của bạn là: {code}\nMã có hiệu lực trong 15 phút.",
        None,
        [email],
    )
