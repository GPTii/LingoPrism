from django.core.management.base import BaseCommand
from django.db.models import F

from apps.gamification.models import Badge, Item, LeagueTier, Outfit, UserInventory
from apps.gamification.sync import sync_catalog

from apps.core import brand

TIERS = brand.TIERS  # 10 tiers, lowest first – icons assets/brand/rank/rank_1..10.png
OLD_TIER_CODES = brand.OLD_TIER_CODES


class Command(BaseCommand):
    help = "Tạo 10 hạng giải đấu, vật phẩm cửa hàng, gói sticker và huy hiệu (apps/gamification/catalog.py)"

    def handle(self, *args, **opts):
        for old, new in OLD_TIER_CODES.items():
            if not LeagueTier.objects.filter(code=new).exists():
                LeagueTier.objects.filter(code=old).update(code=new)
        LeagueTier.objects.update(order=F("order") + 1000)  # "order" is unique: free the slots before renumbering
        for order, (code, name) in enumerate(TIERS):
            LeagueTier.objects.update_or_create(code=code, defaults={
                "name": name, "order": order, "icon": brand.rank(order + 1)})
        items, badges = sync_catalog(Item, Badge, UserInventory, Outfit)
        self.stdout.write(self.style.SUCCESS(f"{len(TIERS)} hạng, {items} vật phẩm, {badges} huy hiệu"))
