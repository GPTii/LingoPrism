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


@shared_task(autoretry_for=(OSError,), retry_backoff=30, max_retries=3)
def send_email_code(email: str, code: str):
    send_mail(
        "LingoPrism - Xác minh email",
        f"Chào bạn,\n\nMã xác minh email của bạn trên LingoPrism là: {code}\nMã có hiệu lực trong 24 giờ.\n\n"
        "Nếu bạn không tạo tài khoản LingoPrism, hãy bỏ qua email này.",
        None,
        [email],
    )


@shared_task(autoretry_for=(OSError,), retry_backoff=30, max_retries=3)
def send_parent_consent(parent_email: str, child_name: str, child_email: str, code: str, site: str):
    send_mail(
        "LingoPrism - Xin phép phụ huynh cho con học",
        f"Kính chào phụ huynh,\n\n{child_name} ({child_email}) đang tạo tài khoản học ngoại ngữ trên LingoPrism "
        "và cho biết bạn là cha, mẹ hoặc người giám hộ.\n\n"
        "Theo quy định về bảo vệ dữ liệu cá nhân của trẻ em, LingoPrism cần sự đồng ý của bạn trước khi con sử dụng. "
        f"Chính sách quyền riêng tư (dữ liệu nào được thu thập, dùng để làm gì, cách xoá): {site}/privacy\n\n"
        f"Nếu bạn đồng ý, hãy đưa con mã sau để nhập vào ứng dụng: {code}\n"
        "Mã có hiệu lực trong 24 giờ.\n\n"
        "Nếu bạn không đồng ý hoặc không biết việc này, chỉ cần bỏ qua email: tài khoản sẽ không dùng được. "
        f"Bạn có thể yêu cầu xoá tài khoản bất cứ lúc nào: {site}/delete-account",
        None,
        [parent_email],
    )
