"""Prismo's outfits (catalog.OUTFITS), the new prices (vảy for help, ngọc for looks) and the pieces that badges
already earned unlock."""
from django.db import migrations

from apps.gamification.sync import sync_catalog


def forwards(apps, schema_editor):
    get = apps.get_model
    Outfit, UserOutfit = get("gamification", "Outfit"), get("gamification", "UserOutfit")
    sync_catalog(get("gamification", "Item"), get("gamification", "Badge"), get("gamification", "UserInventory"), Outfit)
    by_badge = {}
    for outfit in Outfit.objects.exclude(badge_code=""):
        by_badge.setdefault(outfit.badge_code, []).append(outfit)
    for user_id, code in get("gamification", "UserBadge").objects.values_list("user_id", "badge__code"):
        for outfit in by_badge.get(code, []):
            UserOutfit.objects.get_or_create(user_id=user_id, outfit=outfit)


class Migration(migrations.Migration):
    dependencies = [("gamification", "0005_mascot")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
