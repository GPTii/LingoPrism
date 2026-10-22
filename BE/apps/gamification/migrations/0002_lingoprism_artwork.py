"""LingoPrism's own artwork: asset paths of the earlier app stored in the database → assets/brand/...,
and the 10 league tiers renamed (same order and members, light-themed names)."""
from django.db import migrations

from apps.core.brand import OLD_TIER_CODES, TIERS, brand_path, rank

FIELDS = [
    ("accounts", "User", "avatar_preset"),
    ("community", "Group", "icon"),
    ("gamification", "Badge", "icon"),
    ("gamification", "Item", "image"),
    ("gamification", "LeagueTier", "icon"),
    ("notifications", "Notification", "image"),
]


def forwards(apps, schema_editor):
    for app, model, field in FIELDS:
        Model = apps.get_model(app, model)
        for obj in Model.objects.filter(**{f"{field}__startswith": "assets/images/"}).only("pk", field):
            Model.objects.filter(pk=obj.pk).update(**{field: brand_path(getattr(obj, field))})

    Item = apps.get_model("gamification", "Item")
    Item.objects.filter(code="super_boost").update(name="Bình ánh sáng")

    LeagueTier = apps.get_model("gamification", "LeagueTier")
    names = dict(TIERS)
    for tier in LeagueTier.objects.all():
        code = OLD_TIER_CODES.get(tier.code)
        if code and not LeagueTier.objects.filter(code=code).exclude(pk=tier.pk).exists():
            index = [c for c, _ in TIERS].index(code)
            LeagueTier.objects.filter(pk=tier.pk).update(code=code, name=names[code], icon=rank(index + 1))


class Migration(migrations.Migration):
    dependencies = [
        ("gamification", "0001_initial"),
        ("accounts", "0002_user_avatar_preset"),
        ("community", "0002_initial"),
        ("notifications", "0001_initial"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
