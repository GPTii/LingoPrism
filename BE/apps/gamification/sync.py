"""Write the rewards catalogue (catalog.py) to the database: shop items, sticker packs, badges and Prismo's outfits.

Takes the model classes as arguments so a data migration can pass its historical models.
"""
from . import catalog


def sync_catalog(Item, Badge, UserInventory=None, Outfit=None):
    order = 0
    for code, name, desc, image, effect, scales, gems in catalog.ITEMS:
        Item.objects.update_or_create(code=code, defaults={
            "name": name, "description": desc, "image": image, "effect": effect, "cost_scales": scales,
            "cost_gems": gems, "order": order, "active": True})
        order += 1
    for pack in catalog.STICKER_PACKS:
        captions = ", ".join(t for _, t in pack["stickers"][:3])
        Item.objects.update_or_create(code=pack["code"], defaults={
            "name": pack["name"], "description": f"{len(pack['stickers'])} sticker: {captions}…",
            "image": catalog.sticker_path(pack["stickers"][0][0]), "effect": "sticker",
            "cost_scales": pack["cost_scales"], "cost_gems": pack["cost_gems"], "order": order, "active": True})
        order += 1
    # the single stickers sold before the packs: no longer sold, their owners get the pack instead
    Item.objects.filter(code__in=catalog.LEGACY_STICKERS).update(active=False)
    if UserInventory is not None:
        packs = {i.code: i for i in Item.objects.filter(code__in=set(catalog.LEGACY_STICKERS.values()))}
        for inv in UserInventory.objects.filter(item__code__in=catalog.LEGACY_STICKERS, quantity__gt=0).select_related("item"):
            pack = packs[catalog.LEGACY_STICKERS[inv.item.code]]
            UserInventory.objects.get_or_create(user_id=inv.user_id, item=pack, defaults={"quantity": 1})

    for i, b in enumerate(catalog.BADGES):
        Badge.objects.update_or_create(code=b["code"], defaults={
            "name": b["name"], "description": b["description"], "condition": b["condition"],
            "threshold": b["threshold"], "reward_gems": b["gems"], "icon": catalog.badge_path(b["code"]), "order": i})
    if Outfit is not None:
        for i, o in enumerate(catalog.OUTFITS):
            Outfit.objects.update_or_create(code=o["code"], defaults={
                "name": o["name"], "slot": o["slot"], "image": catalog.outfit_path(o["code"]), "cost_gems": o["gems"],
                "badge_code": o["badge"], "event": o["event"], "order": i, "active": True})
    return order, len(catalog.BADGES)
