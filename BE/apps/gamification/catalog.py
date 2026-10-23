"""What can be earned and bought: sticker packs, badges and shop items.

Plain data with no Django imports: FE/scripts/make-rewards.py reads it too, to draw one picture per sticker and badge
(FE/public/rewards/..., MOBILE/assets/rewards/...). `seed_gamification` writes it to the database.
"""

REWARDS = "assets/rewards/"


def sticker_path(code: str) -> str:
    return f"{REWARDS}stickers/{code}.png"


def badge_path(code: str) -> str:
    return f"{REWARDS}badges/{code}.png"


def item_path(code: str) -> str:
    return f"{REWARDS}items/{code}.png"


# Sticker packs: bought once, every sticker in the pack can then be sent in comments, group chats and messages.
# Chinese captions use only characters written the same in Simplified and Traditional (你好, 加油).
STICKER_PACKS = [
    {"code": "pack_hello", "name": "Prismo chào hỏi", "colour": "#1899f0", "cost_scales": None, "cost_gems": 1,
     "stickers": [("hello", "Xin chào!"), ("thanks", "Cảm ơn nha!"), ("sticker_ok", "OK luôn!"),
                  ("great", "Tuyệt vời!"), ("good_night", "Ngủ ngon"), ("bye", "Tạm biệt!")]},
    {"code": "pack_feelings", "name": "Prismo cảm xúc", "colour": "#ff4b6e", "cost_scales": None, "cost_gems": 2,
     "stickers": [("sticker_love", "Yêu quá!"), ("sticker_sad", "Buồn hiu"), ("wow", "Wow!"),
                  ("huh", "Hả?"), ("sorry", "Xin lỗi mà"), ("haha", "Haha!")]},
    {"code": "pack_study", "name": "Học cùng nhau", "colour": "#ff9600", "cost_scales": None, "cost_gems": 3,
     "stickers": [("fighting", "Cố lên!"), ("study_yet", "Học bài chưa?"), ("smart", "Giỏi quá!"),
                  ("score100", "100 điểm!"), ("keep_fire", "Giữ lửa nha!"), ("review_time", "Ôn bài thôi!")]},
    {"code": "pack_world", "name": "Chào thế giới", "colour": "#10b981", "cost_scales": None, "cost_gems": 3,
     "stickers": [("en_hello", "Hello!"), ("zh_hello", "你好!"), ("zh_jiayou", "加油!"),
                  ("en_thanks", "Thank you!"), ("en_goodjob", "Good job!"), ("en_bye", "Bye bye!")]},
]
STICKER_PACK_OF = {code: p["code"] for p in STICKER_PACKS for code, _ in p["stickers"]}
STICKER_CAPTION = {code: text for p in STICKER_PACKS for code, text in p["stickers"]}
# the three single stickers sold before the packs: their owners get the pack each one now belongs to
LEGACY_STICKERS = {"sticker_ok": "pack_hello", "sticker_love": "pack_feelings", "sticker_sad": "pack_feelings"}

# Shop items other than sticker packs: (code, name, description, image, effect, cost_scales, cost_gems)
# Vảy buys what helps you keep learning (streak, XP); ngọc buys looks (stickers, Prismo's outfits).
ITEMS = [
    ("streak_freeze", "Đá băng", "Giữ chuỗi streak khi nghỉ 1 ngày", "assets/brand/icons/streak_freeze.png", "streak_freeze", 200, None),
    ("xp_boost", "Vảy tăng tốc", "Nhận đôi XP trong 15 phút", "assets/brand/icons/xp_x2.png", "xp_double_15m", 150, None),
    ("super_boost", "Bình ánh sáng", "Tăng 25% XP toàn app trong 24 giờ", "assets/brand/icons/xp_potion.png", "xp_plus25_24h", 400, None),
    ("streak_repair", "Hồi chuỗi", "Lỡ mất streak? Nối lại chuỗi cũ trong vòng 3 ngày", item_path("streak_repair"), "streak_repair", 800, None),
    ("gem_exchange", "Đổi vảy lấy ngọc", "Đổi 500 vảy lấy 1 ngọc, nhận ngay", item_path("gem_exchange"), "gem_exchange", 500, None),
]

# What each badge condition looks like: (glyph, colour) – see make-rewards.py
CONDITION_ART = {
    "words_learned": ("book", "#1cb0f6"), "words_mastered": ("cap", "#58cc02"), "streak": ("flame", "#ff9600"),
    "xp": ("star", "#f5b400"), "detections": ("camera", "#ce82ff"), "posts": ("image", "#ff86c8"),
    "cheers": ("heart", "#ff4b4b"), "friends": ("friends", "#14c9a8"), "quests": ("flag", "#e8566f"),
    "sessions": ("bolt", "#1899f0"), "perfect": ("target", "#00b38a"), "early_bird": ("sun", "#ffa31a"),
    "night_owl": ("moon", "#5b5fc7"), "league": ("trophy", "#a56eff"), "league_wins": ("trophy", "#f5b400"),
}
SOCIAL_CONDITIONS = {"posts", "cheers", "friends"}  # not offered to children


def _b(code, name, description, condition, threshold, gems, **extra):
    return {"code": code, "name": name, "description": description, "condition": condition, "threshold": threshold,
            "gems": gems, **extra}


BADGES = [
    # từ đã học
    _b("first-steps", "Bước chân đầu tiên", "Học từ đầu tiên", "words_learned", 1, 1),
    _b("words-25", "Vốn từ nảy mầm", "Học 25 từ", "words_learned", 25, 1),
    _b("word-collector-50", "Nhà sưu tầm từ", "Học 50 từ", "words_learned", 50, 2),
    _b("words-100", "Trăm từ trong túi", "Học 100 từ", "words_learned", 100, 2),
    _b("words-250", "Kho từ vựng", "Học 250 từ", "words_learned", 250, 3),
    _b("words-500", "Từ điển sống", "Học 500 từ", "words_learned", 500, 5),
    _b("words-1000", "Nghìn từ tỏa sáng", "Học 1000 từ", "words_learned", 1000, 8),
    # từ đã thuộc
    _b("mastered-10", "Nhớ như in", "Thuộc 10 từ (ôn đúng vào ngày khác)", "words_mastered", 10, 1),
    _b("mastered-50", "Trí nhớ vàng", "Thuộc 50 từ", "words_mastered", 50, 2),
    _b("word-master-100", "Bậc thầy từ vựng", "Thuộc 100 từ", "words_mastered", 100, 3),
    _b("mastered-250", "Thông thái", "Thuộc 250 từ", "words_mastered", 250, 5),
    _b("mastered-500", "Giáo sư ngôn ngữ", "Thuộc 500 từ", "words_mastered", 500, 8),
    # streak
    _b("streak-3", "Khởi động", "Học 3 ngày liên tiếp", "streak", 3, 1),
    _b("streak-7", "Một tuần kiên trì", "Học 7 ngày liên tiếp", "streak", 7, 2),
    _b("streak-14", "Hai tuần bền bỉ", "Học 14 ngày liên tiếp", "streak", 14, 3),
    _b("streak-30", "Thói quen vững vàng", "Học 30 ngày liên tiếp", "streak", 30, 5),
    _b("streak-50", "Ngọn lửa bền bỉ", "Học 50 ngày liên tiếp", "streak", 50, 5),
    _b("streak-100", "Trăm ngày rực lửa", "Học 100 ngày liên tiếp", "streak", 100, 10),
    _b("streak-365", "Một năm không nghỉ", "Học 365 ngày liên tiếp", "streak", 365, 20),
    # XP
    _b("xp-100", "Tia sáng đầu", "Đạt 100 XP", "xp", 100, 1),
    _b("xp-1000", "Ngàn điểm kinh nghiệm", "Đạt 1000 XP", "xp", 1000, 2),
    _b("xp-5000", "Ánh sáng rực rỡ", "Đạt 5000 XP", "xp", 5000, 3),
    _b("xp-10000", "Ngôi sao học tập", "Đạt 10000 XP", "xp", 10000, 5),
    _b("xp-25000", "Huyền thoại XP", "Đạt 25000 XP", "xp", 25000, 8),
    # chụp ảnh
    _b("snapper-1", "Bấm máy đầu tiên", "Nhận diện bức ảnh đầu tiên", "detections", 1, 1),
    _b("snapper-10", "Nhiếp ảnh gia nhí", "Nhận diện 10 bức ảnh", "detections", 10, 2),
    _b("snapper-50", "Thợ săn đồ vật", "Nhận diện 50 bức ảnh", "detections", 50, 3),
    _b("snapper-200", "Ống kính vàng", "Nhận diện 200 bức ảnh", "detections", 200, 5),
    # buổi học
    _b("sessions-10", "Chăm chỉ", "Hoàn thành 10 buổi học", "sessions", 10, 1),
    _b("sessions-50", "Siêng năng", "Hoàn thành 50 buổi học", "sessions", 50, 2),
    _b("sessions-200", "Không ngừng nghỉ", "Hoàn thành 200 buổi học", "sessions", 200, 5),
    _b("perfect-1", "Không sai câu nào", "Một buổi học đúng hết", "perfect", 1, 1),
    _b("perfect-10", "Hoàn hảo", "10 buổi học đúng hết", "perfect", 10, 2),
    _b("perfect-50", "Bất bại", "50 buổi học đúng hết", "perfect", 50, 5),
    # nhiệm vụ
    _b("quests-10", "Người làm nhiệm vụ", "Hoàn thành 10 nhiệm vụ ngày", "quests", 10, 1),
    _b("quests-50", "Thợ săn nhiệm vụ", "Hoàn thành 50 nhiệm vụ ngày", "quests", 50, 2),
    _b("quests-150", "Chiến binh nhiệm vụ", "Hoàn thành 150 nhiệm vụ ngày", "quests", 150, 3),
    _b("quests-500", "Đại sư nhiệm vụ", "Hoàn thành 500 nhiệm vụ ngày", "quests", 500, 8),
    # giờ học
    _b("early-bird", "Dậy sớm học bài", "Học xong một buổi trước 7 giờ sáng", "early_bird", 1, 1, no_label=True, tier=2),
    _b("night-owl", "Cú đêm chăm học", "Học xong một buổi sau 10 giờ tối", "night_owl", 1, 1, no_label=True, tier=2),
    # giải đấu (thứ hạng: 2 = Ánh Đồng … 10 = Lăng Kính Huyền Thoại)
    _b("league-2", "Lên hạng Ánh Đồng", "Thăng lên hạng Ánh Đồng", "league", 2, 1, no_label=True),
    _b("league-4", "Lên hạng Ánh Vàng", "Thăng lên hạng Ánh Vàng", "league", 4, 2, no_label=True),
    _b("league-6", "Lên hạng Ngọc Lục", "Thăng lên hạng Ngọc Lục", "league", 6, 3, no_label=True),
    _b("league-8", "Lên hạng Tử Ngọc", "Thăng lên hạng Tử Ngọc", "league", 8, 5, no_label=True),
    _b("league-10", "Lăng Kính Huyền Thoại", "Lên hạng cao nhất", "league", 10, 10, no_label=True, tier=6),
    _b("league-win-1", "Quán quân tuần", "Về nhất giải đấu tuần", "league_wins", 1, 3),
    _b("league-win-5", "Nhà vô địch", "Về nhất giải đấu 5 tuần", "league_wins", 5, 8),
    # cộng đồng (không có với tài khoản trẻ em)
    _b("sharer-1", "Bài đăng đầu tiên", "Đăng bài đầu tiên lên cộng đồng", "posts", 1, 1),
    _b("sharer-5", "Người chia sẻ", "Đăng 5 bài lên cộng đồng", "posts", 5, 2),
    _b("sharer-25", "Ngôi sao cộng đồng", "Đăng 25 bài lên cộng đồng", "posts", 25, 3),
    _b("cheers-10", "Người cổ vũ", "Thả tim hoặc bình luận 10 lần", "cheers", 10, 1),
    _b("cheers-50", "Trái tim ấm áp", "Thả tim hoặc bình luận 50 lần", "cheers", 50, 2),
    _b("cheers-200", "Linh hồn cộng đồng", "Thả tim hoặc bình luận 200 lần", "cheers", 200, 3),
    _b("friends-1", "Người bạn đầu tiên", "Kết bạn với 1 người", "friends", 1, 1),
    _b("friends-5", "Hội bạn học", "Có 5 người bạn", "friends", 5, 2),
    _b("friends-15", "Kết nối khắp nơi", "Có 15 người bạn", "friends", 15, 3),
]


# ---------------------------------------------------------------- Prismo's wardrobe
# Every learner has their own Prismo and dresses it: one piece per slot. Pieces are bought with ngọc, or earned
# (a badge unlocks them; they cannot be bought), or sold only during a festival. Each piece is one SVG layer drawn on
# Prismo's own grid (FE/scripts/make-outfits.py): public/outfits/<code>.svg on the web, assets/outfits/<code>.svg in the app.

def outfit_path(code: str) -> str:
    return f"assets/outfits/{code}.svg"


SLOTS = [("background", "Nền"), ("hat", "Mũ"), ("glasses", "Kính"), ("neck", "Đồ đeo"), ("hand", "Cầm tay")]

# Festivals: a piece tagged with one is sold only inside its window (dates are inclusive, local time).
# Halloween and Giáng sinh fall on the same days every year; Tết follows the lunar calendar (mùng 1: 6/2/2027, 26/1/2028).
EVENTS = {
    "halloween": {"name": "Halloween", "yearly": ("10-20", "11-03")},
    "noel": {"name": "Giáng sinh", "yearly": ("12-10", "12-31")},
    "tet": {"name": "Tết Nguyên đán", "dates": [("2027-01-27", "2027-02-16"), ("2028-01-16", "2028-02-05")]},
}


def _o(code, name, slot, gems=None, badge="", event=""):
    return {"code": code, "name": name, "slot": slot, "gems": gems, "badge": badge, "event": event}


OUTFITS = [
    # mũ
    _o("hat_cap", "Mũ lưỡi trai", "hat", 2),
    _o("hat_beanie", "Mũ len", "hat", 2),
    _o("hat_party", "Mũ sinh nhật", "hat", 2),
    _o("hat_non_la", "Nón lá", "hat", 3),
    _o("hat_flowers", "Vòng hoa", "hat", 3),
    _o("hat_beret", "Mũ nồi họa sĩ", "hat", 3),
    _o("hat_grad", "Mũ tốt nghiệp", "hat", badge="word-master-100"),
    _o("hat_nightcap", "Mũ ngủ", "hat", badge="night-owl"),
    _o("hat_flame", "Vương miện lửa", "hat", badge="streak-30"),
    _o("hat_crown", "Vương miện", "hat", badge="league-win-1"),
    _o("hat_witch", "Mũ phù thủy", "hat", 4, event="halloween"),
    _o("hat_santa", "Mũ Noel", "hat", 3, event="noel"),
    # kính
    _o("glasses_round", "Kính tròn", "glasses", 1),
    _o("glasses_sun", "Kính râm", "glasses", 2),
    _o("glasses_heart", "Kính trái tim", "glasses", 3),
    _o("glasses_star", "Kính ngôi sao", "glasses", 3),
    _o("glasses_pixel", "Kính pixel", "glasses", 4),
    _o("glasses_monocle", "Kính một mắt", "glasses", badge="words-500"),
    # đồ đeo
    _o("neck_bow", "Nơ đỏ", "neck", 1),
    _o("neck_tie", "Cà vạt", "neck", 2),
    _o("neck_pearls", "Chuỗi ngọc", "neck", 3),
    _o("neck_medal", "Huy chương vàng", "neck", badge="perfect-10"),
    _o("neck_bell", "Chuông Noel", "neck", 2, event="noel"),
    # cầm tay
    _o("hand_book", "Quyển sách", "hand", 1),
    _o("hand_pencil", "Bút chì", "hand", 1),
    _o("hand_balloon", "Bóng bay", "hand", 2),
    _o("hand_icecream", "Kem ốc quế", "hand", 2),
    _o("hand_flag", "Cờ LingoPrism", "hand", 3),
    _o("hand_camera", "Máy ảnh", "hand", badge="snapper-50"),
    _o("hand_trophy", "Cúp vô địch", "hand", badge="league-win-5"),
    _o("hand_pumpkin", "Đèn bí ngô", "hand", 3, event="halloween"),
    _o("hand_lixi", "Bao lì xì", "hand", 3, event="tet"),
    _o("hand_mai", "Cành mai", "hand", 3, event="tet"),
    # nền
    _o("bg_sky", "Bầu trời", "background", 2),
    _o("bg_classroom", "Lớp học", "background", 3),
    _o("bg_library", "Thư viện", "background", 3),
    _o("bg_beach", "Bãi biển", "background", 3),
    _o("bg_mountain", "Núi xanh", "background", 3),
    _o("bg_sakura", "Hoa anh đào", "background", 4),
    _o("bg_space", "Vũ trụ", "background", 5),
    _o("bg_sunrise", "Bình minh", "background", badge="early-bird"),
    _o("bg_flame", "Lửa rực", "background", badge="streak-100"),
    _o("bg_prism", "Lăng kính huyền thoại", "background", badge="league-10"),
    _o("bg_halloween", "Đêm Halloween", "background", 4, event="halloween"),
    _o("bg_snow", "Tuyết rơi", "background", 4, event="noel"),
    _o("bg_tet", "Phố Tết", "background", 4, event="tet"),
]
