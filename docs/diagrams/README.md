# Sơ đồ phân tích thiết kế LingoPrism

Vẽ từ mã nguồn thật của máy chủ (`BE/apps/*`: 17 module, ~200 endpoint REST, 3 WebSocket), web React và app Flutter.
Nguồn của mọi sơ đồ: `src/usecase_arch.py`, `src/activity.py`, `src/sequence.py`; chạy `python docs/diagrams/src/build.py`
để ghi lại các file `.mmd` + PNG và trang này. ERD cơ sở dữ liệu ở [`docs/database/`](../database/README.md).

## Dùng trong draw.io

1. Mở [app.diagrams.net](https://app.diagrams.net) (hoặc draw.io Desktop).
2. **Sắp xếp → Chèn → Nâng cao → Mermaid…** (*Arrange → Insert → Advanced → Mermaid*).
3. Dán nội dung một file `.mmd` (hoặc một khối trong [`TAT_CA_MA_MERMAID.md`](TAT_CA_MA_MERMAID.md)) → **Chèn**.
4. Flowchart (use case, kiến trúc, activity) thành hình sửa được từng khối; sequence chèn thành một hình, bấm đúp để sửa mã.

Hoặc dán vào [mermaid.live](https://mermaid.live) để xem / xuất SVG, PNG. Ảnh PNG có sẵn cạnh mỗi file để chèn thẳng vào Word.

**Quy ước:** use case – tác nhân 👤, hệ thống ngoài 🖥 (viền đứt), «include» / «extend» là mũi tên đứt; activity – ● bắt đầu,
◉ kết thúc, hình thoi vàng là rẽ nhánh, khối xanh là việc máy chủ làm, khối đỏ là lỗi; sequence – đúng tên endpoint,
view, service và thành phần (PostgreSQL, Redis, Celery, dịch vụ ngoài) trong code.

## Use case (11 sơ đồ)

| Sơ đồ | Mã Mermaid | Ảnh |
|---|---|---|
| UC00 – Use case tổng quát hệ thống LingoPrism | [`UC00_tong_quat.mmd`](usecase/UC00_tong_quat.mmd) | [PNG](usecase/UC00_tong_quat.png) |
| UC01 – Quản lý tài khoản (apps.accounts) | [`UC01_tai_khoan.mmd`](usecase/UC01_tai_khoan.mmd) | [PNG](usecase/UC01_tai_khoan.png) |
| UC02 – Học từ vựng theo chủ đề (apps.vocab, apps.learning) | [`UC02_tu_vung.mmd`](usecase/UC02_tu_vung.mmd) | [PNG](usecase/UC02_tu_vung.png) |
| UC03 – Học & ôn tập cá nhân hoá (apps.learning, apps.literacy, apps.algorithms) | [`UC03_hoc_on_tap.mmd`](usecase/UC03_hoc_on_tap.mmd) | [PNG](usecase/UC03_hoc_on_tap.png) |
| UC04 – Bài kiểm tra (apps.quizzes) | [`UC04_kiem_tra.mmd`](usecase/UC04_kiem_tra.mmd) | [PNG](usecase/UC04_kiem_tra.png) |
| UC05 – Chụp ảnh nhận diện, hội thoại AI và dịch (apps.detection, apps.aitalk) | [`UC05_nhan_dien_ai.mmd`](usecase/UC05_nhan_dien_ai.mmd) | [PNG](usecase/UC05_nhan_dien_ai.png) |
| UC06 – Học theo vị trí (GIS, Proximity Search, Geofencing) (apps.gis, apps.algorithms.proximity) | [`UC06_vi_tri.mmd`](usecase/UC06_vi_tri.mmd) | [PNG](usecase/UC06_vi_tri.png) |
| UC07 – Game hoá và trò chơi (apps.gamification, apps.games) | [`UC07_game_hoa.mmd`](usecase/UC07_game_hoa.mmd) | [PNG](usecase/UC07_game_hoa.png) |
| UC08 – Cộng đồng, nhắn tin và hỗ trợ (apps.community, apps.chat) | [`UC08_cong_dong.mmd`](usecase/UC08_cong_dong.mmd) | [PNG](usecase/UC08_cong_dong.png) |
| UC09 – Thông báo (apps.notifications, apps.push) | [`UC09_thong_bao.mmd`](usecase/UC09_thong_bao.mmd) | [PNG](usecase/UC09_thong_bao.png) |
| UC10 – Quản trị hệ thống | [`UC10_quan_tri.mmd`](usecase/UC10_quan_tri.mmd) | [PNG](usecase/UC10_quan_tri.png) |

## Kiến trúc (5 sơ đồ)

| Sơ đồ | Mã Mermaid | Ảnh |
|---|---|---|
| AR01 – Kiến trúc tổng thể | [`AR01_kien_truc_tong_the.mmd`](architecture/AR01_kien_truc_tong_the.mmd) | [PNG](architecture/AR01_kien_truc_tong_the.png) |
| AR02 – Sơ đồ triển khai (Azure VM B2als_v2: 2 vCPU, 4 GB, ufw 22/80/443, fail2ban; docker compose lingoprism-prod) | [`AR02_trien_khai.mmd`](architecture/AR02_trien_khai.mmd) | [PNG](architecture/AR02_trien_khai.png) |
| AR03 – Các module của máy chủ (modular monolith, mỗi module một app Django) | [`AR03_module_backend.mmd`](architecture/AR03_module_backend.mmd) | [PNG](architecture/AR03_module_backend.png) |
| AR04 – Kiến trúc realtime (Django Channels + Redis) | [`AR04_realtime.mmd`](architecture/AR04_realtime.mmd) | [PNG](architecture/AR04_realtime.png) |
| AR05 – Đường ống nhận diện ảnh | [`AR05_nhan_dien.mmd`](architecture/AR05_nhan_dien.mmd) | [PNG](architecture/AR05_nhan_dien.png) |

## Activity (28 sơ đồ)

| Sơ đồ | Mã Mermaid | Ảnh |
|---|---|---|
| A01 – Đăng ký và xác minh email | [`A01_dang_ky.mmd`](activity/A01_dang_ky.mmd) | [PNG](activity/A01_dang_ky.png) |
| A02 – Đăng nhập (mật khẩu hoặc Google) | [`A02_dang_nhap.mmd`](activity/A02_dang_nhap.mmd) | [PNG](activity/A02_dang_nhap.png) |
| A03 – Quên và đặt lại mật khẩu | [`A03_quen_mat_khau.mmd`](activity/A03_quen_mat_khau.mmd) | [PNG](activity/A03_quen_mat_khau.png) |
| A04 – Duyệt chủ đề và lưu từ | [`A04_tu_vung.mmd`](activity/A04_tu_vung.mmd) | [PNG](activity/A04_tu_vung.png) |
| A05 – Phiên học từ mới / ôn tập (SRS + VIP + Smart Distractor) | [`A05_phien_hoc.mmd`](activity/A05_phien_hoc.mmd) | [PNG](activity/A05_phien_hoc.png) |
| A06 – Luyện câu | [`A06_luyen_cau.mmd`](activity/A06_luyen_cau.mmd) | [PNG](activity/A06_luyen_cau.png) |
| A07 – Luyện phát âm | [`A07_phat_am.mmd`](activity/A07_phat_am.mmd) | [PNG](activity/A07_phat_am.png) |
| A08 – Học đọc – viết tiếng Việt (trẻ em) | [`A08_doc_viet.mmd`](activity/A08_doc_viet.mmd) | [PNG](activity/A08_doc_viet.png) |
| A09 – Kiểm tra vượt cấp độ | [`A09_vuot_cap.mmd`](activity/A09_vuot_cap.mmd) | [PNG](activity/A09_vuot_cap.png) |
| A10 – Làm bài kiểm tra và chấm tự luận | [`A10_bai_kiem_tra.mmd`](activity/A10_bai_kiem_tra.mmd) | [PNG](activity/A10_bai_kiem_tra.png) |
| A11 – Chụp ảnh nhận diện và lưu từ | [`A11_nhan_dien.mmd`](activity/A11_nhan_dien.mmd) | [PNG](activity/A11_nhan_dien.png) |
| A12 – Hội thoại AI từ ảnh | [`A12_hoi_thoai_ai.mmd`](activity/A12_hoi_thoai_ai.mmd) | [PNG](activity/A12_hoi_thoai_ai.png) |
| A13 – Dịch văn bản / giọng nói (trang Dịch và trong chat) | [`A13_dich.mmd`](activity/A13_dich.mmd) | [PNG](activity/A13_dich.png) |
| A14 – Học theo vị trí: bản đồ và geofence | [`A14_vi_tri.mmd`](activity/A14_vi_tri.mmd) | [PNG](activity/A14_vi_tri.png) |
| A15 – Trò chơi | [`A15_tro_choi.mmd`](activity/A15_tro_choi.mmd) | [PNG](activity/A15_tro_choi.png) |
| A16 – Nhiệm vụ, huy hiệu, cửa hàng và giải đấu tuần | [`A16_nhiem_vu_cua_hang.mmd`](activity/A16_nhiem_vu_cua_hang.mmd) | [PNG](activity/A16_nhiem_vu_cua_hang.png) |
| A17 – Cộng đồng: đăng bài, bình luận, lưu từ trong bài | [`A17_bai_viet.mmd`](activity/A17_bai_viet.mmd) | [PNG](activity/A17_bai_viet.png) |
| A18 – Bạn bè, theo dõi, chặn và báo cáo người dùng | [`A18_ban_be_bao_cao.mmd`](activity/A18_ban_be_bao_cao.mmd) | [PNG](activity/A18_ban_be_bao_cao.png) |
| A19 – Nhóm học và chat nhóm realtime | [`A19_chat_nhom.mmd`](activity/A19_chat_nhom.mmd) | [PNG](activity/A19_chat_nhom.png) |
| A20 – Tin nhắn riêng | [`A20_tin_nhan_rieng.mmd`](activity/A20_tin_nhan_rieng.mmd) | [PNG](activity/A20_tin_nhan_rieng.png) |
| A21 – Hỏi giáo viên (chat hỗ trợ) | [`A21_ho_tro.mmd`](activity/A21_ho_tro.mmd) | [PNG](activity/A21_ho_tro.png) |
| A22 – Thông báo | [`A22_thong_bao.mmd`](activity/A22_thong_bao.mmd) | [PNG](activity/A22_thong_bao.png) |
| A23 – Quản trị: kiểm duyệt dữ liệu ngôn ngữ và duyệt từ mới | [`A23_kiem_duyet_ngon_ngu.mmd`](activity/A23_kiem_duyet_ngon_ngu.mmd) | [PNG](activity/A23_kiem_duyet_ngon_ngu.png) |
| A24 – Quản trị: quản lý POI (WebGIS) | [`A24_webgis.mmd`](activity/A24_webgis.mmd) | [PNG](activity/A24_webgis.png) |
| A25 – Quản trị: xử lý báo cáo và khoá tài khoản | [`A25_kiem_duyet_bao_cao.mmd`](activity/A25_kiem_duyet_bao_cao.mmd) | [PNG](activity/A25_kiem_duyet_bao_cao.png) |
| A26 – Quản trị: thuật toán và thực nghiệm | [`A26_thuat_toan.mmd`](activity/A26_thuat_toan.mmd) | [PNG](activity/A26_thuat_toan.png) |
| A27 – Quản trị: phản hồi nhận diện và phiên bản model | [`A27_quan_ly_nhan_dien.mmd`](activity/A27_quan_ly_nhan_dien.mmd) | [PNG](activity/A27_quan_ly_nhan_dien.png) |
| A28 – Quản trị: người dùng, đề thi, game hoá, thông báo hàng loạt, nhật ký | [`A28_quan_tri_chung.mmd`](activity/A28_quan_tri_chung.mmd) | [PNG](activity/A28_quan_tri_chung.png) |

## Sequence (28 sơ đồ)

| Sơ đồ | Mã Mermaid | Ảnh |
|---|---|---|
| S01 – Đăng ký và xác minh email | [`S01_dang_ky.mmd`](sequence/S01_dang_ky.mmd) | [PNG](sequence/S01_dang_ky.png) |
| S02 – Đăng nhập bằng mật khẩu hoặc Google, mở kết nối realtime | [`S02_dang_nhap.mmd`](sequence/S02_dang_nhap.mmd) | [PNG](sequence/S02_dang_nhap.png) |
| S03 – Quên và đặt lại mật khẩu | [`S03_quen_mat_khau.mmd`](sequence/S03_quen_mat_khau.mmd) | [PNG](sequence/S03_quen_mat_khau.png) |
| S04 – Duyệt chủ đề và lưu từ | [`S04_tu_vung.mmd`](sequence/S04_tu_vung.mmd) | [PNG](sequence/S04_tu_vung.png) |
| S05 – Phiên học / ôn tập (SM-2 hoặc FSRS, VIP, Smart Distractor) | [`S05_phien_hoc.mmd`](sequence/S05_phien_hoc.mmd) | [PNG](sequence/S05_phien_hoc.png) |
| S06 – Luyện câu | [`S06_luyen_cau.mmd`](sequence/S06_luyen_cau.mmd) | [PNG](sequence/S06_luyen_cau.png) |
| S07 – Luyện phát âm (chấm trên thiết bị) | [`S07_phat_am.mmd`](sequence/S07_phat_am.mmd) | [PNG](sequence/S07_phat_am.png) |
| S08 – Học đọc – viết tiếng Việt | [`S08_doc_viet.mmd`](sequence/S08_doc_viet.mmd) | [PNG](sequence/S08_doc_viet.png) |
| S09 – Kiểm tra vượt cấp độ | [`S09_vuot_cap.mmd`](sequence/S09_vuot_cap.mmd) | [PNG](sequence/S09_vuot_cap.png) |
| S10 – Làm bài kiểm tra và giáo viên chấm tự luận | [`S10_bai_kiem_tra.mmd`](sequence/S10_bai_kiem_tra.mmd) | [PNG](sequence/S10_bai_kiem_tra.png) |
| S11 – Chụp ảnh nhận diện và xác nhận | [`S11_nhan_dien.mmd`](sequence/S11_nhan_dien.mmd) | [PNG](sequence/S11_nhan_dien.png) |
| S12 – Hội thoại AI từ ảnh | [`S12_hoi_thoai_ai.mmd`](sequence/S12_hoi_thoai_ai.mmd) | [PNG](sequence/S12_hoi_thoai_ai.png) |
| S13 – Dịch văn bản / giọng nói | [`S13_dich.mmd`](sequence/S13_dich.mmd) | [PNG](sequence/S13_dich.png) |
| S14 – Học theo vị trí: bản đồ và geofence | [`S14_geofence.mmd`](sequence/S14_geofence.mmd) | [PNG](sequence/S14_geofence.png) |
| S15 – Trò chơi | [`S15_tro_choi.mmd`](sequence/S15_tro_choi.mmd) | [PNG](sequence/S15_tro_choi.png) |
| S16 – Nhiệm vụ, cửa hàng và giải đấu tuần | [`S16_nhiem_vu_cua_hang.mmd`](sequence/S16_nhiem_vu_cua_hang.mmd) | [PNG](sequence/S16_nhiem_vu_cua_hang.png) |
| S17 – Cộng đồng: bài viết | [`S17_bai_viet.mmd`](sequence/S17_bai_viet.mmd) | [PNG](sequence/S17_bai_viet.png) |
| S18 – Kết bạn, chặn và báo cáo người dùng | [`S18_ban_be.mmd`](sequence/S18_ban_be.mmd) | [PNG](sequence/S18_ban_be.png) |
| S19 – Nhóm học và chat nhóm realtime | [`S19_chat_nhom.mmd`](sequence/S19_chat_nhom.mmd) | [PNG](sequence/S19_chat_nhom.png) |
| S20 – Tin nhắn riêng | [`S20_tin_nhan_rieng.mmd`](sequence/S20_tin_nhan_rieng.mmd) | [PNG](sequence/S20_tin_nhan_rieng.png) |
| S21 – Hỏi giáo viên | [`S21_ho_tro.mmd`](sequence/S21_ho_tro.mmd) | [PNG](sequence/S21_ho_tro.png) |
| S22 – Thông báo realtime và thông báo đẩy | [`S22_thong_bao.mmd`](sequence/S22_thong_bao.mmd) | [PNG](sequence/S22_thong_bao.png) |
| S23 – Quản trị: kiểm duyệt bản dịch và duyệt từ mới | [`S23_kiem_duyet_ngon_ngu.mmd`](sequence/S23_kiem_duyet_ngon_ngu.mmd) | [PNG](sequence/S23_kiem_duyet_ngon_ngu.png) |
| S24 – Quản trị: quản lý POI (WebGIS) | [`S24_webgis.mmd`](sequence/S24_webgis.mmd) | [PNG](sequence/S24_webgis.png) |
| S25 – Quản trị: xử lý báo cáo người dùng | [`S25_kiem_duyet_bao_cao.mmd`](sequence/S25_kiem_duyet_bao_cao.mmd) | [PNG](sequence/S25_kiem_duyet_bao_cao.png) |
| S26 – Quản trị: thuật toán và thực nghiệm | [`S26_thuat_toan.mmd`](sequence/S26_thuat_toan.mmd) | [PNG](sequence/S26_thuat_toan.png) |
| S27 – Quản trị: phản hồi nhận diện | [`S27_quan_ly_nhan_dien.mmd`](sequence/S27_quan_ly_nhan_dien.mmd) | [PNG](sequence/S27_quan_ly_nhan_dien.png) |
| S28 – Quản trị: gửi thông báo hàng loạt | [`S28_thong_bao_hang_loat.mmd`](sequence/S28_thong_bao_hang_loat.mmd) | [PNG](sequence/S28_thong_bao_hang_loat.png) |
