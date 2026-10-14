from django.core.management.base import BaseCommand

from apps.gamification.models import Badge, Item, LeagueTier

TIERS = [
    ("tan-binh", "Tân binh Igloo", "assets/images/rank/rank1.png"),
    ("igloo-dong", "Igloo Đồng", "assets/images/rank/rank3.png"),
    ("igloo-bac", "Igloo Bạc", "assets/images/rank/rank5.png"),
    ("igloo-vang", "Igloo Vàng", "assets/images/rank/rank7.png"),
    ("igloo-kim-cuong", "Igloo Kim cương", "assets/images/rank/rank10.png"),
]
ITEMS = [
    ("streak_freeze", "Đá băng", "Giữ chuỗi streak khi nghỉ 1 ngày", "assets/images/streak/streakbang.png", "streak_freeze", 200, None),
    ("xp_boost", "Vảy tăng tốc", "Nhận đôi XP trong 15 phút", "assets/images/XPx2.png", "xp_double_15m", 150, None),
    ("super_boost", "Bình cực quang", "Tăng 25% XP toàn app trong 24 giờ", "assets/images/binhcucquang.png", "xp_plus25_24h", None, 2),
    ("sticker_ok", "Sticker OK", "Dùng sticker trong chat nhóm & bình luận", "assets/images/chimcanhcut/chim_ok.png", "sticker", None, 2),
    ("sticker_love", "Sticker yêu ngất ngây", "Dùng sticker trong chat nhóm & bình luận", "assets/images/chimcanhcut/chim_yeu.png", "sticker", None, 2),
    ("sticker_sad", "Sticker buồn hiu", "Dùng sticker trong chat nhóm & bình luận", "assets/images/chimcanhcut/chim_buon.png", "sticker", None, 2),
]
BADGES = [
    ("first-steps", "Bước chân đầu tiên", "Học những từ đầu tiên", "words_learned", 1, "assets/images/chimcanhcut/chim_xinchao.png"),
    ("word-collector-50", "Nhà sưu tầm từ", "Học 50 từ", "words_learned", 50, "assets/images/chimcanhcut/chim_hocnhom1.png"),
    ("word-master-100", "Bậc thầy từ vựng", "Thuộc 100 từ", "words_mastered", 100, "assets/images/chimcanhcut/chim_totnghiep.png"),
    ("streak-3", "Khởi động", "Học 3 ngày liên tiếp", "streak", 3, "assets/images/streak/streak1.png"),
    ("streak-7", "Một tuần kiên trì", "Học 7 ngày liên tiếp", "streak", 7, "assets/images/streak/streak3.png"),
    ("streak-30", "Thói quen vững vàng", "Học 30 ngày liên tiếp", "streak", 30, "assets/images/streak/streak7.png"),
    ("xp-1000", "Ngàn điểm kinh nghiệm", "Đạt 1000 XP", "xp", 1000, "assets/images/XP.png"),
    ("snapper-10", "Nhiếp ảnh gia nhí", "Nhận diện 10 bức ảnh", "detections", 10, "assets/images/chimcanhcut/chim_muadong.png"),
    ("sharer-5", "Người chia sẻ", "Đăng 5 bài lên cộng đồng", "posts", 5, "assets/images/chimcanhcut/chim_hocnhom2.png"),
]


class Command(BaseCommand):
    help = "Tạo hạng giải đấu Igloo, vật phẩm cửa hàng và huy hiệu"

    def handle(self, *args, **opts):
        for order, (code, name, icon) in enumerate(TIERS):
            LeagueTier.objects.update_or_create(code=code, defaults={"name": name, "order": order, "icon": icon})
        for order, (code, name, desc, image, effect, scales, gems) in enumerate(ITEMS):
            Item.objects.update_or_create(code=code, defaults={
                "name": name, "description": desc, "image": image, "effect": effect,
                "cost_scales": scales, "cost_gems": gems, "order": order})
        for order, (code, name, desc, cond, threshold, icon) in enumerate(BADGES):
            Badge.objects.update_or_create(code=code, defaults={
                "name": name, "description": desc, "condition": cond, "threshold": threshold, "icon": icon, "order": order})
        self.stdout.write(self.style.SUCCESS(f"{len(TIERS)} hạng, {len(ITEMS)} vật phẩm, {len(BADGES)} huy hiệu"))
