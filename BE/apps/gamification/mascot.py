"""Each learner's Prismo: its wardrobe, what it wears and how it looks to others.

Pieces come three ways (catalog.OUTFITS): bought with ngọc, unlocked by a badge (never sold), or sold only during a
festival (catalog.EVENTS). A piece once owned is kept for good.
"""
from datetime import date

from django.db import transaction

from . import catalog
from .models import Mascot, Outfit, UserBadge, UserOutfit

SLOTS = [code for code, _ in catalog.SLOTS]
BADGE_NAMES = {b["code"]: b["name"] for b in catalog.BADGES}


class MascotError(Exception):
    pass


def event_window(event: str, day: date) -> tuple[date, date] | None:
    """This festival's window that contains `day`, else the next one (None once none is left)."""
    e = catalog.EVENTS.get(event)
    if not e:
        return None
    if "yearly" in e:
        start, end = e["yearly"]
        for year in (day.year, day.year + 1):
            window = date.fromisoformat(f"{year}-{start}"), date.fromisoformat(f"{year}-{end}")
            if day <= window[1]:
                return window
        return None
    for start, end in e["dates"]:
        window = date.fromisoformat(start), date.fromisoformat(end)
        if day <= window[1]:
            return window
    return None


def event_open(event: str, day: date) -> bool:
    window = event_window(event, day)
    return bool(window and window[0] <= day <= window[1])


def how_to_get(outfit: Outfit, day: date) -> str:
    """One line saying how this piece is had, for the wardrobe."""
    if outfit.badge_code:
        return f"Mở khoá bằng huy hiệu “{BADGE_NAMES.get(outfit.badge_code, outfit.badge_code)}”"
    if outfit.event:
        name = catalog.EVENTS[outfit.event]["name"]
        window = event_window(outfit.event, day)
        if window and window[0] <= day:
            return f"Chỉ bán dịp {name}, đến hết {window[1]:%d/%m}"
        if window:
            return f"Chỉ bán dịp {name}, từ {window[0]:%d/%m}"
        return f"Chỉ có trong dịp {name}"
    return ""


def for_sale(outfit: Outfit, day: date) -> bool:
    return bool(outfit.active and outfit.cost_gems and not outfit.badge_code and (not outfit.event or event_open(outfit.event, day)))


def mascot_for(user) -> Mascot:
    return Mascot.objects.get_or_create(user=user)[0]


def owned_codes(user) -> set[str]:
    return set(UserOutfit.objects.filter(user=user).values_list("outfit__code", flat=True))


def look(user) -> dict | None:
    """What others see: the piece in each slot and whether Prismo stands in for the photo. None: plain Prismo."""
    try:
        m = user.mascot
    except Mascot.DoesNotExist:
        return None
    return {"name": m.name, "as_avatar": m.as_avatar, **{slot: getattr(m, slot) for slot in SLOTS}}


def grant_for_badge(user, badge_code: str) -> list[str]:
    """Give the pieces a badge unlocks; returns the names of those that are new."""
    names = []
    for outfit in Outfit.objects.filter(badge_code=badge_code, active=True):
        if UserOutfit.objects.get_or_create(user=user, outfit=outfit)[1]:
            names.append(outfit.name)
    return names


def grant_earned(user) -> None:
    """Every piece the user's badges unlock (for badges earned before the wardrobe existed)."""
    for code in UserBadge.objects.filter(user=user).values_list("badge__code", flat=True):
        grant_for_badge(user, code)


@transaction.atomic
def buy(user, outfit: Outfit, day: date) -> int:
    """Pay the ngọc and keep the piece; returns the gems left."""
    from apps.accounts.models import User

    u = User.objects.select_for_update().get(pk=user.pk)
    if UserOutfit.objects.filter(user=u, outfit=outfit).exists():
        raise MascotError("Prismo đã có món này rồi")
    if outfit.badge_code:
        raise MascotError(f"Món này không bán: {how_to_get(outfit, day).lower()}")
    if not for_sale(outfit, day):
        raise MascotError(how_to_get(outfit, day) or "Món này không bán")
    if u.gems_balance < outfit.cost_gems:
        raise MascotError("Không đủ Ngọc")
    u.gems_balance -= outfit.cost_gems
    u.save(update_fields=["gems_balance"])
    UserOutfit.objects.create(user=u, outfit=outfit)
    return u.gems_balance


def dress(user, changes: dict, name: str | None = None, as_avatar: bool | None = None) -> Mascot:
    """Put on (code) or take off ("") one piece per slot; only pieces the user owns, each in its own slot."""
    m = mascot_for(user)
    owned = owned_codes(user)
    slots = dict(Outfit.objects.filter(code__in=[c for c in changes.values() if c]).values_list("code", "slot"))
    for slot, code in changes.items():
        if slot not in SLOTS:
            raise MascotError(f"Không có ô “{slot}”")
        code = code or ""
        if code and (code not in owned or slots.get(code) != slot):
            raise MascotError("Prismo chưa có món này")
        setattr(m, slot, code)
    if name is not None:
        name = name.strip()
        if not 1 <= len(name) <= 20:
            raise MascotError("Tên Prismo dài từ 1 đến 20 ký tự")
        m.name = name
    if as_avatar is not None:
        m.as_avatar = bool(as_avatar)
    m.save()
    return m
