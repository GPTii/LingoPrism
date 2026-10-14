# SnapLingua 📸🇬🇧
Ứng dụng học từ vựng Tiếng Anh qua **nhận diện hình ảnh** (YOLOv10 → TFLite) và **xử lý ngôn ngữ tự nhiên**, thiết kế **offline-first** với MongoDB Realm, đồng bộ dữ liệu khi có mạng.



cd /Users/admin/Desktop/snaplingua/backend/yolo_service
python main.py



## 🎯 Mục tiêu
- Học từ vựng trực quan, sinh động, gắn với ngữ cảnh thực tế.
- Cá nhân hóa lộ trình học theo tiến độ từng người.
- Học mọi lúc, mọi nơi.

## ✨ Chức năng chính
- Chụp ảnh → nhận diện vật thể → gợi ý từ vựng kèm IPA, nghĩa, ví dụ, phát âm.
- Lưu, phân loại từ vựng; Flashcard, Quiz (SRS – SM-2).
- Học ngoại tuyến; đồng bộ dữ liệu khi có mạng.
- Thống kê tiến độ, streak, heatmap, nhắc học.
- Gamification: thử thách, XP, huy hiệu, bảng xếp hạng.
- Học nhóm, chia sẻ ảnh + từ vựng.

## 🧱 Công nghệ
- **Flutter/Dart**, Java
- **MongoDB Realm Database**, MongoDB Atlas + Device Sync
- **Realm Auth** (email/password, OAuth)
- **YOLOv10**, TensorFlow Lite
- API từ điển/NLP
- State management: Provider / Riverpod

## 🚀 Cài đặt
```bash
flutter pub get
flutter run
