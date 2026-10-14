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
python manage.py seed_all         # nguồn ngôn ngữ → 300 từ × 4 ngôn ngữ đã kiểm tra, đề thi, POI, game hoá, tài khoản demo
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

## Docker (khi deploy)

```bash
docker compose up -d --build
```
