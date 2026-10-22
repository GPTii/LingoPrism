"""Database documentation for the report: core ERD (20 tables), data dictionary, module ERDs, table inventory.

Everything is read from the Django models, so the document always matches the code:

    cd BE && .venv/Scripts/python ../docs/database/build_db_docs.py   # README.md + erd/*.mmd
    C:/lpvenv/Scripts/python docs/database/render_erd.py              # erd/*.mmd -> erd/*.png (needs playwright)
"""
import os
import sys
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent
BE = OUT.parents[1] / "BE"
sys.path.insert(0, str(BE))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django  # noqa: E402

django.setup()

from django.apps import apps  # noqa: E402
from django.db import connection  # noqa: E402

# ------------------------------------------------------------------ what goes where

# the 20 tables the report's main ERD shows, with the attributes worth drawing (keys are always drawn)
CORE = {
    "accounts_user": ["email", "display_name", "role", "active_language", "zh_script", "learner_type"],
    "vocab_language": ["name", "tts_locale"],
    "vocab_topic": ["slug", "name_vi", "audience", "visibility"],
    "vocab_word": ["slug", "yolo_label", "part_of_speech", "levels", "difficulty"],
    "vocab_topicword": ["order"],
    "vocab_wordtranslation": ["text", "pinyin", "ipa", "status", "verified_method"],
    "vocab_examplesentence": ["text", "transliteration", "translation_vi", "source", "status"],
    "learning_personalword": ["language", "status", "stage", "fsrs_stability", "fsrs_difficulty", "due_at"],
    "learning_studysession": ["kind", "scheduler", "planned_count", "completed_count", "xp_earned"],
    "learning_reviewlog": ["question_type", "correct", "rating", "response_ms", "elapsed_days"],
    "quizzes_question": ["kind", "prompt", "options", "difficulty"],
    "quizzes_exam": ["title", "pass_percent", "is_published"],
    "quizzes_submission": ["status", "score", "max_score", "submitted_at"],
    "detection_modelversion": ["name", "classes", "map50", "is_active"],
    "detection_photo": ["image", "source"],
    "detection_detection": ["model_name", "device", "inference_ms"],
    "detection_detectionitem": ["label", "confidence", "bbox", "top_k", "feedback"],
    "gamification_xptransaction": ["source", "amount", "multiplier"],
    "gamification_badge": ["code", "name", "condition", "threshold"],
    "gamification_userbadge": ["awarded_at"],
}

# the core ERD in two readable halves (20 tables in one detailed diagram is ~3.5 times wider than high)
CORE_PARTS = {
    "a": ("Từ vựng – học tập – kiểm tra",
          ["vocab_language", "vocab_topic", "vocab_word", "vocab_topicword", "vocab_wordtranslation",
           "vocab_examplesentence", "learning_personalword", "learning_studysession", "learning_reviewlog",
           "quizzes_question", "quizzes_exam", "quizzes_submission"], ["accounts_user"]),
    "b": ("Người dùng – nhận diện ảnh – gamification",
          ["accounts_user", "detection_modelversion", "detection_photo", "detection_detection",
           "detection_detectionitem", "gamification_xptransaction", "gamification_badge", "gamification_userbadge"],
          ["vocab_word"]),
}
assert sorted(t for _, ts, _ in CORE_PARTS.values() for t in ts) == sorted(CORE)

MODULES = [  # (key, title, apps)
    ("accounts", "Người dùng", ["accounts"]),
    ("vocab", "Từ vựng đa ngôn ngữ", ["vocab"]),
    ("learning", "Học & ôn tập (SRS), luyện đọc viết", ["learning", "literacy"]),
    ("quizzes", "Câu hỏi & bài kiểm tra", ["quizzes"]),
    ("detection", "Nhận diện ảnh (YOLO)", ["detection"]),
    ("gamification", "Gamification: XP, chuỗi ngày, nhiệm vụ, giải đấu, cửa hàng", ["gamification"]),
    ("community", "Cộng đồng & nhắn tin", ["community", "chat"]),
    ("other", "Bản đồ (GIS), thông báo, cấu hình thuật toán", ["gis", "notifications", "algorithms"]),
]
FRAMEWORK_APPS = {"admin", "auth", "contenttypes", "sessions", "token_blacklist"}

# who created / reviewed a row: listed in the dictionary, left out of the diagrams (every table would point at user)
AUDIT_FK = {"created_by_id", "verified_by_id", "graded_by_id", "handled_by_id", "reviewed_by_id"}

TABLE_VI = {
    # core
    "accounts_user": "Tài khoản: học viên, giáo viên (staff), quản trị; ngôn ngữ đang học, hồ sơ, số dư vảy / ngọc.",
    "vocab_language": "Danh mục ngôn ngữ: vi, en, zh-Hans (giản thể – đại lục), zh-Hant (phồn thể – Đài Loan).",
    "vocab_topic": "Chủ đề từ vựng (động vật, đồ ăn…). Chủ đề hệ thống hoặc do học viên tự tạo.",
    "vocab_word": "Khái niệm từ vựng độc lập ngôn ngữ (VD \"cat\"), gắn với nhãn lớp YOLO để nhận diện ảnh.",
    "vocab_topicword": "Bảng nối nhiều – nhiều giữa chủ đề và từ.",
    "vocab_wordtranslation": "Cách viết của một từ trong một ngôn ngữ: phiên âm, pinyin/zhuyin, trạng thái kiểm duyệt.",
    "vocab_examplesentence": "Câu ví dụ có nguồn (Tatoeba / thủ công), đã tách từ để làm bài sắp xếp câu.",
    "learning_personalword": "Từ trong thư viện của học viên kèm trạng thái lặp lại ngắt quãng (SM-2 / FSRS).",
    "learning_studysession": "Một phiên học / ôn tập.",
    "learning_reviewlog": "Mỗi câu trả lời của học viên – dữ liệu gốc để lập lịch và đánh giá thuật toán SM-2 / FSRS.",
    "quizzes_question": "Ngân hàng câu hỏi (trắc nghiệm, điền từ…).",
    "quizzes_exam": "Đề kiểm tra do giáo viên soạn.",
    "quizzes_submission": "Bài làm của học viên cho một đề, điểm và nhận xét.",
    "detection_modelversion": "Phiên bản model nhận diện: danh sách lớp, chỉ số đánh giá, model đang dùng.",
    "detection_photo": "Ảnh học viên chụp / tải lên.",
    "detection_detection": "Một lần nhận diện ảnh (model, thiết bị, thời gian suy luận).",
    "detection_detectionitem": "Một vật nhận diện được: nhãn, độ tin cậy, khung, phương án thay thế, phản hồi đúng / sai.",
    "gamification_xptransaction": "Sổ cái điểm kinh nghiệm (XP): mỗi lần cộng điểm và lý do.",
    "gamification_badge": "Danh mục huy hiệu và điều kiện đạt.",
    "gamification_userbadge": "Huy hiệu học viên đã đạt.",
    # supporting
    "accounts_usergoal": "Mục tiêu học mỗi ngày và giờ nhắc học (1 – 1 với user).",
    "accounts_authprovider": "Tài khoản liên kết đăng nhập ngoài (Google).",
    "accounts_passwordresetcode": "Mã 6 số quên mật khẩu gửi qua email.",
    "vocab_errorreport": "Học viên báo lỗi bản dịch / câu ví dụ; giáo viên xử lý.",
    "vocab_wordcandidate": "Từ mới đề xuất từ danh sách HSK (CC-CEDICT + Wiktionary) chờ giáo viên duyệt.",
    "learning_sessionitem": "Các từ trong một phiên học và thứ tự.",
    "learning_sentenceattempt": "Câu trả lời bài tập câu (sắp xếp, nghe, điền, nghĩa).",
    "learning_learnerlevel": "Cấp độ (1–4) học viên đang học ở mỗi ngôn ngữ.",
    "literacy_literacyprogress": "Kết quả tốt nhất của trẻ ở mỗi bài học đọc – viết.",
    "literacy_literacyattempt": "Từng câu trả lời luyện đọc – viết (phân tích âm / vần / thanh hay nhầm).",
    "quizzes_examquestion": "Câu hỏi trong đề, thứ tự và điểm.",
    "quizzes_answer": "Câu trả lời từng câu trong bài làm.",
    "detection_correctionmemory": "Bộ nhớ sửa lỗi: vật bị nhận sai được ghi nhớ theo đặc trưng ảnh để lần sau tự sửa nhãn.",
    "gamification_userstats": "Bộ đếm tổng hợp (XP, chuỗi ngày, số từ…) để trang chủ / bảng xếp hạng truy vấn nhanh.",
    "gamification_dailyprogress": "Tiến độ học từng ngày (mục tiêu, số từ mới, số lượt ôn, XP).",
    "gamification_dailyquest": "Nhiệm vụ hằng ngày của học viên.",
    "gamification_monthlyquest": "Nhiệm vụ tháng (đếm số ngày hoàn thành nhiệm vụ).",
    "gamification_leaguetier": "Các hạng giải đấu tuần (10 hạng Lăng Kính).",
    "gamification_leaguecycle": "Một mùa giải tuần của một nhóm trong một hạng.",
    "gamification_leaguemember": "Học viên trong mùa giải: XP tuần, thứ hạng, lên / xuống hạng.",
    "gamification_item": "Vật phẩm trong cửa hàng (đóng băng chuỗi, nhân XP…).",
    "gamification_userinventory": "Túi đồ: vật phẩm học viên sở hữu.",
    "gamification_activeboost": "Hiệu ứng nhân XP đang có hiệu lực.",
    "community_post": "Bài đăng ảnh kèm từ vựng nhận diện được.",
    "community_postword": "Từ vựng gắn với bài đăng.",
    "community_postlike": "Lượt thích bài đăng.",
    "community_postcomment": "Bình luận (chữ / sticker).",
    "community_postreport": "Báo cáo vi phạm bài đăng.",
    "community_userfollow": "Quan hệ theo dõi giữa người dùng.",
    "community_group": "Nhóm học.",
    "community_groupmember": "Thành viên nhóm, vai trò, trạng thái duyệt.",
    "chat_groupmessage": "Tin nhắn trong nhóm học.",
    "chat_supportconversation": "Cuộc hội thoại hỗ trợ giữa học viên và nhân viên.",
    "chat_supportmessage": "Tin nhắn hỗ trợ.",
    "gis_poi": "Địa điểm (bảo tàng, chợ…) gợi ý chủ đề khi học viên đến gần; chỉ mục không gian GiST.",
    "gis_poi_topics": "Bảng nối nhiều – nhiều địa điểm – chủ đề.",
    "gis_geofenceevent": "Lần học viên đi vào vùng của một địa điểm.",
    "notifications_notification": "Thông báo trong app.",
    "notifications_notificationsetting": "Cài đặt nhận thông báo của người dùng.",
    "notifications_devicetoken": "Token thiết bị để gửi thông báo đẩy (FCM).",
    "algorithms_algorithmconfig": "Cấu hình thuật toán đang dùng (lập lịch, chọn đáp án nhiễu, trọng số) – 1 dòng.",
    "algorithms_experimentrun": "Kết quả các lần chạy thực nghiệm so sánh thuật toán.",
    # framework
    "accounts_user_groups": "Django: nhóm quyền của người dùng.",
    "accounts_user_user_permissions": "Django: quyền riêng của người dùng.",
    "auth_group": "Django: nhóm quyền.",
    "auth_group_permissions": "Django: quyền của nhóm.",
    "auth_permission": "Django: danh mục quyền.",
    "django_admin_log": "Django Admin: nhật ký thao tác.",
    "django_content_type": "Django: danh mục model (dùng cho phân quyền).",
    "django_session": "Django: phiên đăng nhập trang quản trị.",
    "django_migrations": "Django: các migration đã áp dụng (phiên bản cấu trúc DB).",
    "token_blacklist_outstandingtoken": "SimpleJWT: refresh token đã cấp.",
    "token_blacklist_blacklistedtoken": "SimpleJWT: refresh token đã thu hồi (đăng xuất).",
}

GENERIC = {
    "id": "Khóa chính", "created_at": "Thời điểm tạo", "updated_at": "Thời điểm cập nhật",
    "user_id": "Người dùng", "word_id": "Từ vựng", "topic_id": "Chủ đề", "order": "Thứ tự hiển thị",
    "language_id": "Ngôn ngữ", "language": "Mã ngôn ngữ đang học (vi, en, zh)", "status": "Trạng thái",
    "created_by_id": "Người tạo", "audience": "Đối tượng (tất cả / trẻ em / người lớn)",
}
COL_VI = {
    "accounts_user": {
        "password": "Mật khẩu đã băm (PBKDF2)", "last_login": "Lần đăng nhập cuối", "is_superuser": "Có mọi quyền",
        "email": "Email đăng nhập", "display_name": "Tên hiển thị", "avatar": "Ảnh đại diện tải lên",
        "avatar_preset": "Ảnh đại diện có sẵn trong app", "bio": "Giới thiệu ngắn", "role": "Vai trò",
        "learner_type": "Loại học viên (trẻ em / người lớn)", "learning_languages": "Các ngôn ngữ đang học, VD [\"en\", \"zh\"]",
        "active_language": "Ngôn ngữ đang học hiện tại", "zh_script": "Chữ Hán đang học: giản thể / phồn thể",
        "show_zhuyin": "Hiện chú âm (zhuyin)", "birth_date": "Ngày sinh", "gender": "Giới tính",
        "purpose": "Mục đích học", "daily_minutes": "Số phút học mỗi ngày", "onboarding_completed": "Đã qua màn hình làm quen",
        "timezone": "Múi giờ", "scales_balance": "Số dư vảy (tiền trong app)", "gems_balance": "Số dư ngọc",
        "is_staff": "Được vào trang Django Admin", "is_active": "Tài khoản còn hoạt động",
    },
    "vocab_language": {"code": "Mã ngôn ngữ (BCP 47), khóa chính", "name": "Tên tiếng Việt", "native_name": "Tên bản ngữ",
                       "tts_locale": "Giọng đọc (vi-VN, en-US, zh-CN, zh-TW)"},
    "vocab_topic": {"slug": "Mã định danh", "name_vi": "Tên tiếng Việt", "name_en": "Tên tiếng Anh",
                    "name_zh_hans": "Tên giản thể", "name_zh_hant": "Tên phồn thể", "icon": "Biểu tượng (emoji)",
                    "image": "Ảnh bìa", "owner_id": "Người tạo; trống = chủ đề hệ thống", "visibility": "Phạm vi hiển thị"},
    "vocab_word": {"slug": "Mã định danh khái niệm", "image": "Ảnh minh họa tải lên", "image_url": "Ảnh minh họa (URL)",
                   "image_credit": "Tác giả · giấy phép ảnh", "image_source": "Trang gốc của ảnh (Wikimedia Commons)",
                   "levels": "Cấp độ 1–4 theo từng ngôn ngữ, VD {\"en\": 1, \"zh\": 2}", "emoji": "Emoji minh họa cho trẻ em",
                   "yolo_label": "Nhãn lớp YOLO tương ứng (nối kết quả nhận diện với từ)", "part_of_speech": "Từ loại",
                   "difficulty": "Độ khó 1–5"},
    "vocab_topicword": {},
    "vocab_wordtranslation": {
        "text": "Từ viết trong ngôn ngữ đó", "ipa": "Phiên âm IPA (tiếng Anh – giọng Mỹ)", "pinyin": "Pinyin có dấu thanh",
        "pinyin_numbered": "Pinyin đánh số thanh, VD ma3", "zhuyin": "Chú âm phù hiệu", "measure_word": "Lượng từ (隻 / 只)",
        "accepted_variants": "Các dạng viết khác được chấp nhận khi chấm", "regional_difference": "Giản / phồn khác từ theo vùng (土豆 / 馬鈴薯)",
        "meaning_vi": "Nghĩa tiếng Việt", "meaning_en": "Nghĩa tiếng Anh", "level": "Cấp HSK / TOCFL / CEFR",
        "audio": "File phát âm", "sources": "Dữ liệu đối chiếu từ các nguồn (CC-CEDICT, MOE…)",
        "issues": "Lỗi do bộ kiểm tra tự động phát hiện", "verified_method": "Cách duyệt: tự động / thủ công",
        "verified_at": "Thời điểm duyệt", "verified_by_id": "Người duyệt"},
    "vocab_examplesentence": {
        "text": "Câu ví dụ", "transliteration": "Phiên âm của câu (pinyin)", "translation_vi": "Bản dịch tiếng Việt",
        "translation_en": "Bản dịch tiếng Anh", "source": "Nguồn (tatoeba / thủ công)", "source_id": "Mã câu ở nguồn",
        "license": "Giấy phép", "tokens": "Câu đã tách từ (kèm pinyin / zhuyin)", "target_tokens": "Vị trí các token là từ vựng đang học",
        "checks": "Lỗi / cảnh báo của bộ kiểm tra tự động"},
    "learning_personalword": {
        "status": "Trạng thái học (mới / đang học / đã thuộc…)", "source": "Từ được thêm từ đâu (chủ đề, ảnh, bài đăng…)",
        "source_ref": "Mã đối tượng nguồn (VD id ảnh nhận diện)", "stage": "Giai đoạn ghi nhớ", "ease": "Hệ số dễ (SM-2)",
        "interval_days": "Khoảng cách ôn hiện tại (ngày)", "repetitions": "Số lần nhớ đúng liên tiếp", "lapses": "Số lần quên",
        "wrong_streak": "Số lần sai liên tiếp", "fsrs_difficulty": "Độ khó D của FSRS (1–10)", "fsrs_stability": "Độ ổn định S của FSRS (ngày)",
        "due_at": "Thời điểm đến hạn ôn", "first_learned_at": "Lần học đầu tiên", "last_reviewed_at": "Lần ôn gần nhất"},
    "learning_studysession": {
        "script": "Chữ Hán của phiên (giản / phồn)", "kind": "Loại phiên (học mới / ôn tập…)", "scheduler": "Thuật toán lập lịch dùng (SM-2 / FSRS)",
        "planned_count": "Số từ dự kiến", "completed_count": "Số từ đã làm", "correct_first_try": "Số từ đúng ngay lần đầu",
        "xp_earned": "XP nhận được", "started_at": "Bắt đầu", "ended_at": "Kết thúc"},
    "learning_reviewlog": {
        "personal_word_id": "Từ của học viên được ôn", "session_id": "Phiên học", "script": "Chữ Hán (giản / phồn)",
        "question_type": "Dạng câu hỏi", "correct": "Trả lời đúng", "first_try": "Đúng ngay lần đầu", "rating": "Điểm 0–5 (chất lượng SM-2)",
        "response_ms": "Thời gian trả lời (ms)", "answer": "Câu trả lời", "scheduler": "Thuật toán lập lịch",
        "state_before": "Trạng thái nhớ trước khi trả lời", "state_after": "Trạng thái nhớ sau khi trả lời",
        "elapsed_days": "Số ngày kể từ lần ôn trước"},
    "quizzes_question": {"kind": "Dạng câu hỏi", "language_id": "Ngôn ngữ của câu hỏi", "word_id": "Từ vựng liên quan",
                         "prompt": "Đề bài", "image_url": "Ảnh minh họa", "options": "Các lựa chọn trắc nghiệm (JSON)",
                         "accepted_answers": "Đáp án đúng cho câu điền từ", "explanation": "Giải thích", "difficulty": "Độ khó"},
    "quizzes_exam": {"title": "Tên đề", "description": "Mô tả", "time_limit_minutes": "Thời gian làm bài (phút)",
                     "pass_percent": "Tỉ lệ điểm đạt (%)", "is_published": "Đã công bố"},
    "quizzes_submission": {"exam_id": "Đề kiểm tra", "started_at": "Bắt đầu làm", "submitted_at": "Nộp bài", "score": "Điểm",
                           "max_score": "Điểm tối đa", "feedback": "Nhận xét của giáo viên", "graded_by_id": "Người chấm",
                           "graded_at": "Thời điểm chấm"},
    "detection_modelversion": {"name": "Tên phiên bản", "file": "Đường dẫn file ONNX trên server", "classes": "Danh sách nhãn theo thứ tự lớp",
                               "input_size": "Kích thước ảnh đầu vào (px)", "precision": "Precision trên tập test", "recall": "Recall trên tập test",
                               "map50": "mAP@0.5", "map50_95": "mAP@0.5:0.95", "notes": "Ghi chú cách đo", "is_active": "Model đang dùng"},
    "detection_photo": {"image": "File ảnh", "width": "Chiều rộng (px)", "height": "Chiều cao (px)", "source": "Nguồn (camera / thư viện ảnh)"},
    "detection_detection": {"photo_id": "Ảnh", "model_version_id": "Phiên bản model", "model_name": "Tên model đã chạy",
                            "device": "Nơi chạy (server / điện thoại)", "inference_ms": "Thời gian suy luận (ms)",
                            "confirmed": "Học viên đã xác nhận kết quả"},
    "detection_detectionitem": {"detection_id": "Lần nhận diện", "label": "Nhãn model trả về", "confidence": "Độ tin cậy 0–1",
                                "bbox": "Khung [x1, y1, x2, y2] chuẩn hóa 0–1", "top_k": "Các nhãn thay thế và độ tin cậy",
                                "word_id": "Từ vựng ứng với nhãn", "selected": "Học viên chọn lưu từ này", "feedback": "Phản hồi đúng / sai",
                                "corrected_label": "Nhãn đúng do học viên chọn", "learned_from_id": "Đã tự sửa nhãn theo bộ nhớ sửa lỗi"},
    "gamification_xptransaction": {"source": "Nguồn XP (học, ôn, nhiệm vụ…)", "source_id": "Mã đối tượng nguồn",
                                   "base_amount": "XP gốc", "multiplier": "Hệ số nhân (boost)", "amount": "XP thực nhận (sau boost, giới hạn ngày)",
                                   "note": "Ghi chú"},
    "gamification_badge": {"code": "Mã huy hiệu", "name": "Tên", "description": "Mô tả", "icon": "Ảnh huy hiệu", "sticker": "Sticker thưởng kèm",
                           "condition": "Loại điều kiện", "threshold": "Ngưỡng cần đạt"},
    "gamification_userbadge": {"badge_id": "Huy hiệu", "awarded_at": "Thời điểm đạt"},
}

# ------------------------------------------------------------------ helpers

models_by_table = {m._meta.db_table: m for m in apps.get_models(include_auto_created=True)}


def short_type(f):
    t = (f.db_type(connection) or "").lower()
    for a, b in (("bigint", "bigint"), ("integer", "int"), ("smallint", "smallint"), ("double", "float"),
                 ("numeric", "numeric"), ("varchar", "varchar"), ("text", "text"), ("jsonb", "jsonb"),
                 ("timestamp", "timestamptz"), ("date", "date"), ("boolean", "bool"), ("uuid", "uuid")):
        if t.startswith(a):
            return b
    return t.split("(")[0].replace(" ", "_") or "?"


def full_type(f):
    t = (f.db_type(connection) or "").replace(" with time zone", "tz").replace("timestamptz", "timestamptz")
    if f.primary_key and t == "bigint":
        return "bigint identity"
    return t.replace("double precision", "double").replace("timestamp tz", "timestamptz")


def key_of(f):
    if f.primary_key:
        return "PK"
    if f.is_relation:
        return "FK"
    return "UK" if f.unique else ""


def desc(table, f):
    d = COL_VI.get(table, {}).get(f.column) or GENERIC.get(f.column)
    if not d:
        h = str(f.help_text or "")
        d = h if h else str(f.verbose_name).capitalize()
    if f.choices and len(f.choices) <= 8:
        d += ". Giá trị: " + ", ".join(str(v) for v, _ in f.choices)
    if f.is_relation:
        d += f" → {f.related_model._meta.db_table}"
    return d


def unique_sets(m):
    out = [", ".join(u) for u in m._meta.unique_together]
    for c in m._meta.constraints:
        if getattr(c, "fields", None) and c.__class__.__name__ == "UniqueConstraint":
            out.append(", ".join(c.fields))
    return out


def module_of(table):
    app = models_by_table[table]._meta.app_label
    if app in FRAMEWORK_APPS or table in ("accounts_user_groups", "accounts_user_user_permissions"):
        return None
    return next(k for k, _, a in MODULES if app in a)


def mermaid(tables, attrs_for, stubs=(), names_only=False):
    """erDiagram of `tables`; `stubs` (referenced tables of other modules) are drawn with their key only.
    names_only: boxes without columns (the one-page overview)."""
    lines = ["erDiagram"]
    drawn = list(tables) + [s for s in stubs if s not in tables]
    for t in ([] if names_only else drawn):
        m = models_by_table[t]
        lines.append(f"  {t} {{")
        for f in m._meta.fields:
            if t in stubs and t not in tables and not f.primary_key:
                continue
            if f.primary_key or (f.is_relation and f.column not in AUDIT_FK) or f.column in attrs_for(t):
                lines.append(f"    {short_type(f)} {f.column} {key_of(f)}".rstrip())
        lines.append("  }")
    for t in tables:
        m = models_by_table[t]
        for f in m._meta.fields:
            if not f.is_relation or f.column in AUDIT_FK:
                continue
            parent = f.related_model._meta.db_table
            if parent not in drawn:
                continue
            one = "||" if not f.null else "|o"
            many = "o|" if f.unique else "o{"
            lines.append(f'  {parent} {one}--{many} {t} : "{f.column}"')
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ build

def main():
    erd = OUT / "erd"
    erd.mkdir(exist_ok=True)
    all_tables = sorted(models_by_table)
    framework = [t for t in all_tables if module_of(t) is None]
    domain = [t for t in all_tables if t not in framework]
    framework.append("django_migrations")  # no model: Django's record of applied migrations
    all_tables.append("django_migrations")
    missing = [t for t in all_tables if t not in TABLE_VI]
    if missing:
        print("[cảnh báo] bảng chưa có mô tả:", missing)
    assert set(CORE) <= set(domain), set(CORE) - set(domain)

    core_attrs = lambda t: CORE.get(t, [])  # noqa: E731
    for key, (_title, tables, stubs) in CORE_PARTS.items():
        (erd / f"erd_core_{key}.mmd").write_text(mermaid(tables, core_attrs, stubs), encoding="utf-8")
    by_module = defaultdict(list)
    for t in domain:
        by_module[module_of(t)].append(t)
    for key, _title, _apps in MODULES:
        tables = by_module[key]
        stubs = sorted({f.related_model._meta.db_table for t in tables for f in models_by_table[t]._meta.fields
                        if f.is_relation and f.column not in AUDIT_FK} - set(tables))
        few = lambda t: CORE.get(t) or [f.column for f in models_by_table[t]._meta.fields  # noqa: E731
                         if not f.is_relation and f.column not in ("id", "created_at", "updated_at")][:6]
        (erd / f"erd_{key}.mmd").write_text(mermaid(tables, few, stubs), encoding="utf-8")

    md = []
    w = md.append
    w("# Cơ sở dữ liệu LingoPrism\n")
    w("> Sinh tự động từ các model Django bằng `docs/database/build_db_docs.py`. Không sửa tay: sửa model rồi chạy lại.\n")
    w("## 1. Cách tổ chức\n")
    w("Hệ quản trị: **PostgreSQL 16** (extension `cube` + `earthdistance` cho truy vấn khoảng cách). "
      "Thiết kế theo hai nguyên tắc:\n")
    w("- **Chuẩn hóa 3NF**: mỗi bảng mô tả một thực thể, quan hệ nhiều – nhiều tách thành bảng nối "
      "(`vocab_topicword`, `gamification_userbadge`…). Cột JSONB chỉ dùng cho dữ liệu không truy vấn theo từng phần tử "
      "(khung ảnh, danh sách phương án, trạng thái thuật toán).")
    w("- **Chia module theo nghiệp vụ** (bounded context – Domain-Driven Design, kiến trúc *modular monolith*): "
      "mỗi app Django sở hữu các bảng của mình, tên bảng có tiền tố module (`vocab_`, `learning_`…), module khác truy cập "
      "qua API / service của module đó.\n")
    w(f"Tổng **{len(all_tables)} bảng** = **{len(CORE)} bảng lõi** (nghiệp vụ chính, ERD mục 2) + "
      f"**{len(domain) - len(CORE)} bảng phụ trợ** (phụ lục A) + **{len(framework)} bảng của Django / thư viện** "
      f"(phụ lục B, không tự thiết kế).\n")
    w("| Module | Bảng lõi | Bảng phụ trợ | Tổng |")
    w("|---|---|---|---|")
    for key, title, _ in MODULES:
        ts = by_module[key]
        c = sum(t in CORE for t in ts)
        w(f"| {title} | {c} | {len(ts) - c} | {len(ts)} |")
    w(f"| Django / thư viện | – | – | {len(framework)} |")
    w(f"| **Tổng** | **{len(CORE)}** | **{len(domain) - len(CORE)}** | **{len(all_tables)}** |\n")

    w("## 2. ERD các bảng lõi\n")
    for i, (key, (title, _, stubs)) in enumerate(CORE_PARTS.items(), 1):
        w(f"**Hình {i} – ERD {title}** (bảng `{'`, `'.join(stubs)}` thuộc hình còn lại, chỉ vẽ khóa):\n")
        w(f"![ERD {title}](erd/erd_core_{key}.png)\n")
    w("Ký hiệu crow's foot: `||` đúng một, `|o` không hoặc một, `o{` không hoặc nhiều. Để sơ đồ dễ đọc, các khóa ngoại "
      "\"người tạo / người duyệt\" (`created_by_id`, `verified_by_id`, `graded_by_id`…) không vẽ, nhưng có trong từ điển "
      "dữ liệu. Sơ đồ chỉ vẽ khóa và các cột chính; đầy đủ ở mục 3.\n")
    w("Luồng dữ liệu chính:\n")
    w("1. **Từ vựng**: `vocab_word` là khái niệm độc lập ngôn ngữ; mỗi ngôn ngữ một dòng `vocab_wordtranslation` "
      "(giản thể và phồn thể là hai ngôn ngữ riêng); `vocab_topicword` xếp từ vào chủ đề.")
    w("2. **Nhận diện ảnh → học**: `detection_photo` → `detection_detection` → các `detection_detectionitem`; "
      "nhãn (`label`) khớp `vocab_word.yolo_label` nên học viên lưu được từ vào `learning_personalword`.")
    w("3. **Ôn tập ngắt quãng**: mỗi câu trả lời ghi một `learning_reviewlog` (trạng thái trước / sau) và cập nhật "
      "trạng thái SM-2 / FSRS trong `learning_personalword` (`due_at` = lần ôn tiếp theo).")
    w("4. **Kiểm tra**: giáo viên soạn `quizzes_exam` từ `quizzes_question`; học viên nộp `quizzes_submission`.")
    w("5. **Động lực**: mỗi hoạt động ghi `gamification_xptransaction`; đạt điều kiện thì thêm `gamification_userbadge`.\n")

    w("## 3. Từ điển dữ liệu (bảng lõi)\n")
    for i, t in enumerate(CORE, 1):
        m = models_by_table[t]
        w(f"### 3.{i}. `{t}`\n")
        w(TABLE_VI[t] + "\n")
        w("| Cột | Kiểu | Khóa | Null | Mô tả |")
        w("|---|---|---|---|---|")
        for f in m._meta.fields:
            w(f"| `{f.column}` | {full_type(f)} | {key_of(f)} | {'✓' if f.null else ''} | {desc(t, f)} |")
        u = unique_sets(m)
        if u:
            w("\nRàng buộc duy nhất: " + "; ".join(f"({x})" for x in u) + ".")
        w("")

    w("## Phụ lục A. Bảng phụ trợ theo module\n")
    for key, title, _ in MODULES:
        ts = by_module[key]
        w(f"### {title}\n")
        w(f"![ERD {title}](erd/erd_{key}.png)\n")
        w("| Bảng | Vai trò | Khóa ngoại |")
        w("|---|---|---|")
        for t in ts:
            fks = ", ".join(f"`{f.column}` → {f.related_model._meta.db_table}" for f in models_by_table[t]._meta.fields
                            if f.is_relation) or "–"
            mark = " *(lõi)*" if t in CORE else ""
            w(f"| `{t}`{mark} | {TABLE_VI.get(t, '')} | {fks} |")
        w("")

    w("## Phụ lục B. Bảng của Django và thư viện\n")
    w("Do Django (`auth`, `admin`, `sessions`, `contenttypes`) và SimpleJWT tạo, không thuộc thiết kế nghiệp vụ.\n")
    w("| Bảng | Vai trò |")
    w("|---|---|")
    for t in framework:
        w(f"| `{t}` | {TABLE_VI.get(t, '')} |")
    w("")
    w("## Tài liệu tham khảo\n")
    w("- E. Evans, *Domain-Driven Design: Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003 – bounded context.")
    w("- M. Jovanović, [Defining Module Boundaries With Bounded Contexts](https://milanjovanovic.tech/blog/module-boundaries-bounded-contexts); "
      "[Modular Monolith Data Isolation](https://milanjovanovic.tech/blog/modular-monolith-data-isolation).")
    w("- D. & A. Greenfeld, *Two Scoops of Django*, ch. 4 \"Fundamentals of Django App Design\".")
    w("- E. F. Codd, \"Further Normalization of the Data Base Relational Model\", 1971 – dạng chuẩn 3NF.")
    w("- [PostgreSQL Documentation](https://www.postgresql.org/docs/16/) – kiểu dữ liệu, JSONB, chỉ mục GiST, earthdistance.\n")
    w("## Sinh lại\n")
    w("```bash\ncd BE && .venv/Scripts/python ../docs/database/build_db_docs.py\n"
      "C:/lpvenv/Scripts/python docs/database/render_erd.py   # cần playwright + Edge / Chromium\n```")
    (OUT / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"{len(all_tables)} bảng: {len(CORE)} lõi, {len(domain) - len(CORE)} phụ trợ, {len(framework)} framework → {OUT}")


if __name__ == "__main__":
    main()
