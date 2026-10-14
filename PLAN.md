# LingoPrism — Kế hoạch hoàn thiện hệ thống (Web + App + DB + YOLOv10)

> Repo: https://github.com/GPTii/LingoPrism
> Phạm vi bản plan này: **toàn bộ hệ thống chạy được end-to-end** (Django REST API, web React cho học viên + Admin, app Flutter, PostgreSQL/PostGIS, YOLOv10, realtime chat, Docker).
> Cấu trúc repo: `BE/` (Django API) · `FE/` (web React) · `MOBILE/` (Flutter) · `AI/` (YOLOv10, thực nghiệm).
> **Chưa bao gồm** các thuật toán nghiên cứu: VIP, FSRS, Smart Distractor, Proximity Search tự cài đặt, GA → làm ở giai đoạn sau (Phase 5). Plan chỉ **chuẩn bị sẵn dữ liệu và chỗ cắm** cho chúng.

## ✅ Trạng thái (cập nhật 15/10/2026)

| Hạng mục | Trạng thái |
|---|---|
| Phase 0 – khởi tạo repo, Django, React, chuyển app sang `MOBILE/` | ✅ Xong |
| Phase 1 – tài khoản, từ vựng 3 ngôn ngữ (300 khái niệm × vi/en/zh-Hans/zh-Hant, 100% verified), pipeline kiểm tra + golden test | ✅ Xong |
| Phase 2 – học tập/SRS, game hoá (XP, streak, quest, league, shop, badge), thông báo realtime, đề thi + chấm tự luận | ✅ Xong (BE + Web + App) |
| Phase 3 – cộng đồng, nhóm, chat realtime, chat hỗ trợ, nhận diện YOLOv10 (server + on-device), GIS/POI + geofence, dashboard | ✅ Xong (BE + Web + App) |
| MOBILE – bỏ Firestore/Realm, chuyển toàn bộ sang REST + WebSocket; màn hình mới: đề thi, bản đồ POI, hỏi giáo viên, chọn ngôn ngữ / giản–phồn | ✅ Biên dịch sạch (`flutter analyze` 0 lỗi) |
| AI – pipeline YOLOv10 (78 lớp), notebook Colab, `register_model` | ✅ Sẵn sàng – **cần chạy train trên Colab (GPU)** |
| Docker – `docker-compose.yml` (dev), `docker-compose.prod.yml` + nginx (prod) | ✅ File cấu hình – chưa deploy |
| Phase 5 – thuật toán nghiên cứu (SM-2, FSRS, VIP, Smart Distractor, Proximity Search tự cài, GA) | ⏳ Chưa làm |

Kiểm thử: BE 73 test (pytest) · smoke test 18 luồng API thật · FE `npm run build` · MOBILE `flutter analyze`.
Lưu ý môi trường: Windows chỉ build được Android; JDK 24 cần Gradle ≥ 8.14 (đã nâng wrapper lên 8.14.3).

---

## 0. Hiện trạng SnapLingua (đầu vào để chuyển sang)

| Thành phần | Hiện có | Xử lý |
|---|---|---|
| Flutter app | 219 file, ~63k dòng, GetX, 29 module màn hình (auth, onboarding, survey, home, vocab list/topic/flashcard, learning session, review, camera detection, community, group chat, leaderboard, shop, streak, notification, profile…) | **Giữ UI**, thay tầng dữ liệu |
| Tầng dữ liệu app | `firestore_service.dart` (2171 dòng) + 38 model Firestore + Realm (21 file) | **Bỏ Firestore/Realm**, thay bằng REST API + cache Hive |
| Backend | Spring Boot Kotlin (chỉ auth) | **Bỏ**, viết lại Django |
| YOLO | FastAPI + YOLOv8m COCO; app chạy TFLite YOLOv8/YOLO11 (format `[1,84,N]`) | **Thay bằng YOLOv10 tự train**; sửa parser output YOLOv10 `[1,300,6]` |
| Từ điển | Gọi `dictionaryapi.dev` + Google Translate lúc runtime | **Seed dữ liệu vào DB** (vi/en/zh), không phụ thuộc API ngoài khi demo |
| Assets | Mascot chim cánh cụt, streak, rank, nhóm, âm thanh, font Gilroy | Giữ nguyên |
| ⚠️ Bảo mật | `backend/.../application.yml` lộ mật khẩu MongoDB Atlas | Đổi mật khẩu, không đưa lên git |

---

## 1. Kiến trúc tổng thể

```
 📱 MOBILE (Flutter)              🌐 FE (React: / học viên, /admin quản trị)
      │ REST (JWT) + WebSocket          │ REST (JWT) + WebSocket   ← dùng CHUNG 1 bộ API
      ▼                                  ▼
 ┌──────────── Docker Compose ─────────────────────────────────┐
 │ nginx (HTTPS; phục vụ file build FE; proxy /api /ws /media)  │
 │   └─► django (daphne ASGI): DRF REST API + Django Admin      │
 │        (thao tác thô) + Channels (chat, notification)        │
 │        └─► detection: YOLOv10 inference (ultralytics/onnx)   │
 │   ├─► postgis (PostgreSQL 16 + PostGIS 3.4)                  │
 │   ├─► redis (channel layer, cache, Celery broker)            │
 │   └─► celery worker (gửi thông báo, tác vụ nặng)             │
 └──────────────────────────────────────────────────────────────┘
```

**Công nghệ chốt**
- BE: Python 3.12, Django 5.x, DRF, SimpleJWT, drf-spectacular (Swagger), Channels + channels-redis, daphne, Celery, GeoDjango, Pillow, ultralytics/onnxruntime, pypinyin, django-environ.
- API: **REST API** (JSON, DRF) cho mọi chức năng + **WebSocket** (Channels) cho realtime; xác thực **JWT** (`Authorization: Bearer`); tài liệu Swagger tự sinh. Web và mobile dùng chung.
- Web (FE): React 18 + TypeScript + Vite, React Router, TanStack Query (gọi API/cache), axios (interceptor JWT refresh), Zustand (state đăng nhập); **khu Admin**: Ant Design + Ant Design Charts; **khu học viên**: Tailwind CSS + framer-motion (lật thẻ, hiệu ứng) thiết kế giống app; react-leaflet + OpenStreetMap (bản đồ POI); Web Speech API (phát âm).
- Mobile (thư mục `MOBILE/`): Flutter 3.x, GetX (giữ), dio (+ interceptor JWT refresh), hive (cache offline), web_socket_channel, tflite_flutter, camera, flutter_map + geolocator, flutter_tts, firebase_messaging (**chỉ** push notification – tùy chọn).
- DB: PostgreSQL 16 + PostGIS.
- AI (thư mục `AI/`): YOLOv10 (ultralytics), train trên Colab/Kaggle, export ONNX (server) + TFLite (on-device).

---

## 2. Cấu trúc repo

```
LingoPrism/
├── BE/                         # Django
│   ├── config/                 # settings/{base,dev,prod}.py, urls.py, asgi.py, celery.py
│   ├── apps/
│   │   ├── accounts/           # User, hồ sơ, vai trò, Google login, đổi/quên mật khẩu
│   │   ├── vocab/              # Language, Topic, Word, WordTranslation
│   │   ├── learning/           # PersonalWord (trạng thái SRS), StudySession, SessionItem, ReviewLog
│   │   ├── quizzes/            # Question, Exam, Submission, Answer, chấm tự luận
│   │   ├── detection/          # Photo, Detection, DetectionItem, ModelVersion, API /detect
│   │   ├── gamification/       # XP, streak, Badge, Quest, League, Shop/Item, Inventory
│   │   ├── community/          # Post, Comment, Like, Report, Group, GroupMember, Follow
│   │   ├── chat/               # GroupMessage, SupportConversation/Message, Channels consumers
│   │   ├── notifications/      # Notification, Settings, DeviceToken, push
│   │   ├── gis/                # POI, PoiTopic, geofence (PostGIS)
│   │   ├── algorithms/         # (trống – Phase 5: sm2, fsrs, vip, distractor, proximity, ga)
│   │   └── dashboard/          # API thống kê cho trang Admin, audit log
│   ├── fixtures/  seed/
│   ├── Dockerfile  requirements.txt  pytest.ini
├── FE/                         # Web React + Vite + TypeScript
│   ├── src/
│   │   ├── api/                # axios client, endpoints, types (sinh từ OpenAPI)
│   │   ├── auth/               # đăng nhập, guard theo role
│   │   ├── layouts/            # LearnerLayout, AdminLayout
│   │   ├── pages/learner/      # home, topics, flashcard, review, quiz, exam, camera, community, chat, map, shop, profile…
│   │   ├── pages/admin/        # dashboard, users, vocab, questions, exams, grading, pois, moderation, notifications, support, detections…
│   │   ├── components/  hooks/  realtime/ (WebSocket)
│   ├── Dockerfile (node build → nginx)  vite.config.ts
├── MOBILE/                     # Flutter app (chuyển từ SnapLingua)
├── AI/                         # YOLOv10: data.yaml, scripts (collect/split/train/export/eval), notebooks
├── deploy/nginx/               # nginx.conf (dev & prod)
├── docker-compose.yml          # dev
├── docker-compose.prod.yml     # prod (HTTPS)
├── .env.example  .gitignore  README.md  PLAN.md
```

---

## 3. Thiết kế CSDL (PostgreSQL/PostGIS)

Ánh xạ từ 38 model Firestore cũ + bổ sung theo đề cương (đa ngôn ngữ, đề thi, POI, chat hỗ trợ).

| App | Bảng | Ghi chú / nguồn cũ |
|---|---|---|
| accounts | `User` (email, display_name, avatar, role: admin/staff/learner, learner_type: kid/adult, **learning_languages**, **zh_script: hans/hant** (người học tự chọn, đổi được trong cài đặt), status, scales_balance, gems_balance), `UserGoal`, `AuthProvider`, `SurveyAnswer` | firestore_user, user_goal, auth_provider, user_security, survey |
| vocab | `Language` (**vi, en, zh-Hans, zh-Hant** – 2 dạng chữ Hán là 2 "ngôn ngữ" riêng), `Topic` (name đa ngữ, icon, owner, visibility, audience kid/adult), `Word` (concept: image, yolo_label, part_of_speech, difficulty), `WordTranslation` (word, language, text, ipa (en), pinyin + pinyin_numbered + zhuyin (zh), measure_word (zh), accepted_variants, meaning_vi, level (HSK/TOCFL/CEFR), audio_url, **status** draft/verified/flagged/rejected, **sources** JSONB, verified_method auto/manual, verified_at), `ExampleSentence` (word, language, text, translation_vi, translation_en, source, source_id, license, status), `TopicWord`, `ErrorReport` (người học báo lỗi) | dictionary_word, topic — **mở rộng sang 3 ngôn ngữ, xem mục 3b** |
| learning | `PersonalWord` (user, word, target_language, status, source: camera/manual/topic, srs_stage, ease, interval_days, due_at, repetitions, wrong_streak, forget_count, last_reviewed_at), `StudySession`, `SessionItem`, **`ReviewLog`** (mỗi lần trả lời: rating, response_ms, kết quả, trạng thái trước/sau) | personal_word, study_session, session_item — **ReviewLog là dữ liệu cho SM-2/FSRS/GA sau này** |
| quizzes | `Question` (type: mcq/essay/fill/listen/image, word, prompt, options JSONB, answer), `Exam` (title, topic, language, time_limit, is_published), `ExamQuestion`, `Submission` (user, exam, score, status: submitted/graded), `Answer` (essay text, auto_correct, grader, score, feedback) | **mới** (đề cương: trắc nghiệm + tự luận + chấm bài) |
| detection | `ModelVersion` (name, map50, file), `Photo` (user, image, w, h, source), `Detection` (photo, model_version, inference_ms, device: server/on-device), **`DetectionItem`** (label, confidence, bbox, top-k candidates JSONB, mapped_word, user_confirmed/selected) | detection, detection_word, photo — **lưu đủ confidence + top-k để làm VIP sau** |
| gamification | `XpTransaction`, `DailyProgress`, `Streak`, `Badge` (code, sticker, condition_type, threshold), `UserBadge`, `Quest`/`UserQuest` (daily/monthly), `LeagueTier`, `LeagueCycle`, `LeagueMember`, `Item`, `UserInventory` | giữ nguyên ý nghĩa bản cũ |
| community | `Post`, `PostWord`, `PostComment`, `PostLike`, `PostReport`, `Group`, `GroupMember`, `UserFollow` | giữ |
| chat | `GroupMessage`, `SupportConversation` (learner ↔ staff), `SupportMessage` (status: sent/delivered/read) | group_message + **chat hỗ trợ mới** |
| notifications | `Notification`, `NotificationSetting`, `DeviceToken` | giữ |
| gis | `Poi` (name, category, `location PointField(srid=4326)`, radius_m, address), `PoiTopic` (poi ↔ topic), `GeofenceEvent` (user, poi, entered_at) | **mới**; index GiST |
| web/admin | `AdminAction` (audit log) | admin_action |

**Index quan trọng**: `PersonalWord(user, due_at)`, `ReviewLog(user, created_at)`, `DetectionItem(label)`, `Poi.location` (GiST), `WordTranslation(language, text)`.

---

## 3b. Chất lượng ngôn ngữ — Việt · Anh · Trung (giản thể & phồn thể)

> Nguyên tắc số 1: **app dạy ngôn ngữ không được dạy sai.** Không dịch máy lúc chạy, không tự chuyển giản ↔ phồn từng chữ, không sinh pinyin từng chữ. Học viên **chỉ thấy dữ liệu đã kiểm tra (status = verified)**.

### Hai biến thể tiếng Trung (người học tự chọn khi onboarding, đổi được trong cài đặt)

| | `zh-Hans` – Giản thể (chuẩn Trung Quốc đại lục) | `zh-Hant` – Phồn thể (chuẩn Đài Loan) |
|---|---|---|
| Mặt chữ | Giản thể theo 通用规范汉字表 | Phồn thể theo chuẩn Bộ Giáo dục Đài Loan |
| Từ vựng vùng | Từ đại lục (土豆, 出租车, 自行车) | Từ Đài Loan (馬鈴薯, 計程車, 腳踏車) — **có thể là từ khác hẳn**, không phải bản chuyển chữ |
| Phiên âm | Pinyin có dấu thanh (đọc chuẩn đại lục) | Pinyin (đọc chuẩn Đài Loan, VD 垃圾 lèsè) + **Zhuyin 注音** (bật/tắt) |
| Cấp độ | HSK 3.0 (1–9) | TOCFL |
| Phát âm TTS | giọng `zh-CN` | giọng `zh-TW` |
| Font | Noto Sans SC | Noto Sans TC |

- Mỗi biến thể là **một `WordTranslation` riêng** (text, pinyin, zhuyin, lượng từ, ví dụ riêng) → không bao giờ "suy" bản này từ bản kia.
- Tiến độ SRS gắn với *khái niệm từ* (`Word`) + ngôn ngữ `zh` → đổi giản/phồn không mất tiến độ; `ReviewLog` lưu thêm `script` để thống kê.

### Nguồn dữ liệu chuẩn (thay cho Google Translate/dictionaryapi lúc runtime)

| Dữ liệu | Nguồn | Giấy phép |
|---|---|---|
| zh-Hans: mặt chữ, pinyin, nghĩa Anh | **CC-CEDICT** (theo *từ*, có sẵn cặp giản/phồn) | CC BY-SA 4.0 |
| zh-Hans: cấp độ | Danh sách từ **HSK 3.0** | công khai |
| zh-Hant: mặt chữ chuẩn, cách đọc Đài Loan, Zhuyin | **Từ điển Bộ Giáo dục Đài Loan** (教育部重編國語辭典, dữ liệu mở qua moedict) | CC BY-ND 3.0 TW (ghi nguồn, không sửa nội dung) |
| zh-Hant: cấp độ | Danh sách từ **TOCFL 8000** | công khai |
| Câu ví dụ zh/en (+ bản dịch) | **Tatoeba** – chỉ lấy câu của người bản ngữ, có liên kết bản dịch | CC BY 2.0 FR |
| en: IPA (giọng Mỹ), từ loại | **CMUdict** (chuyển ARPAbet → IPA bằng bảng cố định) + Wiktionary (kaikki.org) | BSD / CC BY-SA |
| vi: nghĩa, ví dụ | Wiktionary tiếng Việt + tự soạn (chủ dự án là người Việt, tự kiểm) | CC BY-SA |
| Chuyển đổi giản↔phồn | **OpenCC** (theo cụm từ, profile `s2twp`/`tw2sp`) — **chỉ dùng để đối chiếu**, không dùng làm dữ liệu | Apache 2.0 |

Trang "Giới thiệu/Nguồn dữ liệu" trên web + app ghi đầy đủ nguồn và giấy phép.

### Quy trình kiểm tra tự động ("duyệt" bằng đối chiếu chéo – không cần người biết tiếng Trung)

```
CSV khái niệm từ (vi/en + yolo_label)  →  import_sources  →  build_translations
   →  validate_language_data  →  verified ✅  (học viên thấy)
                              →  flagged ⚠️  (vào "Hàng chờ kiểm tra" trên Admin – chủ dự án xem & quyết định)
                              →  rejected ❌
```

Một bản dịch tiếng Trung chỉ được `verified` khi **TẤT CẢ** điều kiện đúng:
1. **Có mặt trong nguồn chuẩn** của biến thể đó: zh-Hans tồn tại nguyên dạng trong CC-CEDICT; zh-Hant tồn tại nguyên dạng trong từ điển Bộ GD Đài Loan.
2. **Pinyin khớp nguồn**: zh-Hans khớp CC-CEDICT **và** khớp pypinyin (chế độ cụm từ); zh-Hant lấy từ từ điển Bộ GD. Lệch → `flagged`.
3. **Zhuyin khớp**: Zhuyin của nguồn = Zhuyin sinh từ pinyin bằng bảng âm tiết 1–1.
4. **Thuần chữ**: trường zh-Hant không chứa chữ chỉ có ở giản thể; trường zh-Hans không chứa chữ chỉ có ở phồn thể (kiểm bằng bảng ký tự OpenCC).
5. **Quan hệ giản↔phồn hợp lệ**: `tw2sp(zh-Hant) == zh-Hans`, nếu khác thì phải được đánh dấu `regional_difference` (từ vùng khác nhau như 馬鈴薯/土豆) và có trong cả 2 nguồn — nếu không → `flagged`.
6. **Số âm tiết pinyin = số chữ Hán** (xử lý riêng 儿化), dấu thanh hợp lệ.
7. **Danh từ phải có lượng từ** (个/個, 隻/只, 張/张, 把…) lấy từ CC-CEDICT (`CL:`), có kiểm thuần chữ như trên.
8. **Unicode sạch**: chuẩn hoá NFC; cấm CJK Compatibility Ideographs (U+F900–FAFF, U+2F800–2FA1F) và ký tự lạ lẫn từ copy-paste.

Tiếng Anh: từ phải có trong CMUdict/Wiktionary, IPA giọng Mỹ thống nhất. Tiếng Việt: chuẩn hoá NFC, **một kiểu bỏ dấu thống nhất** (tự động chuẩn hoá *hòa/hoà*, *thủy/thuỷ* về một kiểu), kiểm chính tả bằng bảng âm tiết tiếng Việt hợp lệ.

Câu ví dụ: chỉ lấy câu Tatoeba của người bản ngữ; câu tiếng Trung **chỉ hiển thị ở dạng chữ gốc của nó** nếu không có bản tương ứng dạng kia trong Tatoeba (không tự chuyển câu bằng máy); bản dịch tiếng Việt do chủ dự án kiểm.

### "Bộ đề vàng" (golden test) — chạy trong CI, sai là build fail
Tập các ca dễ sai được viết tay làm unit test, ví dụ:
- 头发 ↔ **頭髮** (không phải 頭發), 面条 ↔ **麵條**, 后面 ↔ **後面**, 一只猫 ↔ **一隻貓**, 干净 ↔ **乾淨**, 里面 ↔ **裡面**
- 土豆 (zh-Hans) ↔ **馬鈴薯** (zh-Hant, từ vùng), 出租车 ↔ **計程車**, 自行车 ↔ **腳踏車**
- Đa âm: 银**行** yínháng / **行**走 xíngzǒu, **长**大 zhǎngdà / **长**度 chángdù, 音**乐** yīnyuè / 快**乐** kuàilè
- Cách đọc khác vùng: 垃圾 lājī (zh-Hans) / lèsè (zh-Hant)

### Hiển thị, phát âm, chấm bài
- Web: thẻ `lang="zh-Hans"` / `lang="zh-Hant-TW"` + font Noto Sans SC/TC (tránh Han unification hiển thị sai nét). Flutter: `Text(locale: Locale.fromSubtags(languageCode: 'zh', scriptCode: 'Hant', countryCode: 'TW'))` + font TC/SC đóng gói sẵn.
- TTS: chọn đúng giọng zh-CN / zh-TW / en-US / vi-VN; nếu máy không có giọng phù hợp → báo cho người dùng (không phát bằng giọng sai).
- Chấm điền từ/tự luận: chấp nhận `accepted_variants` hợp lệ (VD 裡/裏), **không chấp nhận chữ giản thể khi đang học phồn thể** (và ngược lại); cho phép trả lời bằng pinyin có dấu/số thanh ở chế độ luyện phát âm.
- Nút **"Báo lỗi"** trên mọi thẻ từ → `ErrorReport` → từ bị chuyển `flagged` nếu nhiều người báo.
- Ghi chú cho Phase 5: Smart Distractor **không được** chọn từ đồng nghĩa hoặc biến thể vùng (VD 土豆 khi đáp án là 馬鈴薯) làm đáp án sai.

---

## 4. Backend API (DRF, prefix `/api/v1/`)

| Nhóm | Endpoint chính |
|---|---|
| Auth | `POST auth/register`, `auth/login` (JWT), `auth/refresh`, `auth/google` (verify id_token), `auth/password/forgot` → `verify` → `reset`, `auth/password/change` |
| Hồ sơ | `GET/PATCH me`, `me/goal`, `me/survey`, `me/stats` (streak, XP, heatmap), `users/{id}` (public profile) |
| Từ vựng | `languages`, `topics` (lọc theo language/audience), `topics/{id}/words`, `words?search=`, `words/{id}` |
| Từ cá nhân | `my-words` CRUD, `my-words/due` (cần ôn hôm nay), `my-words/import-topic/{id}` |
| Học tập | `sessions` (tạo phiên learn/review → server trả danh sách item + câu hỏi), `sessions/{id}/answer` (ghi ReviewLog, cập nhật SRS cơ bản, cộng XP), `sessions/{id}/finish` |
| Đề thi | `exams`, `exams/{id}/start`, `submissions/{id}/submit`, `submissions/me`, (staff) `submissions/{id}/grade` |
| Nhận diện | `POST detect` (multipart ảnh → YOLOv10 server → items + từ vựng 3 ngôn ngữ), `POST detections/log` (app gửi kết quả on-device), `detections/{id}/confirm` (chọn từ để lưu) |
| Gamification | `gamification/summary`, `quests/today`, `quests/{id}/claim`, `badges/me`, `leaderboard?scope=league|friends`, `shop/items`, `shop/buy`, `inventory` |
| Cộng đồng | `posts` (feed, tạo, like, comment, report), `groups` (CRUD, join/approve, members), `follows` |
| Chat | `groups/{id}/messages` (lịch sử, phân trang), `support/conversations`, `support/conversations/{id}/messages` |
| Thông báo | `notifications`, `notifications/{id}/read`, `notification-settings`, `devices` (đăng ký FCM token) |
| GIS | `pois/nearby?lat=&lng=&radius=` (PostGIS `ST_DWithin` – sẽ là baseline), `pois/{id}/topics`, `geofence/enter` |
| Docs | `/api/schema/`, `/api/docs/` (Swagger) |

**WebSocket (Channels)**: `ws/groups/{id}/` (chat nhóm), `ws/support/{conv_id}/` (chat hỗ trợ), `ws/notifications/` (thông báo realtime, đồng bộ tiến độ/kết quả web ↔ app). Xác thực bằng JWT trong query string.

**SRS tạm thời**: dùng lại logic cũ của app (srs_stage/ease/interval) đưa lên server, viết sau interface `Scheduler` để Phase 5 thay bằng SM-2 chuẩn / FSRS / SM-2+VIP mà không sửa API.

**Câu hỏi trắc nghiệm tạm thời**: distractor chọn ngẫu nhiên cùng topic, viết sau interface `DistractorProvider` → Phase 5 thay bằng Smart Distractor.

---

## 5. Website (FE – React)

Một project React, hai khu vực, đăng nhập chung (JWT); tài khoản `admin`/`staff` mới vào được `/admin`. Mọi dữ liệu lấy qua REST API của BE → học trên web hay app đều đồng bộ.

**Khu học viên** (`/` – giao diện responsive, chức năng như app mobile):
- Đăng ký/đăng nhập (email + Google), onboarding/khảo sát, hồ sơ, mục tiêu, cài đặt thông báo
- Dashboard: streak, XP, heatmap, từ cần ôn hôm nay
- Duyệt chủ đề/từ vựng 3 ngôn ngữ (phát âm bằng Web Speech API)
- Flashcard, luyện tập, làm đề thi (trắc nghiệm + tự luận), xem kết quả & lịch sử
- Upload ảnh → nhận diện YOLOv10 → lưu từ
- Bản đồ POI quanh tôi (Leaflet), gợi ý chủ đề theo vị trí
- Cộng đồng (bài đăng ảnh + từ, like, bình luận), nhóm học, chat nhóm + chat với người hỗ trợ (realtime), thông báo realtime
- Bảng xếp hạng/league, huy hiệu, nhiệm vụ ngày/tháng, shop vật phẩm, streak
- Chế độ trẻ em (học tiếng Việt, giao diện to, mascot, sticker)

**Khu Admin / Staff** (`/admin` – Ant Design; Django Admin ở `/django-admin/` chỉ dùng cho thao tác thô khi dev):
- Dashboard thống kê: người dùng mới, DAU, số lượt học, số lượt nhận diện, độ chính xác theo lớp (Chart.js)
- Quản lý người dùng, phân quyền (admin/staff/learner), khóa tài khoản
- Quản lý ngôn ngữ, chủ đề, từ vựng (import/export CSV), ảnh minh họa
- Ngân hàng câu hỏi, tạo đề, xuất bản đề; **chấm bài tự luận**
- Kiểm duyệt bài đăng/bình luận bị báo cáo
- WebGIS: quản lý POI trên bản đồ (thêm/sửa/kéo thả), gán chủ đề, bán kính geofence
- Gửi thông báo hàng loạt; hộp thư chat hỗ trợ
- Nhật ký nhận diện (ảnh, label, confidence), quản lý phiên bản model YOLO
- Quản lý huy hiệu, nhiệm vụ, vật phẩm shop, mùa giải league

---

## 6. Flutter app (MOBILE) – chuyển đổi từ SnapLingua

1. Copy `SnapLingua-main/` → `MOBILE/`, đổi tên app **LingoPrism**, package `com.lingoprism.app`, icon/splash mới.
2. Gỡ `realm`, `realm_generator`, `cloud_firestore`, `firebase_auth`, `hive_generator` comment, `sqflite` (nếu không dùng), Realm models + `realm_service.dart` + `firestore_service.dart`.
3. Tạo tầng dữ liệu mới:
   - `core/network/api_client.dart` (dio, baseUrl từ `--dart-define=API_URL`, interceptor gắn/refresh JWT, xử lý lỗi)
   - `data/models/*` (DTO JSON thay cho firestore_*), `data/repositories/*` (auth, vocab, learning, quiz, detection, gamification, community, chat, notification, gis)
   - `data/local/cache_service.dart` (Hive: cache topics/words/my-words + hàng đợi kết quả học offline → sync khi có mạng)
   - `data/realtime/ws_client.dart` (WebSocket, tự reconnect)
4. Thay lần lượt từng service cũ (auth → vocab → learning/review → camera → gamification/quest/streak → community/chat → notification → profile) gọi repository mới; controller GetX giữ nguyên nhiều nhất có thể.
5. Camera/YOLOv10:
   - On-device: TFLite YOLOv10n tự train, **viết lại parser** cho output NMS-free `[1, 300, 6]` (x1,y1,x2,y2,score,class), labels mới.
   - Chế độ server: gửi ảnh `POST /detect` khi có mạng (model lớn hơn, chính xác hơn).
   - Màn kết quả: hiện từ 3 ngôn ngữ (vi/en/zh + IPA/pinyin + phát âm TTS), chọn từ để lưu; gửi log detection (confidence, top-k) về server.
6. Màn hình mới: chọn ngôn ngữ học + đối tượng (trẻ em/người lớn) + **dạng chữ Hán: giản thể (đại lục) / phồn thể (Đài Loan)** ở onboarding/survey (đổi được trong cài đặt; bật/tắt Zhuyin); font Noto Sans SC/TC + locale đúng cho chữ Hán; nút Báo lỗi trên thẻ từ; **chế độ trẻ em** (học tiếng Việt, giao diện to, sticker, mascot chim cánh cụt, phần thưởng); làm đề thi + xem kết quả; bản đồ POI gần đây + thông báo khi vào geofence; chat hỗ trợ.
7. Xóa module `debug`, dữ liệu giả (`i.pravatar.cc`), URL IP cứng.
8. Build Android APK (release). ⚠️ iOS cần máy Mac để build – trên Windows chỉ build được Android.

---

## 7. YOLOv10 (track chạy song song từ tuần đầu)

Thư mục `AI/`.

1. **Chọn lớp vật thể**: 40–60 lớp gắn với chủ đề từ vựng (đồ dùng học tập, nhà bếp, phòng khách, trái cây, con vật, phương tiện, quần áo…). Mỗi lớp = 1 `Word` trong DB (`yolo_label`).
2. **Dữ liệu**: lấy từ COCO/Open Images/Roboflow Universe cho các lớp có sẵn + tự chụp bổ sung ở Việt Nam (đồ vật đặc trưng). Mục tiêu ≥ 150–300 ảnh/lớp.
3. **Gán nhãn & làm sạch**: Roboflow hoặc Label Studio, format YOLO; chia train/val/test = 70/20/10.
4. **Huấn luyện**: fine-tune `yolov10n` (app) và `yolov10s`/`m` (server) từ pretrained COCO trên Colab/Kaggle GPU; augmentation; lưu `AI/runs/`.
5. **Đánh giá**: Precision, Recall, mAP50, mAP50-95, **confusion matrix** (lưu file → dùng cho VIP Phase 5), phân bố confidence.
6. **Export**: ONNX (server, onnxruntime CPU) + TFLite float16 (app). Đăng ký vào `ModelVersion`.
7. **Tích hợp**: `apps/detection/inference.py` load model 1 lần; endpoint `/detect`; app on-device; ghi log đầy đủ.

---

## 8. Dữ liệu mẫu ("đầy đủ dữ liệu")

Lệnh `python manage.py seed_all` (idempotent) tạo:
- 4 "ngôn ngữ": vi, en, zh-Hans, zh-Hant
- ~20 chủ đề (gắn audience kid/adult), **≥ 600 khái niệm từ**, mỗi từ đủ vi / en (IPA) / zh-Hans (pinyin, lượng từ, HSK) / zh-Hant (pinyin, zhuyin, lượng từ, TOCFL), câu ví dụ + dịch, ảnh minh họa; toàn bộ lớp YOLO đều có từ tương ứng
  - Nguồn & quy trình kiểm tra: **xem mục 3b** (CC-CEDICT, từ điển Bộ GD Đài Loan, HSK, TOCFL, Tatoeba, CMUdict). Danh sách khái niệm tự soạn (CSV trong `BE/seed/`), phần còn lại sinh bằng lệnh `build_translations` + `validate_language_data`
  - Chỉ seed vào trạng thái `verified` những từ qua hết bộ kiểm tra; số từ `flagged` được xử lý trong Hàng chờ kiểm tra
- Ngân hàng câu hỏi tự sinh từ từ vựng (mcq/điền từ/nghe/ảnh) + ~10 đề thi mẫu (có câu tự luận)
- Huy hiệu, nhiệm vụ ngày/tháng, league tiers, vật phẩm shop (lấy từ dữ liệu app cũ)
- ~50 POI quanh TP.HCM (trường ĐH TN&MT 236B Lê Văn Sỹ, chợ, siêu thị, bệnh viện, công viên, sân bay, bến xe…) gắn chủ đề
- Tài khoản demo: `admin`, `staff` (chấm bài/hỗ trợ), `kid_demo`, `adult_demo` + ~30 user giả có lịch sử học, review log, bài đăng, nhóm, tin nhắn → dashboard và bảng xếp hạng có số liệu

---

## 9. Docker & triển khai

- `docker-compose.yml` (dev): django (runserver/daphne + reload), postgis, redis, celery; FE chạy `npm run dev` (Vite proxy `/api`, `/ws` → django).
- `docker-compose.prod.yml`: django (daphne), celery, postgis (volume), redis, nginx (HTTPS Let's Encrypt/Cloudflare). FE build multi-stage (node build → copy `dist/` vào nginx); nginx phục vụ SPA + proxy `/api`, `/ws`, `/media`; `entrypoint.sh` chạy `migrate` + `collectstatic`.
- `.env.example`: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, `REDIS_URL`, `GOOGLE_CLIENT_ID`, `EMAIL_*`, `YOLO_MODEL_PATH`, `FCM_*`.
- Server đề xuất: VPS 2 vCPU / 4 GB RAM (Ubuntu), tên miền + HTTPS. Demo offline: chạy compose trên laptop, điện thoại cùng Wi-Fi.
- Deploy: `git pull && docker compose -f docker-compose.prod.yml up -d --build`.
- (Tùy chọn) GitHub Actions: chạy test BE + `flutter analyze` mỗi lần push.

---

## 10. Lộ trình (15/10 → 12/11/2026), sau đó Phase 5 thuật toán

| Phase | Thời gian | BE (Django API) | FE (Web React) | MOBILE (Flutter) | AI (YOLOv10, song song) |
|---|---|---|---|---|---|
| **0. Khởi tạo** | 15–17/10 | git init + push repo, `.gitignore`, Docker dev (django+postgis+redis), Django project, settings, Swagger, User model | Khởi tạo Vite + React + TS, router, 2 layout, axios client | Chuyển code vào `MOBILE/`, đổi tên/package, build chạy được | Chốt danh sách lớp, gom dataset |
| **1. Lõi dữ liệu** | 18–24/10 | accounts (JWT, Google, quên MK), vocab 3 ngôn ngữ (zh-Hans + zh-Hant), my-words, **pipeline dữ liệu ngôn ngữ + bộ kiểm tra + golden test (mục 3b)**, seed | Đăng nhập/đăng ký; Admin: user, chủ đề, từ vựng (import CSV); học viên: chủ đề, từ, flashcard | api_client + auth + vocab/topic/flashcard qua API, cache Hive | Gán nhãn, chia tập |
| **2. Học tập & kiểm tra** | 25–31/10 | learning session + ReviewLog + SRS tạm, quizzes/exams/chấm bài, gamification (XP, streak, badge, quest, league, shop), notifications | Học viên: phiên học, ôn tập, quiz, đề thi, kết quả, streak/XP/quest/shop, hồ sơ; Admin: câu hỏi, đề thi, chấm tự luận | learning session, review, quiz/exam, streak, shop, quest, profile | Train v1, đánh giá, export ONNX/TFLite |
| **3. Cộng đồng, realtime, GIS** | 01–07/11 | community, chat Channels (nhóm + hỗ trợ), WS notifications, GIS POI + nearby, API thống kê, `/detect` | Học viên: cộng đồng, chat, bản đồ POI, upload ảnh nhận diện, bảng xếp hạng; Admin: POI trên bản đồ, kiểm duyệt, thông báo, chat hỗ trợ, dashboard thống kê, log nhận diện | community, group chat WS, chat hỗ trợ, bản đồ POI + geofence, camera YOLOv10 (on-device + server) | Train v2 (bổ sung dữ liệu lớp yếu) |
| **4. Hoàn thiện & triển khai** | 08–12/11 | Tối ưu, test API (pytest), Docker prod + deploy VPS + HTTPS | Chế độ trẻ em, responsive, xử lý lỗi, build production | Chế độ trẻ em, offline sync, xử lý lỗi, build APK release | Chốt model, lưu confusion matrix |
| **5. Thuật toán nghiên cứu** | 13/11 → | *(lên plan riêng sau)*: SM-2 chuẩn, FSRS, VIP, Smart Distractor, Proximity Search tự cài, GA + thực nghiệm | | | |

---

## 11. Tiêu chí hoàn thành (Definition of Done) trước Phase 5

- [ ] `docker compose up` một lệnh là chạy đủ BE + web + DB + realtime; `seed_all` tạo đủ dữ liệu demo
- [ ] Web học viên (React): đủ chức năng như app – đăng ký → flashcard → ôn tập → làm đề → upload ảnh nhận diện → chat → bản đồ POI → XP/streak/shop
- [ ] Web Admin: CRUD từ vựng/chủ đề/câu hỏi/đề, chấm tự luận, quản lý user & quyền, POI trên bản đồ, kiểm duyệt, dashboard thống kê
- [ ] App: đăng nhập (email/Google) → chụp ảnh → YOLOv10 nhận diện → hiện từ vi/en/zh → lưu → ôn tập → làm quiz → XP/streak/huy hiệu → chat nhóm realtime → gợi ý từ theo vị trí
- [ ] Tiến độ học / tin nhắn / thông báo đồng bộ realtime giữa web và app
- [ ] YOLOv10 có báo cáo Precision/Recall/mAP + confusion matrix; chạy được cả on-device và server
- [ ] ReviewLog + DetectionItem ghi đầy đủ (sẵn dữ liệu cho Phase 5)
- [ ] **100% từ học viên nhìn thấy có status `verified`**; `validate_language_data` không lỗi; golden test giản/phồn/đa âm/từ vùng pass trong CI
- [ ] Người học chọn được giản thể (đại lục) hoặc phồn thể (Đài Loan); hiển thị đúng font, phiên âm (pinyin/zhuyin) và giọng đọc của từng biến thể
- [ ] Không còn Firestore/Realm, không có secret trong git; APK release cài được trên điện thoại thật
- [ ] Đã deploy lên VPS có HTTPS (hoặc demo bằng laptop)

---

## 12. Rủi ro & cách xử lý

| Rủi ro | Cách xử lý |
|---|---|
| Thời gian rất gấp (đang tuần 8/15) | Ưu tiên luồng chính (auth → vocab → học → camera → quiz); community/shop/league làm sau cùng, có thể giản lược |
| Dataset YOLO thiếu/kém | Bắt đầu ngay từ Phase 0, dùng dataset có sẵn + pretrained COCO; giảm số lớp nếu cần |
| VPS yếu không chạy nổi PyTorch | Server dùng onnxruntime CPU + model nhỏ; app ưu tiên on-device |
| Không có Mac để build iOS | Demo bằng Android; ghi rõ trong báo cáo |
| Đề cương ghi MongoDB + "website Django", làm PostgreSQL + web React | Báo GVHD: Django vẫn là toàn bộ máy chủ (REST API), React chỉ là giao diện; sửa mục 3.3, chương 2.2/2.3 trong báo cáo |
| Làm 2 giao diện (web + mobile) cho cùng chức năng → khối lượng gấp đôi | Dùng chung API; khu Admin dùng Ant Design có sẵn; ưu tiên Admin + luồng học chính, phần cộng đồng/shop trên web làm sau |
| Dạy sai mặt chữ/phiên âm tiếng Trung (giản ↔ phồn, đa âm, từ vùng) | Mục 3b: chỉ lấy từ nguồn chuẩn, đối chiếu chéo tự động, golden test trong CI, học viên chỉ thấy dữ liệu `verified`, nút Báo lỗi |
| Không có người biết tiếng Trung để duyệt | Thu hẹp bộ từ về những từ có mặt trong cả CC-CEDICT/HSK và từ điển Bộ GD/TOCFL; từ nào lệch nguồn thì để `flagged`, không hiển thị |
| Firestore service quá lớn khó thay | Thay theo từng module, giữ controller/UI, test từng màn |
