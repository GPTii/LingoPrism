# LingoPrism 🔺

> **One snap. Three languages.** – Ứng dụng học từ vựng **Tiếng Việt · Tiếng Anh · Tiếng Trung (giản thể / phồn thể)** bằng thị giác máy tính (YOLOv10).

Đồ án tốt nghiệp – Trường ĐH Tài nguyên và Môi trường TP.HCM.

| Thư mục | Nội dung | Công nghệ |
|---|---|---|
| `BE/` | REST API + WebSocket + Django Admin | Python 3.12+, Django 5.2, DRF, SimpleJWT, Channels, PostgreSQL |
| `FE/` | Web học viên (`/`) + Web quản trị (`/admin`) | React 19, TypeScript, Vite 6, Ant Design, Tailwind |
| `MOBILE/` | App Android/iOS | Flutter, GetX |
| `AI/` | Huấn luyện & đánh giá YOLOv10, thực nghiệm thuật toán | Python, Ultralytics |

Tài liệu: [PLAN.md](PLAN.md) (kế hoạch) · [FEATURES.md](FEATURES.md) (danh sách chức năng).

## Chạy local (không cần Docker)

Yêu cầu: Python 3.12+, Node 20+, PostgreSQL 16+ (có sẵn extension `cube`, `earthdistance`), Flutter 3.x.

```bash
# 1. Database
psql -U postgres -c "CREATE DATABASE lingoprism;"

# 2. Backend
cp .env.example .env            # điền DATABASE_URL, DJANGO_SECRET_KEY...
cd BE
python -m venv .venv
.venv/Scripts/activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver      # http://localhost:8000/api/docs/

# 3. Web
cd ../FE
npm install
npm run dev                     # http://localhost:5173

# 4. Mobile
cd ../MOBILE
flutter pub get
flutter run --dart-define=API_URL=http://10.0.2.2:8000
```

## Docker (khi deploy)

```bash
docker compose up -d --build
```
