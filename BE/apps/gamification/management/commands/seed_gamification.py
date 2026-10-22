from django.core.management.base import BaseCommand
from django.db.models import F

from apps.gamification.models import Badge, Item, LeagueTier

from apps.core import brand

TIERS = brand.TIERS  # 10 tiers, lowest first – icons assets/brand/rank/rank_1..10.png
OLD_TIER_CODES = brand.OLD_TIER_CODES
ITEMS = [
    ("streak_freeze", "Đá băng", "Giữ chuỗi streak khi nghỉ 1 ngày", brand.STREAK_FREEZE, "streak_freeze", 200, None),
    ("xp_boost", "Vảy tăng tốc", "Nhận đôi XP trong 15 phút", brand.XP_DOUBLE, "xp_double_15m", 150, None),
    ("super_boost", "Bình ánh sáng", "Tăng 25% XP toàn app trong 24 giờ", brand.XP_POTION, "xp_plus25_24h", None, 2),
    ("sticker_ok", "Sticker OK", "Dùng sticker trong chat nhóm & bình luận", brand.mascot("ok"), "sticker", None, 2),
    ("sticker_love", "Sticker yêu ngất ngây", "Dùng sticker trong chat nhóm & bình luận", brand.mascot("love"), "sticker", None, 2),
    ("sticker_sad", "Sticker buồn hiu", "Dùng sticker trong chat nhóm & bình luận", brand.mascot("sad"), "sticker", None, 2),
]
BADGES = [
    ("first-steps", "Bước chân đầu tiên", "Học những từ đầu tiên", "words_learned", 1, brand.mascot("hello")),
    ("word-collector-50", "Nhà sưu tầm từ", "Học 50 từ", "words_learned", 50, brand.mascot("group")),
    ("word-master-100", "Bậc thầy từ vựng", "Thuộc 100 từ", "words_mastered", 100, brand.mascot("graduate")),
    ("streak-3", "Khởi động", "Học 3 ngày liên tiếp", "streak", 3, brand.streak(2)),
    ("streak-7", "Một tuần kiên trì", "Học 7 ngày liên tiếp", "streak", 7, brand.streak(4)),
    ("streak-30", "Thói quen vững vàng", "Học 30 ngày liên tiếp", "streak", 30, brand.streak(6)),
    ("xp-1000", "Ngàn điểm kinh nghiệm", "Đạt 1000 XP", "xp", 1000, brand.XP),
    ("snapper-10", "Nhiếp ảnh gia nhí", "Nhận diện 10 bức ảnh", "detections", 10, brand.mascot("camera")),
    ("sharer-5", "Người chia sẻ", "Đăng 5 bài lên cộng đồng", "posts", 5, brand.mascot("party")),
]


class Command(BaseCommand):
    help = "Tạo 10 hạng giải đấu, vật phẩm cửa hàng và huy hiệu"

    def handle(self, *args, **opts):
        for old, new in OLD_TIER_CODES.items():
            if not LeagueTier.objects.filter(code=new).exists():
                LeagueTier.objects.filter(code=old).update(code=new)
        LeagueTier.objects.update(order=F("order") + 1000)  # "order" is unique: free the slots before renumbering
        for order, (code, name) in enumerate(TIERS):
            LeagueTier.objects.update_or_create(code=code, defaults={
                "name": name, "order": order, "icon": brand.rank(order + 1)})
        for order, (code, name, desc, image, effect, scales, gems) in enumerate(ITEMS):
            Item.objects.update_or_create(code=code, defaults={
                "name": name, "description": desc, "image": image, "effect": effect,
                "cost_scales": scales, "cost_gems": gems, "order": order})
        for order, (code, name, desc, cond, threshold, icon) in enumerate(BADGES):
            Badge.objects.update_or_create(code=code, defaults={
                "name": name, "description": desc, "condition": cond, "threshold": threshold, "icon": icon, "order": order})
        self.stdout.write(self.style.SUCCESS(f"{len(TIERS)} hạng, {len(ITEMS)} vật phẩm, {len(BADGES)} huy hiệu"))
