# LingoPrism 🔺

> **One snap. Three languages.** – Ứng dụng học từ vựng **Tiếng Việt · Tiếng Anh · Tiếng Trung (giản thể – chuẩn đại lục / phồn thể – chuẩn Đài Loan)** bằng thị giác máy tính (YOLOv10).

Đồ án tốt nghiệp – Trường ĐH Tài nguyên và Môi trường TP.HCM.

| Thư mục | Nội dung | Công nghệ |
|---|---|---|
| `BE/` | REST API + WebSocket + Django Admin + YOLOv10 (ONNX) | Python 3.12+, Django 5.2, DRF, SimpleJWT, Channels, PostgreSQL (cube/earthdistance) |
| `FE/` | Web học viên (`/`) + Web quản trị (`/admin`) | React 19, TypeScript, Vite 6, Ant Design, Tailwind, Leaflet |
| `MOBILE/` | App Android/iOS | Flutter 3.38, GetX, dio, web_socket_channel, tflite_flutter, flutter_map |
| `AI/` | Huấn luyện & đánh giá YOLOv10 (78 lớp ↔ từ vựng) | Ultralytics, FiftyOne, Colab |

Tài liệu: [PLAN.md](PLAN.md) · [FEATURES.md](FEATURES.md)

## Chạy local (không cần Docker)

Yêu cầu: Python 3.12+, Node 20+, PostgreSQL 16+ (có `cube`, `earthdistance`), Flutter 3.x, JDK 17–24.

```bash
# 1. Database
psql -U postgres -c "CREATE DATABASE lingoprism ENCODING 'UTF8' TEMPLATE template0;"

# 2. Backend  (http://localhost:8000/api/docs/ – Swagger)
cp .env.example .env              # sửa DATABASE_URL, DJANGO_SECRET_KEY
cd BE
python -m venv .venv && .venv/Scripts/activate      # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_all         # (gồm seed_demo_activity: 22 người học với 5 tuần lịch sử học, cộng đồng, giải đấu) nguồn ngôn ngữ → 585 từ × 4 ngôn ngữ đã kiểm tra (300 gốc + 285 từ Firestore SnapLingua cũ), đề thi, POI, game hoá, tài khoản demo
mkdir -p models && cp <yolov10n.onnx> models/   # model nhận diện phía server (tuỳ chọn)
python manage.py runserver

# 3. Web  (http://localhost:5173)
cd ../FE && npm install && npm run dev

# 4. Mobile
cd ../MOBILE && flutter pub get
flutter run --dart-define=API_URL=http://10.0.2.2:8000        # máy ảo Android
flutter run --dart-define=API_URL=http://<IP-máy-tính>:8000    # điện thoại thật cùng Wi-Fi
```

### Tài khoản demo (mật khẩu chung `LingoPrism@2026`)

Chỉ trên máy dev. Trên production, `deploy/deploy.sh` đổi mật khẩu từng tài khoản demo thành mật khẩu ngẫu nhiên (lưu ở `ADMIN_PASSWORDS.txt` trên server), vì mật khẩu chung này công khai trong repo.

| Email | Vai trò |
|---|---|
| admin@lingoprism.local | Quản trị viên (web `/admin`, Django Admin `/django-admin/`) |
| staff@lingoprism.local | Giáo viên – chấm tự luận, chat hỗ trợ |
| adult@lingoprism.local | Học viên – tiếng Trung giản thể |
| taiwan@lingoprism.local | Học viên – tiếng Trung phồn thể (có Zhuyin) |
| kid@lingoprism.local | Trẻ em – tiếng Việt |

## Kiểm thử

```bash
cd BE && python -m pytest          # gồm golden test giản/phồn/đa âm/từ vùng
cd MOBILE && flutter analyze
cd FE && npm run build
```

## Dữ liệu ngôn ngữ

Học viên chỉ thấy dữ liệu **đã kiểm tra** – đối chiếu chéo tự động với CC-CEDICT (CC BY-SA 4.0), danh sách HSK, từ điển Bộ Giáo dục Đài Loan qua moedict (CC BY-ND 3.0 TW), CMUdict, Tatoeba (CC BY 2.0 FR). Chi tiết: PLAN.md §3b.

Ảnh minh họa từ vựng: ảnh thật từ Wikimedia Commons (CC0 / public domain / CC BY / CC BY-SA / GFDL), đã được duyệt từng ảnh; tác giả và giấy phép nằm trong `BE/seed/concepts/images.csv` và hiện kèm ảnh trong app. Tải lại: `python manage.py fetch_word_images`.

Lộ trình 4 cấp độ (Nhập môn → Sơ cấp → Trung cấp → Nâng cao) cho mỗi ngôn ngữ: tiếng Trung theo HSK 3.0 (HSK 1–3; từ ngoài HSK hoặc HSK 4+ xếp theo tần suất), tiếng Anh/tiếng Việt theo tần suất trong câu Tatoeba – dữ liệu ở `BE/seed/concepts/levels.csv` (có cột ghi đè tay), tính lại bằng `python manage.py build_levels`. Học xong 70% số từ của một cấp thì mở cấp tiếp, hoặc qua bài kiểm tra vượt cấp (8/10).

## Docker (khi deploy)

```bash
docker compose up -d --build
```

## Thuật toán nghiên cứu (đề cương) – `BE/apps/algorithms`

Tự cài đặt bằng Python/NumPy, không dùng thư viện cho phần lõi; chọn thuật toán đang chạy và xem thực nghiệm ở **Admin → Thuật toán AI**.

| Thuật toán | File | Dùng ở đâu | Baseline so sánh |
|---|---|---|---|
| SM-2 | `sm2.py` | lập lịch ôn (mặc định) | Leitner cũ |
| FSRS-4.5 (D/S/R) | `fsrs.py` | lập lịch ôn (tuỳ chọn) | SM-2 |
| VIP – ưu tiên ôn theo nhầm lẫn thị giác | `vip.py`, `vision.py` | thứ tự từ trong phiên ôn tập | theo hạn ôn |
| Smart Distractor (Word2Vec skip-gram tự cài) | `word2vec.py`, `distractor.py` | đáp án nhiễu trắc nghiệm | ngẫu nhiên cùng chủ đề |
| Proximity Search (grid index + Haversine) | `proximity.py` | tìm POI gần, geofencing | PostgreSQL earthdistance |
| Genetic Algorithm | `ga.py` | tối ưu 17 tham số FSRS trên lịch sử ôn | tham số FSRS mặc định |

```bash
python manage.py train_word2vec                  # ~15–20 phút trên CPU, ghi seed/cache/concept_vectors.npz
python manage.py run_algorithm_experiments       # vision, srs, ga, vip, distractor, proximity → ExperimentRun
python manage.py run_algorithm_experiments --only vision --confusion <report/confusion_matrix.json>   # khi có model YOLO tự train
```
Lịch sử ôn của người học mẫu được sinh theo mô hình trí nhớ (quên hàm mũ, `simulate.py`) và thí nghiệm VIP chạy trên người học mô phỏng – cần chạy lại khi có dữ liệu người dùng thật.
