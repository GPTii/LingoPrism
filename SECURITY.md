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
| **Thư viện có lỗ hổng** (A03 Supply Chain) | `npm audit`, `osv-scanner` (Flutter): 0 lỗ hổng (28/10/2026). `pip-audit`: 7 CVE của `twisted` (phụ thuộc của daphne) chưa có bản vá chính thức; 6 nằm ở phần daphne không dùng (IMAP, IRC, telnet, XMPP, DNS), CVE-2026-115877 (header HTTP) bị nginx chặn trước – nâng cấp khi twisted 26.10 ra bản chính thức | `.github/workflows/security.yml` (mỗi push + hằng tuần) |
| Server chỉ nhận request qua Cloudflare | nginx đóng kết nối không đến từ dải IP Cloudflare (`return 444`); ufw không làm được vì Docker mở cổng bằng iptables riêng | `nginx.conf` (`geo $from_cloudflare`) |
| HTTPS bắt buộc | http → 301 https; HSTS 1 năm; TLS 1.2/1.3 với cipher có forward secrecy (Mozilla intermediate) | `nginx.conf` |
| Tài khoản demo lộ mật khẩu | mật khẩu chung `LingoPrism@2026` công khai trong repo: mỗi lần deploy, tài khoản `@lingoprism.local` nào còn dùng nó được đổi mật khẩu ngẫu nhiên và thu hồi phiên | `manage.py secure_demo_accounts`, `deploy/deploy.sh` |
| Bấm trùng / request song song (race condition) | đăng ký trùng email → 400; kết bạn khoá 2 người theo thứ tự id; mua đồ, nhận quest khoá hàng | `RegisterSerializer`, `CommunityUserViewSet.friend` |
| Ký tự NUL, tham số sai kiểu | NUL trong query/JSON → 400 (PostgreSQL không lưu được, trước đây là 500); `?before=abc` → bỏ qua | `apps/core/middleware.py`, `apps/core/params.py` |
| Cạn kết nối DB khi đông người | `CONN_MAX_AGE=0` + pool psycopg tối đa 40 kết nối mỗi process: request vượt quá chờ đến lượt thay vì lỗi (trước đây ~20 người dùng cùng lúc, rồi 200 người dùng cùng lúc, là lỗi 500 "too many clients") | `config/settings/base.py` |
| **App mobile** (OWASP MASVS) | token trong Android Keystore / iOS Keychain (`flutter_secure_storage`), không backup dữ liệu app, release chỉ HTTPS, R8 + `--obfuscate`; không SDK Facebook, không quyền `AD_ID` (chính sách Google Play cho app có trẻ em) | `TokenStorage`, `AndroidManifest.xml` |
| Redis sập kéo cả web sập | cache (nơi giữ bộ đếm giới hạn tốc độ) coi Redis sập là cache trống, ngắt mạch 10 s; giới hạn của nginx vẫn chạy | `apps/core/cache.py` |
| DB sập: request treo, luồng bị giữ | kết nối DB timeout 5 s, chờ pool tối đa 10 s; `health/` trả 503 cho công cụ giám sát; DB lên lại thì tự hồi phục sau ~3 s | `config/settings/base.py`, `apps/core/views.py` |

## Kiểm tra tự động

- `apps/core/test_authz.py` – đi qua **mọi** route API (đọc từ URL conf, endpoint mới tự được kiểm): chưa đăng nhập → 401; người học vào route staff → bị chặn; người B đụng vào ảnh, phiên học, tin nhắn, bài thi, hỗ trợ, nhóm, bài viết của người A → bị chặn và dữ liệu không đổi (OWASP API1 BOLA/IDOR); dữ liệu rác vào mọi route (người học, admin, và chủ dữ liệu) → không bao giờ 500.
- `.github/workflows/security.yml` – gitleaks (lộ secret trong lịch sử git), bandit + semgrep (code Python/Django/React), pip-audit, npm audit, osv-scanner (thư viện có CVE), trivy (Dockerfile).
- `apps/chat/test_websockets.py` – 3 kênh WebSocket: token giả / tài khoản khoá → 4401, người ngoài nhóm / đang chờ duyệt / hộp hỗ trợ của người khác → 4403, xả tin bị chặn sau 8 tin, frame > 8 KB hoặc nhị phân → đóng 4413, sự kiện không lọt sang người khác.
- `apps/core/test_bulk.py` – xoá hàng loạt chỉ trong phạm vi được phép, giữ lại mục không được xoá (kèm lý do), xoá cả file ảnh.
- Kiểm tra tải (k6, 10/2026 trên production): spike 0→200 người dùng không lỗi 5xx, soak 20 phút 99,99 % thành công, 100 kết nối WebSocket giữ 1 phút (ping p95 150 ms).
- Diễn tập khôi phục: `sh deploy/restore-drill.sh` khôi phục bản sao lưu mới nhất vào một database tạm cạnh database thật, so số dòng từng bảng, rồi xoá.

## Phải làm trên server (code không làm thay được)

1. **Đặt Cloudflare (gói Free) trước server.** DDoS tầng mạng (hàng Gbps) không app nào tự chống được, chỉ CDN chặn được. Bật "Under Attack Mode" khi bị tấn công, (đã làm: `set_real_ip_from` và chặn mọi IP không phải Cloudflare trong `nginx.conf`). Trên Cloudflare giữ **SSL/TLS → Full** (origin dùng chứng chỉ tự ký; muốn "Full (strict)" thì phải thay bằng chứng chỉ Cloudflare Origin CA trước) và bật **Always Use HTTPS**.
2. **Tường lửa:** chỉ mở 22, 80, 443 (`ufw allow 22,80,443/tcp`). SSH chỉ dùng key, tắt đăng nhập bằng mật khẩu; cài `fail2ban`.
3. **HTTPS**: Cloudflare + chứng chỉ origin; nginx đã gửi HSTS 1 năm.
4. **Sao lưu DB hằng ngày** (`deploy/backup.sh`, cron 03:00) và chép ra ngoài server; chạy `sh deploy/restore-drill.sh` định kỳ để chắc bản sao lưu khôi phục được.
5. **Giám sát:** UptimeRobot (báo khi web sập), xem log `security` (đăng nhập sai hàng loạt), có thể thêm Sentry để bắt lỗi 500.
6. **Cập nhật:** `apt upgrade` hệ điều hành; chạy `npm audit` / `pip-audit` trước mỗi lần deploy.
7. Mật khẩu admin dài; tài khoản demo trong README phải đổi mật khẩu hoặc xoá trước khi public.

## Ghi chú về giới hạn tần suất

Giới hạn **theo IP** được nới rộng có chủ đích: cả lớp học dùng chung wifi trường nên ra cùng một IP. Giới hạn chặt nằm ở **mỗi tài khoản** và **mỗi email**. Mọi mức đều đổi được qua biến môi trường `THROTTLE_*`. Vượt giới hạn thì API trả `429 Too Many Requests`.
