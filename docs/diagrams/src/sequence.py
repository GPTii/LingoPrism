"""Sequence diagrams (Mermaid). Participants are the real components: client (React web / Flutter app), the Django
REST API (DRF view), the services / models behind it, PostgreSQL, Redis, Celery and the external services."""


def seq(title, body):
    return f"---\ntitle: {title}\n---\nsequenceDiagram\n    autonumber\n{body}\n"


DIAGRAMS = {}

DIAGRAMS["sequence/S01_dang_ky"] = seq(
    "S01 – Đăng ký và xác minh email",
    """
    actor U as Khách
    participant C as Web / App
    participant API as API Django<br/>RegisterView / VerifyEmailView
    participant DB as PostgreSQL
    participant R as Redis
    participant W as Celery worker
    participant M as Gmail SMTP
    U->>C: Nhập email, mật khẩu, tên, đồng ý điều khoản
    C->>API: POST /auth/register/
    API->>API: Kiểm tra throttle register, email trùng, độ mạnh mật khẩu
    alt Không hợp lệ
        API-->>C: 400 {errors theo từng ô}
    else Hợp lệ
        API->>DB: INSERT User (email_verified=false), UserGoal
        API->>DB: INSERT EmailVerificationCode
        API->>R: send_email_code.delay(email, code)
        API-->>C: 201 {access, refresh, user}
        R->>W: Nhận tác vụ
        W->>M: send_mail(mã 6 số)
        M-->>U: Email chứa mã
    end
    U->>C: Nhập mã
    C->>API: POST /auth/email/verify/ {code} (Bearer)
    API->>DB: Kiểm tra mã, hạn, số lần sai
    alt Mã đúng
        API->>DB: UPDATE User email_verified=true
        API-->>C: 200
    else Sai (lần 5 huỷ mã)
        API-->>C: 400 "Mã không đúng"
    end""",
)

DIAGRAMS["sequence/S02_dang_nhap"] = seq(
    "S02 – Đăng nhập bằng mật khẩu hoặc Google, mở kết nối realtime",
    """
    actor U as Học viên
    participant C as Web / App
    participant G as Google Identity
    participant API as API Django<br/>LoginView / GoogleLoginView
    participant DB as PostgreSQL
    participant WS as ASGI /ws/events/
    alt Email / mật khẩu
        U->>C: Email, mật khẩu
        C->>API: POST /auth/login/
        API->>API: Throttle theo IP (login) và theo email (auth_email)
        API->>DB: Lấy User, kiểm tra mật khẩu, status != locked
    else Google
        U->>C: Chọn tài khoản Google
        C->>G: google_sign_in / Google Identity
        G-->>C: ID token
        C->>API: POST /auth/google/ {id_token}
        API->>G: Xác thực chữ ký + audience (client ID web / Android)
        API->>DB: Tìm hoặc tạo User + AuthProvider
    end
    API->>DB: UPDATE last_login
    API-->>C: 200 {access, refresh, user}
    C->>C: Lưu token (persist store / secure storage)
    C->>WS: WebSocket ?token=access
    WS->>WS: JWTAuthMiddleware xác thực
    WS-->>C: {event: connected}
    Note over C: App: bật geofence, đăng ký FCM, đồng bộ bài học offline
    C->>API: Hết hạn access → POST /auth/refresh/
    API-->>C: access mới""",
)

DIAGRAMS["sequence/S03_quen_mat_khau"] = seq(
    "S03 – Quên và đặt lại mật khẩu",
    """
    actor U as Người dùng
    participant C as Web / App
    participant API as API Django<br/>Forgot / VerifyReset / ResetPassword
    participant DB as PostgreSQL
    participant W as Celery + SMTP
    U->>C: Nhập email
    C->>API: POST /auth/password/forgot/
    API->>DB: Tìm User
    opt Email tồn tại
        API->>DB: Lưu PasswordResetCode
        API->>W: send_reset_code.delay()
        W-->>U: Email chứa mã
    end
    API-->>C: 200 (giống nhau dù email có hay không)
    U->>C: Nhập mã
    C->>API: POST /auth/password/verify/
    API->>DB: Kiểm tra mã, đếm lần sai
    API-->>C: 200 {reset_token}
    U->>C: Mật khẩu mới
    C->>API: POST /auth/password/reset/
    API->>DB: set_password, xoá mã
    API->>DB: Thu hồi mọi refresh token (blacklist)
    API-->>C: 200 → đăng nhập lại""",
)

DIAGRAMS["sequence/S04_tu_vung"] = seq(
    "S04 – Duyệt chủ đề và lưu từ",
    """
    actor U as Học viên
    participant C as Web / App
    participant API as API Django<br/>TopicViewSet / MyWordViewSet
    participant SV as vocab.services
    participant DB as PostgreSQL
    U->>C: Mở Từ vựng
    C->>API: GET /topics/?lang=zh&script=hans
    API->>DB: Chủ đề hệ thống + chủ đề của người học
    API-->>C: Danh sách chủ đề
    U->>C: Mở một chủ đề
    C->>API: GET /topics/{id}/words/
    API->>SV: resolve_target(), words_for_target()
    SV->>DB: Chỉ bản dịch verified (hoặc từ tự tạo), lọc audience trẻ em
    API-->>C: Thẻ từ: chữ, pinyin/IPA/zhuyin, nghĩa Việt, ảnh, câu ví dụ
    C->>C: TTS theo tts_locale (zh-CN / zh-TW / en-US / vi-VN)
    U->>C: Lưu từ
    C->>API: POST /my-words/ {word, source: topic}
    API->>SV: Kiểm tra từ có bản dịch hiển thị cho ngôn ngữ đang học
    API->>DB: get_or_create PersonalWord (status=new)
    API-->>C: 201 (mới) / 200 (đã có)""",
)

DIAGRAMS["sequence/S05_phien_hoc"] = seq(
    "S05 – Phiên học / ôn tập (SM-2 hoặc FSRS, VIP, Smart Distractor)",
    """
    actor U as Học viên
    participant C as Web / App
    participant API as API Django<br/>StudySessionViewSet
    participant ALG as algorithms<br/>VIP · Scheduler · Distractor
    participant DB as PostgreSQL
    participant GM as gamification<br/>(signal session_finished)
    participant WS as Redis → /ws/events/
    U->>C: Ôn tập
    C->>API: POST /sessions/ {kind: review}
    API->>DB: PersonalWord due_at ≤ now
    API->>DB: AlgorithmConfig (scheduler, review_priority, distractor)
    alt review_priority = vip
        API->>ALG: vip.rank(due, weights)
        ALG->>DB: Hồ sơ nhầm lẫn thị giác của lớp YOLO
        ALG-->>API: Từ theo điểm VIP
    end
    API->>DB: INSERT StudySession(scheduler), SessionItem
    loop Mỗi từ
        API->>ALG: build_questions(word, provider)
        ALG-->>API: Câu hỏi + 3 đáp án nhiễu (Word2Vec, lọc, xếp hạng)
    end
    API-->>C: 201 {items, questions}
    loop Mỗi câu trả lời
        U->>C: Chọn đáp án
        C->>API: POST /sessions/{id}/answer/ {correct, first_try, response_ms}
        API->>ALG: scheduler.review(state, đúng?, rating, elapsed)
        ALG-->>API: Trạng thái mới + due_at
        API->>DB: UPDATE PersonalWord, INSERT ReviewLog
        API-->>C: {status, stage, due_at}
    end
    C->>API: POST /sessions/{id}/finish/
    API->>DB: ended_at, xp_earned
    API->>GM: session_finished
    GM->>DB: XP (hệ số, trần ngày), chuỗi ngày, nhiệm vụ, vảy, huy hiệu, giải tuần
    GM->>WS: push_event(xp)
    WS-->>C: {event: xp}
    API-->>C: Kết quả + từ cần luyện + level_up""",
)

DIAGRAMS["sequence/S06_luyen_cau"] = seq(
    "S06 – Luyện câu",
    """
    actor U as Học viên
    participant C as Web / App
    participant API as API Django<br/>SentencePracticeViewSet
    participant DB as PostgreSQL
    participant GM as gamification
    U->>C: Mở Luyện câu
    C->>API: GET /sentences/lesson/
    API->>DB: ExampleSentence verified của các từ đang học (Tatoeba)
    API-->>C: Bài: sắp xếp, nghe – sắp xếp, điền từ, chọn nghĩa
    loop Mỗi bài
        U->>C: Trả lời
        C->>API: POST /sentences/check/ {example, answer}
        API->>API: Chuẩn hoá và so khớp (tiếng Trung theo chữ)
        opt Đúng
            API->>GM: award_xp(practice), mark_activity
        end
        API-->>C: {correct, expected, translation_vi, xp}
    end""",
)

DIAGRAMS["sequence/S07_phat_am"] = seq(
    "S07 – Luyện phát âm (chấm trên thiết bị)",
    """
    actor U as Học viên
    participant C as Web / App
    participant API as API Django
    participant SR as Nhận dạng giọng nói<br/>(Web Speech API / speech_to_text)
    participant TTS as TTS của thiết bị
    C->>API: GET /my-words/?page_size=50
    API-->>C: Từ trong thư viện + tts_locale
    loop Mỗi từ (tối đa 10)
        C->>TTS: Đọc mẫu (đúng locale)
        U->>C: Bấm mic, đọc
        C->>SR: listen(locale)
        SR-->>C: Các phương án nghe được
        C->>C: score(): Levenshtein theo chữ / chữ cái → 0–100, tô phần sai
        C-->>U: Điểm + phần đọc chưa đúng
    end""",
)

DIAGRAMS["sequence/S08_doc_viet"] = seq(
    "S08 – Học đọc – viết tiếng Việt",
    """
    actor U as Trẻ em
    participant C as Web / App
    participant API as API Django<br/>literacy views
    participant DB as PostgreSQL
    participant GM as gamification
    C->>API: GET /literacy/lessons/
    API->>DB: LiteracyProgress → bài cao nhất được mở
    API-->>C: Lộ trình + trạng thái khoá
    U->>C: Mở bài n
    C->>API: GET /literacy/lessons/{n}/
    API-->>C: Nội dung bài (âm, vần, bài tập) hoặc 403 nếu chưa mở
    loop Mỗi bài tập
        C->>API: POST /literacy/check/ {item, answer}
        API-->>C: Đúng / sai + đáp án
    end
    C->>API: POST /literacy/lessons/{n}/finish/ {percent}
    API->>DB: Lưu best_percent
    alt percent ≥ 60
        API->>GM: award_xp, mark_activity
        API-->>C: Mở bài n+1
    else
        API-->>C: Học lại
    end""",
)

DIAGRAMS["sequence/S09_vuot_cap"] = seq(
    "S09 – Kiểm tra vượt cấp độ",
    """
    actor U as Học viên
    participant C as Web / App
    participant API as API Django<br/>LevelTestView
    participant DB as PostgreSQL
    C->>API: GET /levels/{n}/test/
    API->>DB: 10 từ của cấp n
    API->>API: Ký token (user, cấp, đáp án) bằng django.signing
    API-->>C: 10 câu + token
    U->>C: Làm bài
    C->>API: POST /levels/{n}/test/ {token, answers}
    API->>API: Giải token, kiểm tra người + cấp
    alt ≥ 8 câu đúng
        API->>DB: Mở cấp n+1, đặt làm cấp hiện tại
        API-->>C: {passed: true}
    else
        API-->>C: {passed: false, score}
    end""",
)

DIAGRAMS["sequence/S10_bai_kiem_tra"] = seq(
    "S10 – Làm bài kiểm tra và giáo viên chấm tự luận",
    """
    actor U as Học viên
    actor T as Giáo viên
    participant C as Web / App
    participant A as Trang quản trị
    participant API as API Django<br/>Exam / Submission / AdminSubmission
    participant DB as PostgreSQL
    participant N as notifications
    C->>API: POST /exams/{id}/start/
    API->>DB: INSERT Submission (in_progress)
    API-->>C: Câu hỏi (không kèm đáp án)
    U->>C: Làm bài, nộp
    C->>API: POST /submissions/{id}/submit/ {answers}
    loop Mỗi câu
        API->>API: MCQ: so phương án · FILL: so đáp án chấp nhận · ESSAY: chờ chấm
        API->>DB: INSERT Answer(score, is_correct)
    end
    API->>DB: _recompute → graded / submitted
    opt Không có tự luận chờ chấm
        API->>DB: award_xp(exam, percent / 5)
    end
    API-->>C: Kết quả tạm
    T->>A: Mở bài chờ chấm
    A->>API: POST /admin/submissions/{id}/grade/ {grades, feedback}
    API->>DB: Cập nhật điểm từng câu (≤ điểm tối đa), tính lại
    API->>N: notify(học viên, "Bài kiểm tra đã được chấm")
    N-->>C: Realtime + đẩy
    API-->>A: 200""",
)

DIAGRAMS["sequence/S11_nhan_dien"] = seq(
    "S11 – Chụp ảnh nhận diện và xác nhận",
    """
    actor U as Học viên
    participant C as App / Web
    participant API as API Django<br/>DetectView / DetectionViewSet
    participant DET as Bộ nhận diện ONNX<br/>OIV7 + COCO INT8 + CLIP
    participant MEM as Bộ nhớ sửa lỗi<br/>(MobileNetV3 embedder)
    participant DB as PostgreSQL + media
    U->>C: Chụp ảnh
    C->>API: POST /detect/ (multipart, throttle detect)
    API->>DET: predict(image)
    DET->>DET: Hai YOLO, gộp box, CLIP kiểm tra box không chắc
    DET-->>API: boxes (label, confidence, bbox, top_k), ms
    API->>MEM: apply(user, image, boxes)
    MEM-->>API: Box được sửa theo lỗi đã báo (nếu giống)
    API->>DB: INSERT Photo, Detection, DetectionItem
    API->>DB: Nối nhãn → Word verified
    API-->>C: Vật + thẻ từ theo ngôn ngữ đang học
    U->>C: Đánh dấu đúng / sai / sửa tên / chọn từ
    C->>API: POST /detections/{id}/confirm/ {items, added}
    API->>DB: UPDATE DetectionItem (feedback, corrected_label)
    opt Có vật bị báo sai
        API->>MEM: Nhúng vùng ảnh → CorrectionMemory
    end
    API->>DB: INSERT PersonalWord (source=camera) → nhiệm vụ Lưu từ
    API-->>C: {saved, reported}
    Note over C,API: Offline: TFLite trên máy, sau đó POST /detections/log/""",
)

DIAGRAMS["sequence/S12_hoi_thoai_ai"] = seq(
    "S12 – Hội thoại AI từ ảnh",
    """
    actor U as Học viên
    participant C as Web / App
    participant API as API Django<br/>PhotoDialogueView
    participant DB as PostgreSQL
    participant AI as Gemini API<br/>(Claude dự phòng)
    C->>API: GET /ai/status/
    API-->>C: {dialogue: true}
    U->>C: Tạo hội thoại
    C->>API: POST /detections/{id}/dialogue/ (throttle ai_dialogue)
    API->>DB: Đã có PhotoDialogue cho ngôn ngữ này?
    alt Đã có
        API-->>C: Hội thoại đã lưu
    else Chưa có
        API->>DB: Các từ verified của ảnh
        API->>AI: generateContent (JSON schema, đúng bộ chữ, hợp trẻ em)
        AI-->>API: {title_vi, lines}
        API->>API: Tính pinyin (pypinyin + CC-CEDICT thanh nhẹ)
        API->>DB: INSERT PhotoDialogue
        API-->>C: Hội thoại (nhãn AI tạo)
    end""",
)

DIAGRAMS["sequence/S13_dich"] = seq(
    "S13 – Dịch văn bản / giọng nói",
    """
    actor U as Học viên
    participant C as Web / App
    participant SR as Nhận dạng giọng nói<br/>(thiết bị)
    participant API as API Django<br/>TranslateView
    participant AI as Gemini flash-lite
    participant SRC as CC-CEDICT
    participant DB as PostgreSQL
    opt Nói
        U->>C: Bấm mic
        C->>SR: listen(locale)
        SR-->>C: Văn bản
    end
    C->>API: POST /translate/ {text, source (hoặc auto), target}
    API->>API: Kiểm tra cặp ngôn ngữ, ≤ 500 ký tự, throttle 120/giờ
    API->>AI: generateContent (timeout 25 s)
    AI-->>API: {translation}
    API->>SRC: Bản dịch tiếng Trung có chữ của bộ chữ kia?
    alt Sai bộ chữ / AI lỗi
        API-->>C: 503 "Không dịch được"
    else
        API->>API: Tính pinyin
        API->>DB: Tìm từ verified trong hai câu
        API-->>C: {translation, reading, words, machine_translated}
    end
    alt Trang Dịch
        U->>C: Lưu một từ
        C->>API: POST /my-words/?lang=&script=
    else Ô chat
        C->>C: Thay chữ bằng bản dịch, hiện pinyin + Hoàn tác
    end""",
)

DIAGRAMS["sequence/S14_geofence"] = seq(
    "S14 – Học theo vị trí: bản đồ và geofence",
    """
    actor U as Học viên
    participant GPS as GPS (Geolocator)
    participant C as App
    participant API as API Django<br/>NearbyView / GeofenceCheckView
    participant IDX as GridIndex<br/>(proximity.py)
    participant DB as PostgreSQL
    participant N as notifications
    U->>C: Mở bản đồ
    C->>API: GET /pois-nearby/?lat&lng&radius
    API->>IDX: query(lat, lng, r): ô lưới → Haversine
    API-->>C: POI + chủ đề
    loop App đang mở
        GPS-->>C: Vị trí mới (đi được 25 m)
        opt Lần kiểm tra trước đã > 15 giây
            C->>API: POST /geofence/check/ {lat, lng}
            API->>IDX: POI trong 2 km
            API->>DB: Giữ POI có d ≤ radius_m
            loop Mỗi POI chứa điểm
                API->>DB: Có GeofenceEvent trong 6 giờ? INSERT GeofenceEvent
                opt Chưa báo + cho phép gợi ý vị trí + POI có chủ đề
                    API->>N: notify("Bạn đang ở gần …", route=/vocab/topics/id)
                    N-->>C: Banner realtime + FCM
                end
            end
            API-->>C: {entered}
        end
    end
    U->>C: Bấm banner
    C->>C: DeepLink → màn chủ đề""",
)

DIAGRAMS["sequence/S15_tro_choi"] = seq(
    "S15 – Trò chơi",
    """
    actor U as Học viên
    participant C as Web / App
    participant API as API Django<br/>games views
    participant DB as PostgreSQL
    participant GM as gamification
    C->>API: GET /games/map/
    API->>DB: GameNode của người học, bạn bè đang chơi
    API-->>C: Bản đồ màn, rương, bạn bè
    U->>C: Chọn màn
    C->>API: GET /games/rounds/{node}/
    API->>DB: Từ đã học → câu hỏi
    API-->>C: Các vòng + token ký số (user, màn, ngôn ngữ, đáp án)
    opt Trợ giúp
        C->>API: POST /games/rounds/{node}/help/
        API->>DB: Trừ vảy (tối đa 3 lần / loại)
    end
    C->>API: POST /games/rounds/{node}/finish/ {token, results}
    API->>API: Giải token, đối chiếu số câu
    API->>DB: Cập nhật GameNode (sao, %, lần qua)
    opt Qua lần đầu
        API->>GM: award_xp(game), màn trùm cộng ngọc
    end
    API->>GM: mark_activity, nhiệm vụ Thắng màn, thống kê huy hiệu
    API-->>C: {percent, stars, xp, gems, next / review}""",
)

DIAGRAMS["sequence/S16_nhiem_vu_cua_hang"] = seq(
    "S16 – Nhiệm vụ, cửa hàng và giải đấu tuần",
    """
    actor U as Học viên
    participant C as Web / App
    participant API as API Django<br/>Quest / Shop / Leaderboard
    participant GS as gamification.services
    participant DB as PostgreSQL
    actor A as Quản trị viên
    C->>API: GET /quests/today/
    API->>GS: ensure_quests(user)
    API-->>C: Nhiệm vụ + tiến độ
    U->>C: Nhận thưởng
    C->>API: POST /quests/{id}/claim/
    API->>GS: claim_quest → XP / vảy (một lần)
    U->>C: Mua vật phẩm
    C->>API: POST /shop/items/{id}/buy/
    API->>GS: purchase(): đủ tiền? trừ, thêm UserInventory
    U->>C: Dùng tăng tốc XP
    C->>API: POST /shop/items/{id}/use/
    API->>GS: use_item → ActiveBoost (hệ số XP có hạn)
    C->>API: GET /leaderboard/
    API->>DB: LeagueMember tuần này theo weekly_xp
    API-->>C: Bảng xếp hạng hạng của tôi
    A->>API: POST /admin/league-tiers/close-week/ (hoặc lệnh close_league_week)
    API->>GS: close_cycle: lên / xuống hạng, thưởng, thông báo""",
)

DIAGRAMS["sequence/S17_bai_viet"] = seq(
    "S17 – Cộng đồng: bài viết",
    """
    actor U as Học viên
    participant C as Web / App
    participant API as API Django<br/>PostViewSet
    participant DB as PostgreSQL + media
    participant N as notifications
    C->>API: GET /posts/ (bảng tin, ẩn bài của người đã chặn)
    API-->>C: Bài viết
    U->>C: Đăng bài + ảnh
    C->>API: POST /posts/ (throttle upload, cần email xác minh)
    API->>DB: INSERT Post
    U->>C: Thích / bình luận
    C->>API: POST /posts/{id}/like/ · /comments/
    API->>DB: Lưu
    API->>N: notify(chủ bài)
    U->>C: Lưu từ trong bài
    C->>API: POST /posts/{id}/save-words/
    API->>DB: PersonalWord (source=community)
    U->>C: Báo cáo
    C->>API: POST /posts/{id}/report/
    API->>DB: INSERT PostReport (pending)""",
)

DIAGRAMS["sequence/S18_ban_be"] = seq(
    "S18 – Kết bạn, chặn và báo cáo người dùng",
    """
    actor U as Học viên A
    actor V as Học viên B
    participant C as Web / App
    participant API as API Django<br/>CommunityUserViewSet
    participant DB as PostgreSQL
    participant N as notifications
    U->>C: Tìm theo ID 8 số
    C->>API: GET /community/users/search/?q=
    API-->>C: Người học (không có trẻ em)
    U->>C: Kết bạn
    C->>API: POST /community/users/{B}/friend/
    API->>DB: INSERT FriendRequest
    API->>N: notify(B)
    V->>C: Đồng ý
    C->>API: POST /community/users/friend-requests/{id}/accept/
    API->>DB: Tạo quan hệ bạn bè, cập nhật bộ đếm
    API->>N: notify(A)
    U->>C: Báo cáo B (kèm hội thoại, chặn luôn)
    C->>API: POST /community/users/{B}/report/ {reason, thread, block}
    API->>DB: Lấy 30 tin cuối của thread A–B làm bằng chứng
    API->>DB: INSERT UserReport (pending)
    opt block
        API->>DB: Chặn: xoá theo dõi / bạn bè, cấm nhắn
    end
    API-->>C: 201""",
)

DIAGRAMS["sequence/S19_chat_nhom"] = seq(
    "S19 – Nhóm học và chat nhóm realtime",
    """
    actor U as Học viên
    participant C as Web / App
    participant API as API Django<br/>GroupViewSet / GroupMessages
    participant WS as GroupChatConsumer<br/>/ws/groups/{id}/
    participant SV as chat.services
    participant DB as PostgreSQL
    participant R as Redis channel layer
    participant O as Thành viên khác
    U->>C: Tham gia nhóm
    C->>API: POST /groups/{id}/join/
    API->>DB: GroupMember (pending nếu cần duyệt / active)
    C->>API: GET /groups/{id}/messages/
    API-->>C: 50 tin gần nhất
    C->>WS: connect ?token
    WS->>DB: is_active_member?
    WS->>R: group_add(chat_group_id)
    U->>C: Gửi tin (đã Nói / Dịch nếu muốn)
    C->>WS: {action: send, content, client_id}
    WS->>WS: Token bucket: 8 tin liên tiếp, 1 tin / giây
    WS->>SV: send_group_message
    SV->>DB: Không phải trẻ em, email xác minh, chống trùng client_id, INSERT
    SV->>R: group_send(message)
    R-->>C: {event: message}
    R-->>O: {event: message}
    O->>API: POST /groups/{id}/messages/{mid}/heart/
    API->>SV: heart_group_message (select_for_update)
    SV->>R: group_send(heart)
    R-->>C: {event: heart, hearts}""",
)

DIAGRAMS["sequence/S20_tin_nhan_rieng"] = seq(
    "S20 – Tin nhắn riêng",
    """
    actor U as Học viên A
    participant C as Web / App của A
    participant API as API Django<br/>DirectThreadViewSet
    participant SV as chat.services
    participant DB as PostgreSQL
    participant R as Redis → /ws/events/
    participant B as Thiết bị của B
    C->>API: POST /messages/threads/ {user: B}
    API->>SV: can_message(A, B): người lớn, không chặn, bạn bè / theo dõi nhau
    API->>DB: get_or_create DirectThread
    U->>C: Gửi tin
    C->>API: POST /messages/threads/{id}/messages/ {content, client_id} (throttle message)
    API->>SV: send_direct_message
    SV->>DB: INSERT DirectMessage
    SV->>R: push_event(A, dm) · push_event(B, dm)
    R-->>B: {event: dm}
    opt B đã đọc hết tin trước đó
        SV->>DB: notify(B) → FCM
    end
    B->>API: GET messages → mark_direct_read
    API->>R: push_event(A, dm_read)
    R-->>C: Đã xem
    B->>API: POST /messages/threads/{id}/heart/ {message}
    API->>R: push_event(A và B, dm_heart)""",
)

DIAGRAMS["sequence/S21_ho_tro"] = seq(
    "S21 – Hỏi giáo viên",
    """
    actor U as Học viên
    actor T as Giáo viên
    participant C as App / Web
    participant A as Trang hỗ trợ
    participant WS as SupportChatConsumer<br/>/ws/support/{id}/
    participant SV as chat.services
    participant DB as PostgreSQL
    participant R as Redis
    participant N as notifications
    C->>WS: POST /support/conversations/ rồi connect
    U->>C: Câu hỏi
    C->>WS: {action: send}
    WS->>SV: send_support_message
    SV->>DB: INSERT SupportMessage, mở lại hội thoại
    SV->>R: group_send(message)
    opt Đã có giáo viên phụ trách
        SV->>N: notify(giáo viên)
    end
    T->>A: Mở hộp thư hỗ trợ
    A->>WS: connect, gửi trả lời
    WS->>SV: send_support_message (staff)
    SV->>DB: Gán giáo viên phụ trách nếu chưa có
    SV->>N: notify(học viên)
    R-->>C: {event: message}
    C->>WS: {action: read}
    WS->>R: {event: read}
    T->>A: Đóng
    A->>SV: POST /support/conversations/{id}/close/""",
)

DIAGRAMS["sequence/S22_thong_bao"] = seq(
    "S22 – Thông báo realtime và thông báo đẩy",
    """
    participant SRC as Một chức năng bất kỳ<br/>(chat, chấm bài, geofence…)
    participant N as notifications.services
    participant DB as PostgreSQL
    participant R as Redis → /ws/events/
    participant P as push (signal post_save)
    participant F as Firebase FCM
    participant C as Web / App
    SRC->>N: notify(user, kind, title, body, data.route)
    N->>DB: INSERT Notification
    N->>R: push_event(user, notification)
    R-->>C: Banner + số chưa đọc (bấm → DeepLink)
    DB-->>P: post_save(Notification)
    P->>DB: Thiết bị đã đăng ký của user
    P->>F: send (luồng nền, khi Firebase bật)
    F-->>C: Thông báo hệ thống khi app đóng
    C->>C: Bấm → DeepLink.open(route)
    C->>N: POST /notifications/{id}/read/""",
)

DIAGRAMS["sequence/S23_kiem_duyet_ngon_ngu"] = seq(
    "S23 – Quản trị: kiểm duyệt bản dịch và duyệt từ mới",
    """
    actor T as Giáo viên
    participant A as Trang Kiểm duyệt ngôn ngữ
    participant API as API Django<br/>AdminTranslation / AdminCandidate
    participant CHK as vocab.lang.checks
    participant SRC as Nguồn: CC-CEDICT, HSK,<br/>moedict, TOCFL, CMUdict
    participant DB as PostgreSQL
    A->>API: GET /admin/translations/?status=flagged
    API-->>A: Bản dịch + lỗi tự động
    T->>A: Sửa / kiểm tra lại
    A->>API: POST /admin/translations/{id}/recheck/
    API->>CHK: Chạy lại kiểm tra
    CHK->>SRC: Đối chiếu chữ, pinyin, bộ chữ, phát âm
    API->>DB: Lưu issues, status
    T->>A: Duyệt
    A->>API: POST /admin/translations/{id}/verify/
    API->>DB: status=verified, method=manual, verified_by
    A->>API: POST /admin/candidates/{id}/approve/
    API->>CHK: check(candidate) cho vi, en, zh-Hans, zh-Hant
    alt Không lỗi
        API->>DB: build_vocab: Word + WordTranslation, ghi CSV đã duyệt
        API-->>A: 200
    else Có lỗi
        API-->>A: 400 + lỗi
    end""",
)

DIAGRAMS["sequence/S24_webgis"] = seq(
    "S24 – Quản trị: quản lý POI (WebGIS)",
    """
    actor T as Giáo viên
    participant A as Bản đồ quản trị<br/>(React Leaflet)
    participant API as API Django<br/>PoiViewSet
    participant DB as PostgreSQL
    participant IDX as poi_index (GridIndex)
    A->>API: GET /pois/
    API-->>A: Mọi POI (kể cả đã tắt)
    T->>A: Bấm bản đồ / kéo ghim, nhập bán kính, chủ đề
    A->>A: Xem trước vòng tròn geofence
    A->>API: POST /pois/ hoặc PATCH /pois/{id}/
    API->>DB: Lưu Poi (lat, lng, radius_m, topics)
    DB-->>IDX: Tín hiệu lưu → invalidate()
    IDX->>IDX: Dựng lại chỉ mục lưới ở truy vấn sau
    API-->>A: 201 / 200""",
)

DIAGRAMS["sequence/S25_kiem_duyet_bao_cao"] = seq(
    "S25 – Quản trị: xử lý báo cáo người dùng",
    """
    actor T as Giáo viên
    participant A as Trang Kiểm duyệt
    participant API as API Django<br/>AdminUserReportViewSet
    participant DB as PostgreSQL
    participant N as notifications
    participant AU as AuditLogMiddleware
    A->>API: GET /admin/user-reports/?status=pending
    API-->>A: Báo cáo + lý do + 30 tin bằng chứng
    T->>A: Khoá tài khoản
    A->>API: POST /admin/user-reports/{id}/resolve/ {lock: true}
    alt Người bị báo là học viên
        API->>DB: User.status = locked
        API->>DB: Mọi báo cáo pending về người này → resolved
    else Giáo viên / quản trị
        API-->>A: 400
    end
    API->>N: notify(người báo cáo, "đã được xem xét")
    API-->>A: 200
    AU->>DB: INSERT AuditLog (người làm, đường dẫn, đối tượng)""",
)

DIAGRAMS["sequence/S26_thuat_toan"] = seq(
    "S26 – Quản trị: thuật toán và thực nghiệm",
    """
    actor A as Quản trị viên
    participant P as Trang Thuật toán
    participant API as API Django<br/>AlgorithmsView / RunExperimentView
    participant EX as algorithms.experiments<br/>/ benchmark / ga
    participant DB as PostgreSQL
    P->>API: GET /admin/algorithms/
    API->>DB: AlgorithmConfig + ExperimentRun mới nhất mỗi loại
    API-->>P: Cấu hình, lựa chọn, kết quả
    A->>P: Đổi lịch ôn / thứ tự ôn / đáp án nhiễu / tìm POI
    P->>API: PATCH /admin/algorithms/
    API->>DB: UPDATE AlgorithmConfig (phiên học sau dùng)
    A->>P: Chạy lại GA
    P->>API: POST /admin/algorithms/run/ga/
    API->>EX: histories → chia train / test → GA (24 cá thể × 25 thế hệ)
    EX->>EX: Đánh giá log-loss trên thẻ test
    opt Tốt hơn tham số cũ
        EX->>DB: AlgorithmConfig.fsrs_weights
    end
    EX->>DB: INSERT ExperimentRun(kind=ga)
    API-->>P: Kết quả
    Note over P,EX: Tương tự: srs, vip, distractor, proximity, geofence, realtime, yolo, benchmark""",
)

DIAGRAMS["sequence/S27_quan_ly_nhan_dien"] = seq(
    "S27 – Quản trị: phản hồi nhận diện",
    """
    actor T as Giáo viên
    participant A as Trang Nhận diện
    participant API as API Django<br/>AdminCorrectionViewSet
    participant MEM as detection.memory
    participant DB as PostgreSQL
    A->>API: GET /admin/detection-reports/summary/
    API-->>A: pending / approved / chưa xuất
    A->>API: GET /admin/detection-reports/
    API-->>A: Ảnh, nhãn model, nhãn học viên sửa
    T->>A: Duyệt
    A->>API: POST /admin/detection-reports/{id}/approve/
    API->>MEM: Áp dụng cho mọi người (không chờ 3 người báo)
    API->>DB: status=approved
    T->>A: Xuất dữ liệu train
    A->>API: GET /admin/detection-reports/export/
    API->>DB: exported_at
    API-->>A: File nhãn YOLO cho lần train sau""",
)

DIAGRAMS["sequence/S28_thong_bao_hang_loat"] = seq(
    "S28 – Quản trị: gửi thông báo hàng loạt",
    """
    actor T as Giáo viên / Quản trị
    participant A as Trang Thông báo
    participant API as API Django<br/>BroadcastView
    participant DB as PostgreSQL
    participant N as notifications.services
    participant C as Web / App người học
    T->>A: Tiêu đề, nội dung, đối tượng (vai trò, người lớn / trẻ em)
    A->>API: POST /admin/broadcast/
    API->>DB: User is_active, lọc theo đối tượng
    loop Mỗi người
        API->>N: notify(user, broadcast)
        N-->>C: Realtime + FCM
    end
    API-->>A: {sent: n}""",
)
