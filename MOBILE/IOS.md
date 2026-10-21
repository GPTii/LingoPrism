# App iPhone từ máy Windows (miễn phí)

Không cần máy Mac và không cần tài khoản Apple Developer trả phí ($99/năm).

## 1. Build file .ipa trên GitHub (máy macOS miễn phí)

1. Đẩy code lên GitHub (`git push`). Mỗi lần thư mục `MOBILE/` thay đổi trên nhánh `main`, GitHub tự build.
   Hoặc build tay: repo trên GitHub → **Actions** → **iOS build** → **Run workflow**.
2. Đợi khoảng 15–25 phút, mở lần chạy đó → mục **Artifacts** → tải **LingoPrism-ios** (file zip chứa `LingoPrism.ipa`).

File `.github/workflows/ios.yml`. Repo công khai nên máy macOS của GitHub Actions miễn phí, không giới hạn số phút.

## 2. Cài lên iPhone bằng Sideloadly (Windows)

1. Cài **iTunes** và **iCloud** bản tải từ trang Apple (không dùng bản Microsoft Store), mở iTunes một lần với iPhone đã cắm cáp.
2. Tải Sideloadly: https://sideloadly.io
3. Kéo `LingoPrism.ipa` vào Sideloadly, nhập Apple ID (nên dùng Apple ID đã từng đăng nhập trên một iPhone), bấm **Start**.
4. Trên iPhone:
   * iOS 16 trở lên: **Cài đặt → Quyền riêng tư & Bảo mật → Chế độ nhà phát triển** → bật, khởi động lại máy;
   * **Cài đặt → Cài đặt chung → Quản lý VPN & thiết bị** → chọn Apple ID của bạn → **Tin cậy**.

Giới hạn của Apple ID miễn phí: app chạy được **7 ngày**, sau đó cài lại (Sideloadly có tự làm mới khi iPhone
cắm cáp hoặc cùng Wi-Fi), tối đa 3 app tự cài cùng lúc. Trước buổi bảo vệ nên cài lại để còn đủ 7 ngày.

## Khi cần lâu dài

Tài khoản Apple Developer ($99/năm) → TestFlight: gửi link cài cho người khác, app dùng được 90 ngày mỗi bản build.
