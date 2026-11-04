"""Activity diagrams (Mermaid flowchart): ● start, ◉ end, ◇ decision. One per server function."""

STYLE = """
    classDef se fill:#333,stroke:#333,color:#fff
    classDef dec fill:#fff8e1,stroke:#d9a400
    classDef sys fill:#eaf4fe,stroke:#1899f0
    classDef err fill:#fdecea,stroke:#e4572e"""


def act(title, body):
    return f"---\ntitle: {title}\n---\nflowchart TD\n    S((●)):::se\n    E((◉)):::se\n{body}{STYLE}\n"


DIAGRAMS = {}

DIAGRAMS["activity/A01_dang_ky"] = act("A01 – Đăng ký và xác minh email", """
    S --> A[Nhập email, mật khẩu, tên, tick đồng ý điều khoản]
    A --> B{Hợp lệ?<br/>email chưa dùng, mật khẩu đủ mạnh,<br/>đã đồng ý điều khoản}:::dec
    B -- Không --> B1[Hiện lỗi từng ô]:::err --> A
    B -- Có --> C[Tạo User email_verified = false + UserGoal]:::sys
    C --> D[Sinh mã 6 số, Celery gửi email]:::sys
    D --> F[Trả JWT access + refresh, đăng nhập luôn]:::sys
    F --> G[Khảo sát chào mừng: ngôn ngữ học, người lớn / trẻ em]
    G --> H[Nhập mã 6 số từ email]
    H --> I{Mã đúng và còn hạn?}:::dec
    I -- Sai --> I1{Sai lần thứ 5?}:::dec
    I1 -- Chưa --> H
    I1 -- Rồi --> J[Mã bị huỷ, bấm Gửi lại mã]:::err --> D
    I -- Đúng --> K[email_verified = true<br/>mở chat, đăng bài]:::sys --> E""")

DIAGRAMS["activity/A02_dang_nhap"] = act("A02 – Đăng nhập (mật khẩu hoặc Google)", """
    S --> A{Cách đăng nhập}:::dec
    A -- Email / mật khẩu --> B[Nhập email, mật khẩu]
    B --> C{Quá giới hạn thử?<br/>theo IP và theo email}:::dec
    C -- Có --> C1[429 – thử lại sau]:::err --> E
    C -- Không --> D{Đúng mật khẩu và<br/>tài khoản không bị khoá?}:::dec
    D -- Không --> D1[Ghi log đăng nhập thất bại, báo lỗi]:::err --> B
    A -- Google --> G[Google trả ID token]
    G --> H{Xác thực token với Google}:::dec
    H -- Sai --> H1[Báo lỗi]:::err --> E
    H -- Đúng --> I{Email đã có tài khoản?}:::dec
    I -- Chưa --> J[Tạo tài khoản, liên kết Google]:::sys --> K
    I -- Rồi --> K[Liên kết AuthProvider nếu chưa có]:::sys
    D -- Đúng --> K
    K --> L[Cập nhật last_login, trả JWT + hồ sơ]:::sys
    L --> M[Client lưu token, mở WebSocket /ws/events/,<br/>bật geofence + thông báo đẩy trên app]
    M --> N{Hồ sơ thiếu ảnh / ngày sinh / giới tính?}:::dec
    N -- Có --> N1[Hỏi bổ sung một lần, có Để sau] --> E
    N -- Không --> E""")

DIAGRAMS["activity/A03_quen_mat_khau"] = act("A03 – Quên và đặt lại mật khẩu", """
    S --> A[Nhập email]
    A --> B[Máy chủ luôn trả lời giống nhau<br/>dù email có tồn tại hay không]:::sys
    B --> C{Email tồn tại?}:::dec
    C -- Có --> D[Sinh mã, Celery gửi email]:::sys --> F
    C -- Không --> F[Người dùng nhập mã 6 số]
    F --> G{Mã đúng, còn hạn, chưa sai 5 lần?}:::dec
    G -- Không --> G1[Báo lỗi / mã hết hiệu lực]:::err --> F
    G -- Có --> H[Nhập mật khẩu mới]
    H --> I{Đủ mạnh?}:::dec
    I -- Không --> H
    I -- Có --> J[Lưu mật khẩu, thu hồi mọi refresh token cũ]:::sys --> K[Đăng nhập lại] --> E""")

DIAGRAMS["activity/A04_tu_vung"] = act("A04 – Duyệt chủ đề và lưu từ", """
    S --> A[Chọn ngôn ngữ đang học<br/>Anh / Trung giản thể / Trung phồn thể / Việt]
    A --> B[Lấy danh sách chủ đề hệ thống + chủ đề của mình]:::sys
    B --> C[Mở một chủ đề]
    C --> D[Lọc từ có bản dịch đã kiểm duyệt cho ngôn ngữ đó,<br/>trẻ em chỉ thấy từ dành cho trẻ]:::sys
    D --> F[Xem thẻ từ: chữ, pinyin / IPA, nghĩa Việt, ảnh, câu ví dụ]
    F --> G{Thao tác}:::dec
    G -- Nghe --> H[TTS đúng vùng: zh-CN / zh-TW / en-US / vi-VN] --> F
    G -- Báo lỗi --> I[Tạo ErrorReport cho đội nội dung]:::sys --> F
    G -- Lưu từ --> J{Từ đã có trong thư viện?}:::dec
    J -- Có --> K[Giữ nguyên] --> E
    J -- Chưa --> L[Tạo PersonalWord status = new,<br/>chờ vào phiên học]:::sys --> E
    G -- Lưu cả chủ đề --> L""")

DIAGRAMS["activity/A05_phien_hoc"] = act("A05 – Phiên học từ mới / ôn tập (SRS + VIP + Smart Distractor)", """
    S --> A{Loại phiên}:::dec
    A -- Học mới --> B[Lấy từ status new theo cấp độ / chủ đề,<br/>thiếu thì bổ sung từ lộ trình]:::sys
    A -- Ôn tập --> C[Lấy từ đến hạn due_at ≤ bây giờ]:::sys
    C --> D{Thứ tự ôn = VIP?}:::dec
    D -- Có --> D1[Xếp theo điểm VIP: quên + độ khó<br/>+ độ không chắc nhận diện + nhầm lẫn thị giác]:::sys --> F
    D -- Không --> D2[Xếp theo hạn ôn] --> F
    B --> F{Có từ nào?}:::dec
    F -- Không --> F1[Báo chưa có từ đến hạn / để học]:::err --> E
    F -- Có --> G[Tạo StudySession, ghi bộ lập lịch đang dùng<br/>SM-2 hoặc FSRS + tham số GA]:::sys
    G --> H[Sinh câu hỏi cho mỗi từ,<br/>đáp án nhiễu bằng Smart Distractor / ngẫu nhiên]:::sys
    H --> I[Học viên trả lời một câu]
    I --> J[Tính rating: đúng lần đầu = 4, đúng sau khi sai = 3, sai = 1]:::sys
    J --> K[Bộ lập lịch cập nhật trạng thái + hạn ôn mới]:::sys
    K --> L[Ghi ReviewLog: trạng thái trước / sau, thời gian trả lời]:::sys
    L --> M{Còn câu?}:::dec
    M -- Còn --> I
    M -- Hết --> N[Kết thúc phiên: XP = 5 × số câu + 5 × số đúng lần đầu]:::sys
    N --> O[Cộng XP có hệ số tăng tốc, trần XP ngày,<br/>chuỗi ngày, nhiệm vụ, vảy, huy hiệu, giải tuần]:::sys
    O --> P{Đủ % để mở cấp tiếp?}:::dec
    P -- Có --> P1[Lên cấp] --> Q
    P -- Không --> Q[Hiện kết quả + từ cần luyện thêm] --> E""")

DIAGRAMS["activity/A06_luyen_cau"] = act("A06 – Luyện câu", """
    S --> A[Yêu cầu một bài luyện câu]
    A --> B[Chọn câu ví dụ đã kiểm duyệt (Tatoeba)<br/>chứa từ học viên đang học]:::sys
    B --> C{Có câu phù hợp?}:::dec
    C -- Không --> C1[Báo cần học thêm từ] --> E
    C -- Có --> D[Tạo bài: sắp xếp câu, nghe – sắp xếp,<br/>điền từ, chọn nghĩa (nghĩa luôn bằng tiếng Việt)]:::sys
    D --> F[Học viên làm một bài]
    F --> G[Máy chủ chấm: so khớp chuẩn hoá,<br/>tiếng Trung so từng chữ]:::sys
    G --> H{Đúng?}:::dec
    H -- Có --> I[Cộng XP luyện tập, đánh dấu hoạt động]:::sys --> J
    H -- Sai --> I2[Hiện đáp án đúng + bản dịch] --> J
    J{Còn bài?}:::dec
    J -- Còn --> F
    J -- Hết --> E""")

DIAGRAMS["activity/A07_phat_am"] = act("A07 – Luyện phát âm", """
    S --> A[Lấy tối đa 10 từ trong thư viện có giọng đọc]
    A --> B{Thiết bị nhận dạng được giọng nói?}:::dec
    B -- Không --> B1[Hướng dẫn dùng Chrome / Edge / app] --> E
    B -- Có --> C[Nghe giọng mẫu (TTS đúng vùng)]
    C --> D[Bấm mic, đọc to từ]
    D --> F[Bộ nhận dạng của thiết bị trả các phương án nghe được]
    F --> G[So với từ mẫu: tiếng Trung theo chữ,<br/>ngôn ngữ khác theo chữ cái (Levenshtein)]
    G --> H[Điểm 0–100, tô đỏ phần đọc chưa đúng]
    H --> I{Đọc lại?}:::dec
    I -- Có --> D
    I -- Không --> J{Còn từ?}:::dec
    J -- Còn --> C
    J -- Hết --> K[Điểm trung bình của lượt] --> E""")

DIAGRAMS["activity/A08_doc_viet"] = act("A08 – Học đọc – viết tiếng Việt (trẻ em)", """
    S --> A[Mở lộ trình bài học đọc – viết]
    A --> B[Máy chủ tính bài cao nhất được mở<br/>(giáo viên mở được tất cả)]:::sys
    B --> C[Chọn một bài đã mở]
    C --> D{Bài được mở?}:::dec
    D -- Không --> D1[Khoá, học bài trước] --> A
    D -- Có --> F[Học âm, vần, ghép chữ, nghe đọc]
    F --> G[Làm bài tập: chọn, ghép, gõ có dấu]
    G --> H[POST /literacy/check: chấm từng câu]:::sys
    H --> I{Còn câu?}:::dec
    I -- Còn --> G
    I -- Hết --> J[POST /literacy/lessons/n/finish]:::sys
    J --> K{Đạt ≥ 60%?}:::dec
    K -- Có --> K1[Lưu tiến độ, cộng XP, mở bài tiếp theo]:::sys --> E
    K -- Không --> K2[Lưu điểm tốt nhất, học lại]:::sys --> E""")

DIAGRAMS["activity/A09_vuot_cap"] = act("A09 – Kiểm tra vượt cấp độ", """
    S --> A[Chọn cấp muốn vượt]
    A --> B[GET /levels/n/test: 10 câu + token ký số]:::sys
    B --> C[Làm 10 câu]
    C --> D[POST đáp án + token]
    D --> F{Token hợp lệ và đúng người, đúng cấp?}:::dec
    F -- Không --> F1[Báo đề hết hạn] --> E
    F -- Có --> G{Đúng ≥ 8 câu?}:::dec
    G -- Có --> H[Mở cấp tiếp theo, chuyển sang cấp đó]:::sys --> E
    G -- Không --> I[Giữ cấp hiện tại, gợi ý ôn thêm] --> E""")

DIAGRAMS["activity/A10_bai_kiem_tra"] = act("A10 – Làm bài kiểm tra và chấm tự luận", """
    S --> A[Học viên chọn đề]
    A --> B[POST /exams/id/start: tạo Submission in_progress]:::sys
    B --> C[Làm bài: trắc nghiệm, điền từ, tự luận]
    C --> D[POST /submissions/id/submit]
    D --> F{Đã nộp trước đó?}:::dec
    F -- Rồi --> F1[Báo bài đã nộp]:::err --> E
    F -- Chưa --> G[Chấm từng câu]:::sys
    G --> G1[Trắc nghiệm: so phương án đúng<br/>Điền từ: so tập đáp án chấp nhận sau chuẩn hoá<br/>Tự luận: để trống = 0 điểm, có viết = chờ chấm]:::sys
    G1 --> H{Còn câu tự luận chờ chấm?}:::dec
    H -- Không --> I[Trạng thái graded, cộng XP theo %]:::sys --> R
    H -- Có --> J[Trạng thái submitted – chờ giáo viên]:::sys
    J --> K[Giáo viên mở bài, cho điểm + nhận xét từng câu]
    K --> L{Điểm ≤ điểm tối đa?}:::dec
    L -- Không --> K
    L -- Có --> M[Tính lại tổng, trạng thái graded]:::sys
    M --> N[Thông báo cho học viên: Bài đã được chấm]:::sys --> R
    R[Học viên xem kết quả, đáp án, nhận xét] --> E""")

DIAGRAMS["activity/A11_nhan_dien"] = act("A11 – Chụp ảnh nhận diện và lưu từ", """
    S --> A[Chụp hoặc chọn ảnh]
    A --> B{Có mạng?}:::dec
    B -- Không --> C[Nhận diện bằng TFLite trên máy]
    C --> C1[Lưu tạm, gửi /detections/log khi có mạng]:::sys --> H
    B -- Có --> D{Ảnh quá dung lượng / quá tần suất?}:::dec
    D -- Có --> D1[Báo lỗi]:::err --> E
    D -- Không --> F[Máy chủ: OIV7 + COCO INT8,<br/>CLIP kiểm tra box không chắc,<br/>áp dụng bộ nhớ sửa lỗi]:::sys
    F --> G[Lưu Photo, Detection, DetectionItem<br/>(nhãn, độ tin, khung, top-k)]:::sys
    G --> H[Nối nhãn → từ đã kiểm duyệt, hiện thẻ từ theo ngôn ngữ học]
    H --> I{Mỗi vật: đúng không?}:::dec
    I -- Đúng --> J[feedback = correct]
    I -- Sai, chọn vật khác --> K[corrected_label, feedback = wrong]
    I -- Không phải vật --> L[Báo không có vật này]
    I -- Gõ tên tiếng Việt --> M[Tra từ điển đã kiểm duyệt → từ đúng]
    J & K & L & M --> N[Chọn từ muốn lưu, POST /detections/id/confirm]
    N --> O[Lưu phản hồi, tạo PersonalWord source = camera]:::sys
    O --> O2[Vật bị báo sai: nhúng vùng ảnh (MobileNetV3)<br/>vào bộ nhớ sửa lỗi – áp dụng ngay cho người báo]:::sys
    O2 --> P[Nhiệm vụ Lưu từ, hồ sơ nhầm lẫn thị giác cho VIP]:::sys
    P --> Q{Tạo hội thoại AI từ ảnh?}:::dec
    Q -- Có --> Q1[Xem A12] --> E
    Q -- Không --> E""")

DIAGRAMS["activity/A12_hoi_thoai_ai"] = act("A12 – Hội thoại AI từ ảnh", """
    S --> A[Bấm Tạo hội thoại với các từ này]
    A --> B{Máy chủ đã bật AI?}:::dec
    B -- Không --> B1[Ẩn nút] --> E
    B -- Có --> C{Ảnh đã có hội thoại cho ngôn ngữ này?}:::dec
    C -- Có --> C1[Trả hội thoại đã lưu, không gọi AI] --> K
    C -- Chưa --> D[Lấy các từ đã kiểm duyệt trong ảnh<br/>(vật được chọn, nhãn đã sửa)]:::sys
    D --> F{Có từ nào?}:::dec
    F -- Không --> F1[Báo ảnh chưa có từ kiểm duyệt]:::err --> E
    F -- Có --> G[Gọi Gemini (Claude dự phòng): 4–6 câu,<br/>dùng đủ các từ, hợp trẻ em, đúng bộ chữ]:::sys
    G --> H{AI trả JSON hợp lệ?}:::dec
    H -- Không --> H1[Báo AI đang bận / thử lại]:::err --> E
    H -- Có --> I[Máy chủ tự tính pinyin (pypinyin + CC-CEDICT)]:::sys
    I --> J[Lưu PhotoDialogue]:::sys --> K[Hiện hội thoại, nhãn AI tạo, nghe từng câu] --> E""")

DIAGRAMS["activity/A13_dich"] = act("A13 – Dịch văn bản / giọng nói (trang Dịch và trong chat)", """
    S --> A{Nhập bằng}:::dec
    A -- Gõ --> C[Văn bản ≤ 500 ký tự]
    A -- Nói --> B[Nhận dạng giọng nói trên thiết bị<br/>theo ngôn ngữ đã chọn] --> C
    C --> D{Cặp ngôn ngữ hợp lệ?<br/>khác nhau, không giản ↔ phồn}:::dec
    D -- Không --> D1[Báo lỗi]:::err --> E
    D -- Có --> F{Quá 120 lần / giờ?}:::dec
    F -- Có --> F1[429]:::err --> E
    F -- Không --> G[Gemini flash-lite dịch<br/>(nguồn auto: tự nhận ngôn ngữ)]:::sys
    G --> H{Bản dịch tiếng Trung đúng bộ chữ?<br/>(đối chiếu CC-CEDICT)}:::dec
    H -- Sai --> H1[Từ chối, báo không dịch được]:::err --> E
    H -- Đúng --> I[Tính pinyin, tìm từ đã kiểm duyệt trong câu]:::sys
    I --> J{Đang ở đâu?}:::dec
    J -- Trang Dịch --> K[Hiện bản dịch máy, nghe, chép,<br/>Lưu từ đã kiểm duyệt] --> E
    J -- Ô chat --> L[Thay chữ trong ô bằng bản dịch,<br/>hiện pinyin + Hoàn tác] --> M[Gửi tin như bình thường] --> E""")

DIAGRAMS["activity/A14_vi_tri"] = act("A14 – Học theo vị trí: bản đồ và geofence", """
    S --> A{Cách dùng}:::dec
    A -- Mở bản đồ --> B[Lấy vị trí hiện tại, chọn bán kính]
    B --> C[GET /pois-nearby: chỉ mục lưới + Haversine]:::sys
    C --> D[Hiện POI trên bản đồ] --> F[Chạm POI → chủ đề → học] --> E
    A -- Tự động (app đang mở) --> G[Nhận vị trí sau mỗi 25 m]
    G --> H{Lần kiểm tra trước đã quá 15 giây?}:::dec
    H -- Chưa --> G
    H -- Rồi --> I[POST /geofence/check]
    I --> J[Tìm POI có d ≤ bán kính POI]:::sys
    J --> K{Có POI?}:::dec
    K -- Không --> G
    K -- Có --> L[Ghi GeofenceEvent]:::sys
    L --> M{Đã báo POI này trong 6 giờ qua<br/>hoặc tắt gợi ý vị trí<br/>hoặc POI chưa gắn chủ đề?}:::dec
    M -- Có --> G
    M -- Không --> N[Tạo thông báo: Bạn đang ở gần … học ngay chủ đề …]:::sys
    N --> O[Banner trong app + thông báo đẩy]
    O --> P{Học viên bấm?}:::dec
    P -- Có --> F
    P -- Không --> G""")

DIAGRAMS["activity/A15_tro_choi"] = act("A15 – Trò chơi", """
    S --> A[Mở bản đồ trò chơi của ngôn ngữ đang học]
    A --> B[Máy chủ dựng bản đồ: các màn, màn trùm, rương,<br/>vị trí bạn bè]:::sys
    B --> C{Chọn}:::dec
    C -- Rương --> R[POST mở rương: thưởng một lần] --> A
    C -- Màn chơi --> D[GET màn: câu hỏi từ từ đã học + token ký số]:::sys
    D --> F[Chơi các vòng trên thiết bị]
    F --> G{Dùng trợ giúp?}:::dec
    G -- Có --> G1{Đủ vảy, chưa quá 3 lần / loại?}:::dec
    G1 -- Có --> G2[Trừ vảy, hiện gợi ý / làm lại câu] --> F
    G1 -- Không --> F
    G -- Không --> H[POST kết quả + token]
    H --> I{Token đúng người, đúng màn, đúng ngôn ngữ<br/>và kết quả khớp số câu?}:::dec
    I -- Không --> I1[Từ chối]:::err --> E
    I -- Có --> J[Tính % đúng, số sao]:::sys
    J --> K{Qua màn lần đầu?}:::dec
    K -- Có --> K1[Cộng XP (trùm: thêm ngọc), huy hiệu trò chơi]:::sys --> L
    K -- Không --> L[Lưu sao tốt nhất, nhiệm vụ Thắng màn]:::sys
    L --> M{Qua màn?}:::dec
    M -- Có --> M1[Gợi ý màn tiếp theo] --> E
    M -- Không --> M2[Hiện câu sai để ôn] --> E""")

DIAGRAMS["activity/A16_nhiem_vu_cua_hang"] = act("A16 – Nhiệm vụ, huy hiệu, cửa hàng và giải đấu tuần", """
    S --> A[Học, chơi, lưu từ, làm bài…]
    A --> B[Cộng tiến độ nhiệm vụ ngày / tháng, kiểm tra huy hiệu]:::sys
    B --> C{Nhiệm vụ đạt?}:::dec
    C -- Có --> D[Bấm Nhận: cộng XP / vảy, một lần]:::sys --> F
    C -- Chưa --> F{Vào cửa hàng?}:::dec
    F -- Có --> G[Chọn vật phẩm]
    G --> H{Đủ vảy / ngọc, chưa sở hữu<br/>(với đồ dùng một lần)?}:::dec
    H -- Không --> H1[Báo không đủ]:::err --> F
    H -- Có --> I[Trừ tiền, thêm vào kho]:::sys
    I --> J{Loại}:::dec
    J -- Tăng tốc XP --> J1[Dùng: bật hệ số XP có thời hạn]:::sys --> K
    J -- Đóng băng chuỗi --> J2[Tự dùng khi lỡ đúng một ngày, giữ chuỗi]:::sys --> K
    J -- Sticker / đồ Prismo --> J3[Dùng trong chat / thay đồ]:::sys --> K
    F -- Không --> K[XP vào giải đấu tuần theo hạng]
    K --> L[Cuối tuần: đóng giải, lên / xuống hạng, thưởng]:::sys --> E""")

DIAGRAMS["activity/A17_bai_viet"] = act("A17 – Cộng đồng: đăng bài, bình luận, lưu từ trong bài", """
    S --> A[Xem bảng tin]
    A --> B{Thao tác}:::dec
    B -- Đăng bài --> C{Email đã xác minh, không quá giới hạn tải lên?}:::dec
    C -- Không --> C1[Báo lỗi]:::err --> A
    C -- Có --> D[Lưu bài + ảnh, có thể kèm từ vựng]:::sys --> A
    B -- Thích / lưu bài --> F[Bật / tắt]:::sys --> A
    B -- Bình luận --> G[Lưu bình luận, thông báo chủ bài]:::sys --> A
    B -- Lưu từ trong bài --> H[Thêm các từ đã kiểm duyệt vào thư viện]:::sys --> A
    B -- Báo cáo bài --> I[Tạo PostReport cho kiểm duyệt]:::sys --> A
    B -- Thoát --> E""")

DIAGRAMS["activity/A18_ban_be_bao_cao"] = act("A18 – Bạn bè, theo dõi, chặn và báo cáo người dùng", """
    S --> A{Là tài khoản trẻ em?}:::dec
    A -- Có --> A1[Không dùng được tính năng xã hội] --> E
    A -- Không --> B[Tìm bằng tên hoặc ID 8 số / gợi ý]
    B --> C{Thao tác}:::dec
    C -- Theo dõi --> D[Theo dõi / bỏ theo dõi]:::sys --> E
    C -- Kết bạn --> F[Gửi lời mời, thông báo người kia]:::sys
    F --> G{Người kia}:::dec
    G -- Đồng ý --> G1[Thành bạn bè: nhắn tin được]:::sys --> E
    G -- Từ chối --> E
    C -- Chặn --> H[Chặn: huỷ theo dõi, bạn bè, ẩn bài, cấm nhắn]:::sys --> E
    C -- Báo cáo --> I{Đã có báo cáo đang chờ?}:::dec
    I -- Có --> I1[Báo đã gửi trước đó] --> E
    I -- Không --> J[Tạo UserReport, kèm 30 tin nhắn cuối làm bằng chứng]:::sys
    J --> K{Chặn luôn?}:::dec
    K -- Có --> H
    K -- Không --> E""")

DIAGRAMS["activity/A19_chat_nhom"] = act("A19 – Nhóm học và chat nhóm realtime", """
    S --> A[Chọn nhóm, bấm Tham gia]
    A --> B{Nhóm cần duyệt?}:::dec
    B -- Có --> C[Thành viên pending, báo trưởng nhóm]:::sys
    C --> D{Trưởng nhóm duyệt?}:::dec
    D -- Không --> E
    D -- Có --> F
    B -- Không --> F[Thành viên active, báo trưởng nhóm]:::sys
    F --> G[Mở WebSocket /ws/groups/id (JWT)]
    G --> H{Là thành viên active, không phải trẻ em,<br/>email đã xác minh?}:::dec
    H -- Không --> H1[Đóng kết nối 4403]:::err --> E
    H -- Có --> I[Soạn tin: gõ / Nói / Dịch, sticker, khoe huy hiệu]
    I --> J{Quá 8 tin liên tiếp (1 tin / giây)?}:::dec
    J -- Có --> J1[Từ chối: gửi quá nhanh]:::err --> I
    J -- Không --> K{client_id đã lưu?}:::dec
    K -- Có --> K1[Bỏ qua bản gửi lại] --> I
    K -- Không --> L[Lưu GroupMessage, phát tới cả nhóm qua Redis]:::sys
    L --> M[Mọi thành viên nhận cùng thứ tự]
    M --> N{⋯ trên một tin}:::dec
    N -- Thả tim --> N1[Bật / tắt tim, phát sự kiện heart]:::sys --> I
    N -- Dịch --> N2[Dịch sang tiếng Việt, chỉ mình thấy] --> I
    N -- Không --> E""")

DIAGRAMS["activity/A20_tin_nhan_rieng"] = act("A20 – Tin nhắn riêng", """
    S --> A[Mở hội thoại với một người]
    A --> B{Cả hai người lớn, không chặn nhau,<br/>là bạn bè hoặc theo dõi nhau?}:::dec
    B -- Không --> B1[Không nhắn được, chỉ xem lịch sử]:::err --> E
    B -- Có --> C[Tải 50 tin gần nhất, đánh dấu đã đọc]:::sys
    C --> D[Gửi tin: chữ (Nói / Dịch) hoặc sticker đã sở hữu]
    D --> F{Email đã xác minh?}:::dec
    F -- Không --> F1[Báo cần xác minh]:::err --> E
    F -- Có --> G[Lưu DirectMessage (chống trùng client_id)]:::sys
    G --> H[push_event dm tới mọi thiết bị của hai người]:::sys
    H --> I{Người nhận đã đọc hết tin trước?}:::dec
    I -- Có --> I1[Một thông báo cho cả loạt tin]:::sys --> J
    I -- Không --> J[Người nhận mở → dm_read → Đã xem]
    J --> K{⋯}:::dec
    K -- Thả tim --> K1[dm_heart tới hai người]:::sys --> D
    K -- Dịch --> K2[Bản dịch máy dưới tin] --> D
    K -- Báo cáo --> K3[Xem A18] --> E
    K -- Thoát --> E""")

DIAGRAMS["activity/A21_ho_tro"] = act("A21 – Hỏi giáo viên (chat hỗ trợ)", """
    S --> A[Học viên mở Hỏi giáo viên]
    A --> B[Tạo / mở SupportConversation]:::sys
    B --> C[Gửi câu hỏi qua /ws/support/id]
    C --> D[Lưu tin, cập nhật thời gian, mở lại nếu đã đóng]:::sys
    D --> F{Hội thoại đã có giáo viên phụ trách?}:::dec
    F -- Chưa --> G[Hiện trong hộp thư chung của giáo viên]
    F -- Rồi --> H[Thông báo giáo viên phụ trách]:::sys
    G --> I[Giáo viên trả lời: tự nhận phụ trách]:::sys
    H --> I
    I --> J[Thông báo học viên, đánh dấu đã nhận / đã đọc]:::sys
    J --> K{Xong?}:::dec
    K -- Chưa --> C
    K -- Rồi --> L[Giáo viên đóng hội thoại]:::sys --> E""")

DIAGRAMS["activity/A22_thong_bao"] = act("A22 – Thông báo", """
    S --> A[Một sự kiện: tin nhắn, chấm bài, lời mời, gần POI,<br/>mốc XP, thông báo hàng loạt…]
    A --> B[notify: tạo Notification]:::sys
    B --> C[push_event tới /ws/events của người nhận]:::sys
    B --> D{Người nhận có thiết bị đăng ký<br/>và Firebase đã bật?}:::dec
    D -- Có --> D1[Gửi FCM ở luồng nền]:::sys
    D -- Không --> F
    C --> F{App / web đang mở?}:::dec
    F -- Có --> G[Banner + tăng số chưa đọc]
    F -- Không --> H[Thông báo hệ thống trên điện thoại]
    G & H --> I{Bấm vào?}:::dec
    I -- Có --> J[DeepLink: mở màn hình theo data.route]
    I -- Không --> K[Còn trong mục Thông báo]
    J & K --> E""")

DIAGRAMS["activity/A23_kiem_duyet_ngon_ngu"] = act("A23 – Quản trị: kiểm duyệt dữ liệu ngôn ngữ và duyệt từ mới", """
    S --> A{Hàng chờ}:::dec
    A -- Bản dịch bị gắn cờ --> B[Xem lỗi do bộ kiểm tra tự động tìm<br/>(CC-CEDICT, HSK, moedict, TOCFL, CMUdict)]
    B --> C{Quyết định}:::dec
    C -- Kiểm tra lại --> C1[Chạy lại đối chiếu nguồn]:::sys --> B
    C -- Sửa --> C2[Sửa chữ, pinyin, nghĩa] --> C1
    C -- Duyệt tay --> C3[status = verified, verified_method = manual]:::sys --> E
    C -- Từ chối --> C4[status = rejected, ẩn với học viên]:::sys --> E
    A -- Từ mới HSK --> D[Sửa nghĩa Việt, chủ đề]
    D --> F[Kiểm tra nguồn cho vi, en, zh-Hans, zh-Hant]:::sys
    F --> G{Có lỗi?}:::dec
    G -- Có --> D
    G -- Không --> H{Duyệt?}:::dec
    H -- Bỏ qua --> H1[status = rejected] --> E
    H -- Duyệt --> I[Tạo Word + bản dịch đã kiểm, ghi CSV đã duyệt]:::sys --> E""")

DIAGRAMS["activity/A24_webgis"] = act("A24 – Quản trị: quản lý POI (WebGIS)", """
    S --> A[Mở bản đồ quản lý POI]
    A --> B{Thao tác}:::dec
    B -- Thêm --> C[Bấm lên bản đồ để đặt ghim]
    B -- Sửa --> D[Chọn ghim, kéo đến vị trí mới]
    C & D --> F[Nhập tên, loại, địa chỉ, bán kính geofence,<br/>gắn chủ đề, bật / tắt]
    F --> G[Xem trước vòng tròn bán kính]
    G --> H{Hợp lệ?}:::dec
    H -- Không --> F
    H -- Có --> I[Lưu POI]:::sys
    I --> J[Làm mới chỉ mục lưới Proximity]:::sys --> E
    B -- Xoá / xoá nhiều --> K[Xoá POI]:::sys --> J""")

DIAGRAMS["activity/A25_kiem_duyet_bao_cao"] = act("A25 – Quản trị: xử lý báo cáo và khoá tài khoản", """
    S --> A{Loại báo cáo}:::dec
    A -- Bài viết --> B[Xem bài và lý do]
    B --> C{Quyết định}:::dec
    C -- Ẩn bài --> C1[Đặt bài ẩn, đánh dấu đã xử lý]:::sys --> N
    C -- Bỏ qua --> C2[Đóng báo cáo]:::sys --> N
    A -- Người dùng --> D[Xem lý do + bằng chứng 30 tin nhắn]
    D --> F{Khoá tài khoản?}:::dec
    F -- Có --> G{Là học viên?}:::dec
    G -- Không --> G1[Không khoá được giáo viên / quản trị từ đây]:::err --> E
    G -- Có --> H[status = locked: không đăng nhập được,<br/>đóng mọi báo cáo đang chờ về người này]:::sys --> N
    F -- Không --> I[Bỏ qua báo cáo này]:::sys --> N
    N[Thông báo người báo cáo: đã xem xét (không nói cách xử lý)]:::sys --> O[Ghi audit log] --> E""")

DIAGRAMS["activity/A26_thuat_toan"] = act("A26 – Quản trị: thuật toán và thực nghiệm", """
    S --> A[Mở Thuật toán AI & thực nghiệm]
    A --> B[Xem cấu hình đang dùng + kết quả mới nhất]:::sys
    B --> C{Thao tác}:::dec
    C -- Đổi cấu hình --> D[Chọn lịch ôn SM-2 / FSRS, thứ tự ôn Theo hạn / VIP,<br/>đáp án nhiễu Ngẫu nhiên / Smart, tìm POI PostgreSQL / Lưới]
    D --> D1[Lưu AlgorithmConfig: áp dụng cho phiên học mới]:::sys --> B
    C -- Chạy lại thực nghiệm --> F{Loại}:::dec
    F -- srs / vip / distractor / proximity /<br/>geofence / realtime / yolo --> G[Chạy, lưu ExperimentRun]:::sys --> B
    F -- GA --> H[Tối ưu 17 tham số FSRS trên thẻ huấn luyện]:::sys
    H --> I{Log-loss trên thẻ kiểm tra tốt hơn?}:::dec
    I -- Có --> I1[Ghi tham số mới vào cấu hình]:::sys --> B
    I -- Không --> I2[Giữ tham số cũ] --> B
    F -- Benchmark --> J[Thử mọi tổ hợp, chọn theo quy tắc,<br/>kiểm tra lại trên nhóm mới]:::sys
    J --> K{Áp dụng tốt nhất?}:::dec
    K -- Có --> I1
    K -- Không --> B
    C -- Xem trước --> L[Thứ tự VIP của một học viên /<br/>đáp án nhiễu của một từ] --> B
    C -- Thoát --> E""")

DIAGRAMS["activity/A27_quan_ly_nhan_dien"] = act("A27 – Quản trị: phản hồi nhận diện và phiên bản model", """
    S --> A{Thao tác}:::dec
    A -- Phản hồi sai của học viên --> B[Xem ảnh, nhãn model, nhãn học viên sửa]
    B --> C{Quyết định}:::dec
    C -- Duyệt --> D[Bộ nhớ sửa lỗi áp dụng cho mọi người<br/>(tự động khi ≥ 3 người báo cùng lỗi)]:::sys --> F
    C -- Từ chối --> D2[Loại bỏ]:::sys --> F
    F{Xuất dữ liệu train?}:::dec
    F -- Có --> G[Xuất phản hồi đã duyệt thành dữ liệu train YOLO]:::sys --> E
    F -- Không --> E
    A -- Phiên bản model --> H[Đăng ký / bật phiên bản (tên, chỉ số mAP)]:::sys --> E
    A -- Ảnh & thống kê --> I[Xem độ tin trung bình, lớp hay sai, xoá ảnh]:::sys --> E""")

DIAGRAMS["activity/A28_quan_tri_chung"] = act("A28 – Quản trị: người dùng, đề thi, game hoá, thông báo hàng loạt, nhật ký", """
    S --> A{Chức năng}:::dec
    A -- Người dùng --> B[Tìm, tạo, sửa vai trò / trạng thái, xoá] --> L
    A -- Câu hỏi & đề --> C[Tạo câu hỏi, ghép đề, đặt điểm từng câu] --> L
    A -- Game hoá --> D[Huy hiệu, vật phẩm, hạng giải đấu, đóng tuần] --> L
    A -- Thông báo hàng loạt --> F[Nhập tiêu đề, nội dung, chọn đối tượng<br/>(vai trò, người lớn / trẻ em)]
    F --> G[notify từng người → realtime + đẩy]:::sys --> L
    A -- Bảng điều khiển --> H[Số người dùng, hoạt động, nhận diện, nội dung] --> E
    A -- Nhật ký --> I[Xem audit log, lọc theo người / thao tác] --> E
    L[Ghi audit log thao tác quản trị]:::sys --> E""")
