"""Use case + architecture diagrams (Mermaid). Run build.py to write the .mmd files and render them."""

USECASE_STYLE = """
    classDef actor fill:#fff,stroke:#333,stroke-width:1.5px
    classDef uc fill:#eaf4fe,stroke:#1899f0,color:#0b3b66
    classDef ext fill:#f5f5f5,stroke:#888,stroke-dasharray:4 3"""

DIAGRAMS = {}

DIAGRAMS["usecase/UC00_tong_quat"] = (
    """---
title: UC00 – Use case tổng quát hệ thống LingoPrism
---
flowchart LR
    Guest["👤 Khách"]:::actor
    Learner["👤 Học viên"]:::actor
    Adult["👤 Học viên người lớn"]:::actor
    Kid["👤 Học viên trẻ em"]:::actor
    Staff["👤 Giáo viên / Hỗ trợ"]:::actor
    Admin["👤 Quản trị viên"]:::actor
    AI["🖥 Mô hình AI<br/>(YOLO + CLIP, Gemini)"]:::ext
    Ext["🖥 Dịch vụ ngoài<br/>(Google, Firebase, SMTP, GPS)"]:::ext

    Adult -. kế thừa .-> Learner
    Kid -. kế thừa .-> Learner
    Admin -. kế thừa .-> Staff

    subgraph SYS["Hệ thống LingoPrism"]
        U1(["Quản lý tài khoản<br/>(UC01)"]):::uc
        U2(["Học từ vựng theo chủ đề<br/>(UC02)"]):::uc
        U3(["Học & ôn tập cá nhân hoá<br/>(UC03)"]):::uc
        U4(["Làm bài kiểm tra<br/>(UC04)"]):::uc
        U5(["Chụp ảnh nhận diện, AI hội thoại, dịch<br/>(UC05)"]):::uc
        U6(["Học theo vị trí – GIS<br/>(UC06)"]):::uc
        U7(["Game hoá & trò chơi<br/>(UC07)"]):::uc
        U8(["Cộng đồng, nhắn tin, hỗ trợ<br/>(UC08)"]):::uc
        U9(["Nhận thông báo<br/>(UC09)"]):::uc
        U10(["Quản trị hệ thống<br/>(UC10)"]):::uc
    end

    Guest --- U1
    Learner --- U1 & U2 & U3 & U4 & U5 & U6 & U7 & U8 & U9
    Staff --- U4 & U8 & U10
    U5 --- AI
    U1 & U6 & U9 --- Ext
"""
    + USECASE_STYLE
)

DIAGRAMS["usecase/UC01_tai_khoan"] = (
    """---
title: UC01 – Quản lý tài khoản (apps.accounts)
---
flowchart LR
    Guest["👤 Khách"]:::actor
    Learner["👤 Học viên"]:::actor
    Google["🖥 Google Sign-In"]:::ext
    Mail["🖥 Email SMTP (Celery)"]:::ext
    subgraph SYS["Hệ thống LingoPrism"]
        R(["Đăng ký bằng email"]):::uc
        V(["Xác minh email bằng mã 6 số"]):::uc
        L(["Đăng nhập email / mật khẩu"]):::uc
        G(["Đăng nhập bằng Google"]):::uc
        F(["Quên mật khẩu (mã qua email)"]):::uc
        O(["Đăng xuất"]):::uc
        P(["Xem / sửa hồ sơ"]):::uc
        S(["Khảo sát chào mừng: ngôn ngữ, người lớn / trẻ em"]):::uc
        K(["Đặt mục tiêu & giờ nhắc học"]):::uc
        C(["Đổi mật khẩu"]):::uc
        D(["Xoá tài khoản"]):::uc
        T(["Đồng ý điều khoản"]):::uc
    end
    Guest --- R & L & G & F
    Learner --- O & P & S & K & C & D
    R -. «include» .-> T
    R -. «include» .-> V
    V --- Mail
    F --- Mail
    G --- Google
"""
    + USECASE_STYLE
)

DIAGRAMS["usecase/UC02_tu_vung"] = (
    """---
title: UC02 – Học từ vựng theo chủ đề (apps.vocab, apps.learning)
---
flowchart LR
    Learner["👤 Học viên"]:::actor
    subgraph SYS["Hệ thống LingoPrism"]
        A(["Chọn ngôn ngữ học: Anh / Trung giản thể / Trung phồn thể / Việt"]):::uc
        B(["Xem danh sách chủ đề"]):::uc
        C(["Xem thẻ từ: nghĩa, phiên âm, ảnh, câu ví dụ"]):::uc
        D(["Nghe phát âm (TTS đúng vùng)"]):::uc
        E(["Lưu từ / cả chủ đề vào Từ của tôi"]):::uc
        F(["Tạo chủ đề riêng"]):::uc
        G(["Báo lỗi dữ liệu từ vựng"]):::uc
        H(["Quản lý thư viện từ (lọc, xoá)"]):::uc
    end
    Learner --- A & B & F & G & H
    B -. «extend» .-> C
    C -. «extend» .-> D
    C -. «extend» .-> E
"""
    + USECASE_STYLE
)

DIAGRAMS["usecase/UC03_hoc_on_tap"] = (
    """---
title: UC03 – Học & ôn tập cá nhân hoá (apps.learning, apps.literacy, apps.algorithms)
---
flowchart LR
    Learner["👤 Học viên"]:::actor
    Kid["👤 Học viên trẻ em"]:::actor
    Kid -. kế thừa .-> Learner
    subgraph SYS["Hệ thống LingoPrism"]
        A(["Học từ mới (phiên học)"]):::uc
        B(["Ôn từ đến hạn"]):::uc
        S(["Lập lịch ôn: SM-2 / FSRS (+ tham số GA)"]):::uc
        V(["Ưu tiên ôn theo VIP<br/>(nhầm lẫn thị giác)"]):::uc
        Q(["Trả lời câu hỏi trắc nghiệm<br/>(Smart Distractor)"]):::uc
        C(["Luyện câu: sắp xếp, nghe, điền từ"]):::uc
        P(["Luyện phát âm (nhận dạng giọng nói)"]):::uc
        L(["Lộ trình 4 cấp độ"]):::uc
        T(["Kiểm tra vượt cấp"]):::uc
        R(["Học đọc – viết tiếng Việt"]):::uc
        X(["Xem thống kê học tập"]):::uc
    end
    Learner --- A & B & C & P & L & X
    Kid --- R
    A & B -. «include» .-> Q
    B -. «include» .-> V
    A & B -. «include» .-> S
    L -. «extend» .-> T
"""
    + USECASE_STYLE
)

DIAGRAMS["usecase/UC04_kiem_tra"] = (
    """---
title: UC04 – Bài kiểm tra (apps.quizzes)
---
flowchart LR
    Learner["👤 Học viên"]:::actor
    Staff["👤 Giáo viên / Hỗ trợ"]:::actor
    subgraph SYS["Hệ thống LingoPrism"]
        A(["Xem danh sách đề"]):::uc
        B(["Làm bài (trắc nghiệm, điền từ, tự luận)"]):::uc
        C(["Chấm tự động trắc nghiệm / điền từ"]):::uc
        D(["Xem kết quả & nhận xét"]):::uc
        E(["Quản lý ngân hàng câu hỏi"]):::uc
        F(["Tạo / sửa đề kiểm tra"]):::uc
        G(["Chấm bài tự luận"]):::uc
    end
    Learner --- A & B & D
    Staff --- E & F & G
    B -. «include» .-> C
"""
    + USECASE_STYLE
)

DIAGRAMS["usecase/UC05_nhan_dien_ai"] = (
    """---
title: UC05 – Chụp ảnh nhận diện, hội thoại AI và dịch (apps.detection, apps.aitalk)
---
flowchart LR
    Learner["👤 Học viên"]:::actor
    Det["🖥 Bộ nhận diện<br/>(YOLOv8m-OIV7 + YOLOv10m + CLIP)"]:::ext
    Phone["🖥 Model trên máy<br/>(TFLite)"]:::ext
    LLM["🖥 Gemini / Claude"]:::ext
    subgraph SYS["Hệ thống LingoPrism"]
        A(["Chụp / chọn ảnh để nhận diện"]):::uc
        B(["Nhận diện trên máy chủ"]):::uc
        C(["Nhận diện offline trên điện thoại"]):::uc
        D(["Camera trực tiếp"]):::uc
        E(["Xác nhận đúng / sai, sửa tên vật"]):::uc
        F(["Gõ tên vật bằng tiếng Việt"]):::uc
        G(["Lưu từ từ ảnh"]):::uc
        H(["Xem lịch sử ảnh"]):::uc
        I(["Tạo hội thoại AI từ ảnh"]):::uc
        J(["Dịch văn bản / giọng nói"]):::uc
        K(["Lưu từ đã kiểm duyệt từ bản dịch"]):::uc
    end
    Learner --- A & D & H & I & J
    A -. «include» .-> B
    A -. «extend» .-> C
    A -. «include» .-> E
    E -. «extend» .-> F
    E -. «extend» .-> G
    J -. «extend» .-> K
    B --- Det
    C & D --- Phone
    I & J --- LLM
"""
    + USECASE_STYLE
)

DIAGRAMS["usecase/UC06_vi_tri"] = (
    """---
title: UC06 – Học theo vị trí (GIS, Proximity Search, Geofencing) (apps.gis, apps.algorithms.proximity)
---
flowchart LR
    Learner["👤 Học viên"]:::actor
    Staff["👤 Giáo viên / Hỗ trợ"]:::actor
    GPS["🖥 GPS điện thoại"]:::ext
    subgraph SYS["Hệ thống LingoPrism"]
        A(["Xem bản đồ POI quanh mình"]):::uc
        B(["Tìm POI lân cận (chỉ mục lưới + Haversine)"]):::uc
        C(["Mở chủ đề gắn với POI"]):::uc
        D(["Nhận gợi ý khi vào vùng POI (geofence)"]):::uc
        E(["Bật / tắt gợi ý theo vị trí"]):::uc
        F(["Quản lý POI trên bản đồ (WebGIS)"]):::uc
        G(["Gắn chủ đề, bán kính cho POI"]):::uc
    end
    Learner --- A & D & E
    Staff --- F
    A -. «include» .-> B
    A -. «extend» .-> C
    D -. «include» .-> B
    F -. «include» .-> G
    D --- GPS
"""
    + USECASE_STYLE
)

DIAGRAMS["usecase/UC07_game_hoa"] = (
    """---
title: UC07 – Game hoá và trò chơi (apps.gamification, apps.games)
---
flowchart LR
    Learner["👤 Học viên"]:::actor
    subgraph SYS["Hệ thống LingoPrism"]
        A(["Nhận XP, giữ chuỗi ngày học"]):::uc
        B(["Làm nhiệm vụ ngày / tháng, nhận thưởng"]):::uc
        C(["Mở khoá huy hiệu"]):::uc
        D(["Thi đấu giải tuần, bảng xếp hạng"]):::uc
        E(["Mua vật phẩm (vảy, ngọc), dùng tăng tốc"]):::uc
        F(["Thay đồ cho Prismo"]):::uc
        G(["Chơi bản đồ trò chơi theo ngôn ngữ"]):::uc
        H(["Dùng trợ giúp trong màn chơi"]):::uc
        I(["Mở rương thưởng"]):::uc
        J(["Xem bạn bè trên bản đồ trò chơi"]):::uc
    end
    Learner --- A & B & C & D & E & F & G
    G -. «extend» .-> H
    G -. «extend» .-> I
    G -. «extend» .-> J
"""
    + USECASE_STYLE
)

DIAGRAMS["usecase/UC08_cong_dong"] = (
    """---
title: UC08 – Cộng đồng, nhắn tin và hỗ trợ (apps.community, apps.chat)
---
flowchart LR
    Adult["👤 Học viên người lớn"]:::actor
    Learner["👤 Học viên"]:::actor
    Staff["👤 Giáo viên / Hỗ trợ"]:::actor
    Adult -. kế thừa .-> Learner
    subgraph SYS["Hệ thống LingoPrism"]
        A(["Xem bảng tin, đăng bài kèm ảnh"]):::uc
        B(["Thích, bình luận, lưu bài, lưu từ trong bài"]):::uc
        C(["Tham gia / tạo nhóm học"]):::uc
        D(["Chat nhóm realtime"]):::uc
        E(["Kết bạn bằng ID 8 số, theo dõi"]):::uc
        F(["Nhắn tin riêng"]):::uc
        G(["Nói thành chữ, dịch tin trước khi gửi"]):::uc
        H(["Thả tim, dịch tin sang tiếng Việt"]):::uc
        I(["Chặn, báo cáo người dùng / bài viết"]):::uc
        J(["Hỏi giáo viên (chat hỗ trợ)"]):::uc
        K(["Trả lời học viên, đóng hội thoại"]):::uc
    end
    Learner --- A & B & J
    Adult --- C & E & F & I
    Staff --- K
    C -. «extend» .-> D
    D & F -. «extend» .-> G
    D & F -. «extend» .-> H
"""
    + USECASE_STYLE
)

DIAGRAMS["usecase/UC09_thong_bao"] = (
    """---
title: UC09 – Thông báo (apps.notifications, apps.push)
---
flowchart LR
    Learner["👤 Học viên"]:::actor
    Staff["👤 Giáo viên / Hỗ trợ"]:::actor
    FCM["🖥 Firebase Cloud Messaging"]:::ext
    subgraph SYS["Hệ thống LingoPrism"]
        A(["Nhận thông báo realtime (WebSocket)"]):::uc
        B(["Nhận thông báo đẩy khi tắt app"]):::uc
        C(["Xem, đánh dấu đã đọc, xoá thông báo"]):::uc
        D(["Mở màn hình liên quan từ thông báo"]):::uc
        E(["Cài đặt loại thông báo"]):::uc
        F(["Nhắc học theo giờ (trên máy)"]):::uc
        G(["Gửi thông báo hàng loạt"]):::uc
    end
    Learner --- A & B & C & E & F
    Staff --- G
    C -. «extend» .-> D
    B --- FCM
"""
    + USECASE_STYLE
)

DIAGRAMS["usecase/UC10_quan_tri"] = (
    """---
title: UC10 – Quản trị hệ thống
---
flowchart LR
    Staff["👤 Giáo viên / Hỗ trợ"]:::actor
    Admin["👤 Quản trị viên"]:::actor
    Admin -. kế thừa .-> Staff
    subgraph SYS["Hệ thống LingoPrism"]
        A(["Xem bảng điều khiển"]):::uc
        B(["Quản lý người dùng, phân quyền, khoá"]):::uc
        C(["Quản lý chủ đề, từ, câu ví dụ"]):::uc
        D(["Kiểm duyệt dữ liệu ngôn ngữ (đối chiếu nguồn)"]):::uc
        E(["Duyệt từ mới HSK"]):::uc
        F(["Quản lý câu hỏi, đề, chấm tự luận"]):::uc
        G(["Quản lý POI (WebGIS)"]):::uc
        H(["Xử lý báo cáo, ẩn bài, khoá tài khoản"]):::uc
        I(["Quản lý nhận diện: ảnh, phản hồi sai, phiên bản model"]):::uc
        J(["Quản lý game hoá: huy hiệu, vật phẩm, giải đấu"]):::uc
        K(["Chọn thuật toán, chạy thực nghiệm"]):::uc
        L(["Gửi thông báo hàng loạt"]):::uc
        M(["Xem nhật ký thao tác (audit log)"]):::uc
        N(["Hộp thư hỗ trợ học viên"]):::uc
    end
    Staff --- A & C & D & E & F & G & H & I & L & N
    Admin --- B & J & K & M
"""
    + USECASE_STYLE
)

# ---------------------------------------------------------------- architecture

DIAGRAMS["architecture/AR01_kien_truc_tong_the"] = """---
title: AR01 – Kiến trúc tổng thể
---
flowchart TB
    subgraph C["Client"]
        WEB["Web React + Vite<br/>(Ant Design, Leaflet)"]
        APP["App Flutter Android / iOS<br/>(GetX, TFLite, speech_to_text, flutter_tts)"]
    end
    CF["Cloudflare<br/>(DNS, HTTPS, che IP máy chủ)"]
    subgraph S["Máy chủ lingoprism.id.vn"]
        NG["nginx<br/>(file tĩnh web, reverse proxy, giới hạn tần suất)"]
        subgraph DJ["Django 5 ASGI – uvicorn"]
            REST["REST API /api/v1<br/>(DRF, JWT, Swagger)"]
            WS["WebSocket /ws<br/>(Django Channels)"]
            ALG["Thuật toán tự cài<br/>SM-2, FSRS, GA, VIP,<br/>Word2Vec, Distractor, Proximity"]
            DET["Nhận diện ONNX Runtime<br/>YOLOv8m-OIV7 + YOLOv10m (INT8) + CLIP"]
        end
        CEL["Celery worker<br/>(gửi email)"]
        PG[("PostgreSQL 16<br/>+ cube / earthdistance")]
        RD[("Redis 7<br/>channel layer, hàng đợi, cache")]
        MED[("Ảnh tải lên, model .onnx")]
    end
    subgraph X["Dịch vụ ngoài"]
        GO["Google Sign-In"]
        FCM["Firebase Cloud Messaging"]
        SMTP["Gmail SMTP"]
        GEM["Gemini API (Claude dự phòng)"]
        OSM["OpenStreetMap tiles"]
    end
    WEB & APP -->|HTTPS + WSS| CF --> NG
    NG -->|/api| REST
    NG -->|/ws| WS
    REST --- ALG & DET
    REST & WS --> PG
    WS <--> RD
    REST --> RD --> CEL --> SMTP
    DET --- MED
    REST --> GO & FCM & GEM
    FCM -.-> APP
    WEB & APP -.-> OSM
"""

DIAGRAMS["architecture/AR02_trien_khai"] = """---
title: AR02 – Sơ đồ triển khai (Azure VM B2als_v2: 2 vCPU, 4 GB, ufw 22/80/443, fail2ban; docker compose lingoprism-prod)
---
flowchart TB
    U["Trình duyệt / Điện thoại"] -->|443| CF["Cloudflare proxy"]
    subgraph VM["Azure VM – Ubuntu 24.04"]
        subgraph DC["docker compose"]
            web["web: nginx + bản build React<br/>:80 / :443 (chỉ nhận IP Cloudflare)"]
            backend["backend: uvicorn config.asgi<br/>(WEB_CONCURRENCY tiến trình), migrate khi khởi động"]
            worker["worker: celery -A config worker"]
            db[("db: postgres:16")]
            redis[("redis: redis:7-alpine")]
        end
        vol[("volumes: pgdata, media, static<br/>BE/models (.onnx, chỉ đọc), secrets (Firebase)")]
        cron["cron 03:00 VN: deploy/backup.sh<br/>(dump DB, media, .env → ~/backups)"]
    end
    PC["Máy phát triển (Windows)"]
    CF --> web -->|proxy /api /ws /admin| backend
    backend --> db & redis
    worker --> redis & db
    backend & worker --- vol
    cron --> db
    PC -->|deploy.bat: push.sh qua SSH| VM
    PC -->|pull-backups: mỗi 10 ngày| cron
    PC -->|run-experiments.bat| backend
"""

DIAGRAMS["architecture/AR03_module_backend"] = """---
title: AR03 – Các module của máy chủ (modular monolith, mỗi module một app Django)
---
flowchart LR
    accounts["accounts<br/>tài khoản, JWT, Google, email"]
    vocab["vocab<br/>ngôn ngữ, chủ đề, từ, bản dịch,<br/>kiểm duyệt nguồn"]
    learning["learning<br/>thư viện từ, phiên học, luyện câu,<br/>lộ trình cấp độ"]
    literacy["literacy<br/>học đọc – viết"]
    quizzes["quizzes<br/>câu hỏi, đề, bài làm, chấm"]
    detection["detection<br/>ảnh, nhận diện, phản hồi, model"]
    aitalk["aitalk<br/>hội thoại AI, dịch"]
    algorithms["algorithms<br/>SM-2, FSRS, GA, VIP, Word2Vec,<br/>Distractor, Proximity, thực nghiệm"]
    gis["gis<br/>POI, lân cận, geofence"]
    gamification["gamification<br/>XP, chuỗi, nhiệm vụ, huy hiệu,<br/>giải đấu, cửa hàng, Prismo"]
    games["games<br/>bản đồ trò chơi, màn, rương"]
    community["community<br/>bài viết, nhóm, bạn bè, chặn, báo cáo"]
    chat["chat<br/>chat nhóm, tin riêng, hỗ trợ"]
    notifications["notifications<br/>thông báo, sự kiện realtime"]
    push["push<br/>Firebase FCM"]
    audit["audit<br/>nhật ký quản trị"]
    core["core<br/>dashboard, health, phiên bản, quyền"]

    learning --> vocab & algorithms & gamification
    literacy --> vocab & gamification
    quizzes --> vocab & gamification
    detection --> vocab & learning
    aitalk --> detection & vocab
    algorithms --> learning & detection & gis & vocab
    gis --> vocab & notifications & algorithms
    games --> learning & gamification
    gamification --> notifications
    community --> chat & notifications & vocab
    chat --> community & notifications
    notifications --> push
    accounts --> notifications
    core --> audit
"""

DIAGRAMS["architecture/AR04_realtime"] = """---
title: AR04 – Kiến trúc realtime (Django Channels + Redis)
---
flowchart LR
    subgraph Clients
        A1["Web / App A"]
        A2["Web / App B"]
    end
    subgraph Server["ASGI"]
        E["UserEventsConsumer<br/>/ws/events/?token=JWT"]
        G["GroupChatConsumer<br/>/ws/groups/&lt;id&gt;/"]
        S["SupportChatConsumer<br/>/ws/support/&lt;id&gt;/"]
        SV["services: send_group_message,<br/>send_direct_message, notify, push_event"]
    end
    R[("Redis channel layer<br/>nhóm user_&lt;id&gt;, chat_group_&lt;id&gt;,<br/>chat_support_&lt;id&gt;")]
    DB[("PostgreSQL")]
    FCM["Firebase FCM"]
    A1 & A2 <-->|JWT trong query| E & G & S
    G & S -->|gửi tin| SV --> DB
    SV -->|group_send| R --> E & G & S
    SV -->|Notification post_save| FCM
"""

DIAGRAMS["architecture/AR05_nhan_dien"] = """---
title: AR05 – Đường ống nhận diện ảnh
---
flowchart TB
    IMG["Ảnh từ camera / thư viện"] --> MODE{"Có mạng?"}
    MODE -- Không --> TFL["TFLite trên điện thoại<br/>(on_device_detector)"] --> LOG["POST /detections/log/"]
    MODE -- Có --> UP["POST /detect/ (ảnh ≤ giới hạn MB)"]
    UP --> Y1["YOLOv8m-OIV7 INT8<br/>232 lớp"] & Y2["YOLOv10m COCO INT8"]
    Y1 & Y2 --> MERGE["Gộp box, mỗi vật giữ nhãn tự tin nhất"]
    MERGE --> CLIP{"YOLO không chắc<br/>(conf &lt; 0.6, box ≥ 10% ảnh)?"}
    CLIP -- Có --> V["CLIP MobileCLIP2 kiểm tra lại nhãn"] --> MEM
    CLIP -- Không --> MEM["Áp dụng bộ nhớ sửa lỗi<br/>(phản hồi đã duyệt)"]
    MEM --> SAVE[("Photo, Detection,<br/>DetectionItem (label, confidence, bbox, top_k)")]
    LOG --> SAVE
    SAVE --> WORDS["Nối nhãn → Word đã kiểm duyệt<br/>→ thẻ từ theo ngôn ngữ đang học"]
    WORDS --> FB["Người học xác nhận / sửa"] --> VIP["Hồ sơ nhầm lẫn thị giác → VIP"]
"""
