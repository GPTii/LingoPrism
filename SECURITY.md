# Bảo mật & chống quá tải – LingoPrism

Đối chiếu với [OWASP Top 10:2025](https://owasp.org/Top10/2025/0x00_2025-Introduction) và OWASP API Security Top 10 (2023).

## Đã có trong code

| Rủi ro | Bảo vệ | Ở đâu |
|---|---|---|
| **DDoS tầng ứng dụng / spam request** (API4 Unrestricted Resource Consumption) | 2 lớp giới hạn tần suất: nginx theo IP (`limit_req`, `limit_conn`) → DRF theo IP, theo tài khoản và theo email. Endpoint nặng (nhận diện ảnh YOLO) có mức riêng | `deploy/nginx/nginx.conf`, `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]`, `apps/core/throttles.py` |
| Slowloris / client chậm giữ kết nối | timeout header/body/send ở nginx; query DB quá 15 s bị huỷ (`statement_timeout`) | nginx, `DATABASES` |
| **Dò mật khẩu** (A07 Authentication Failures) | 40 lần/phút mỗi IP + **10 lần/giờ mỗi tài khoản dù đổi IP**; log `security` ghi mọi lần sai | `LoginView`, `EmailRateThrottle` |
| Dò mã quên mật khẩu / spam email người khác | mã 5 lần thử, giới hạn xin mã theo IP và theo email; email gửi qua Celery (SMTP chậm không treo server) | `ForgotPasswordView`, `accounts/tasks.py` |
| Phiên bị đánh cắp | đổi / đặt lại mật khẩu → thu hồi mọi refresh token; refresh token xoay vòng + blacklist | `logout_everywhere` |
| **Xem/sửa dữ liệu người khác** (A01 Broken Access Control) | mọi API người học lọc theo `request.user`; API quản trị cần `IsStaffRole`/`IsAdminRole`; hồ sơ công khai không có email | các `get_queryset` |
| **Lộ vị trí qua ảnh** (EXIF GPS – có người học là trẻ em) | ảnh upload bị xoá EXIF, đặt tên ngẫu nhiên, mã hoá lại, thu nhỏ ≤ 2048 px | `apps/core/images.py` |
| Bom giải nén ảnh (file nhỏ, khai báo 100 000×100 000 px) | `Image.MAX_IMAGE_PIXELS`, từ chối > 60 MP | `apps/core/images.py` |
| Spam chat realtime | token bucket mỗi kết nối WebSocket (8 tin liền, 1 tin/giây), khung tối đa 8 KB, tin nhắn cắt 1–2k ký tự | `apps/chat/consumers.py` |
| **Cấu hình sai** (A02 Security Misconfiguration) | production không chạy nếu thiếu `DJANGO_SECRET_KEY`; `DEBUG=False`; tắt Swagger và browsable API; cookie Secure/HttpOnly; `X-Frame-Options DENY`; CSP; ẩn version nginx; chặn file ẩn (`.env`, `.git`) | `config/settings/prod.py`, nginx |
| XSS | React tự escape; CSP chỉ cho script cùng nguồn; file trong `/media/` không bao giờ được chạy như trang/script | nginx CSP |
| Giả IP để né giới hạn | nginx **ghi đè** `X-Forwarded-For` bằng IP thật; Django chỉ tin đúng `NUM_PROXIES` proxy | `proxy_params.conf` |
| Chiếm container | backend chạy bằng user thường (`app`), không phải root; Postgres/Redis không mở cổng ra ngoài | `BE/Dockerfile`, compose |
| **Thư viện có lỗ hổng** (A03 Supply Chain) | `npm audit`: 0 lỗ hổng (17/10/2026). `pip-audit`: `twisted` (phụ thuộc của daphne) CVE-2026-106454, chưa có bản vá – theo dõi và nâng cấp khi có | chạy lại định kỳ |

## Phải làm trên server (code không làm thay được)

1. **Đặt Cloudflare (gói Free) trước server.** DDoS tầng mạng (hàng Gbps) không app nào tự chống được, chỉ CDN chặn được. Bật "Under Attack Mode" khi bị tấn công, rồi bỏ comment `set_real_ip_from`/`real_ip_header` trong `nginx.conf`.
2. **Tường lửa:** chỉ mở 22, 80, 443 (`ufw allow 22,80,443/tcp`). SSH chỉ dùng key, tắt đăng nhập bằng mật khẩu; cài `fail2ban`.
3. **HTTPS** (Cloudflare hoặc certbot). Chạy ổn rồi mới đặt `SECURE_HSTS_SECONDS=31536000`.
4. **Sao lưu DB hằng ngày** (`pg_dump`) ra ngoài server, và thử khôi phục ít nhất một lần.
5. **Giám sát:** UptimeRobot (báo khi web sập), xem log `security` (đăng nhập sai hàng loạt), có thể thêm Sentry để bắt lỗi 500.
6. **Cập nhật:** `apt upgrade` hệ điều hành; chạy `npm audit` / `pip-audit` trước mỗi lần deploy.
7. Mật khẩu admin dài; tài khoản demo trong README phải đổi mật khẩu hoặc xoá trước khi public.

## Ghi chú về giới hạn tần suất

Giới hạn **theo IP** được nới rộng có chủ đích: cả lớp học dùng chung wifi trường nên ra cùng một IP. Giới hạn chặt nằm ở **mỗi tài khoản** và **mỗi email**. Mọi mức đều đổi được qua biến môi trường `THROTTLE_*`. Vượt giới hạn thì API trả `429 Too Many Requests`.
