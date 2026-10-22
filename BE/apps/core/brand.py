"""LingoPrism's own artwork in the apps (MOBILE/assets/brand, drawn by MOBILE/tool/brand_assets.py).

Paths stored in the database (avatar presets, badges, shop items, league tiers, group icons, notifications) point
there. `brand_path` translates a path of the earlier app's artwork ("assets/images/...") – kept in sync with
MOBILE/lib/app/core/utils/brand_assets.dart.
"""
import re

MASCOT = "assets/brand/mascot/"
AVATARS = [f"assets/brand/avatar/avatar_{i}.png" for i in range(1, 7)]
XP = "assets/brand/icons/xp.png"
XP_DOUBLE = "assets/brand/icons/xp_x2.png"
XP_POTION = "assets/brand/icons/xp_potion.png"
STREAK_FREEZE = "assets/brand/icons/streak_freeze.png"


def streak(level: int) -> str:
    return f"assets/brand/icons/streak_{max(0, min(level, 6))}.png"


def rank(tier: int) -> str:
    """League tier 1..10."""
    return f"assets/brand/rank/rank_{max(1, min(tier, 10))}.png"


def group_icon(i: int) -> str:
    return f"assets/brand/group/group_{max(1, min(i, 5))}.png"


def mascot(name: str) -> str:
    return f"{MASCOT}prismo_{name}.png"


# 10 league tiers, lowest first: from a ray of light to the legendary prism
TIERS = [
    ("tia-sang", "Tia Sáng"), ("anh-dong", "Ánh Đồng"), ("anh-bac", "Ánh Bạc"), ("anh-vang", "Ánh Vàng"),
    ("bach-kim", "Bạch Kim"), ("ngoc-luc", "Ngọc Lục"), ("lam-ngoc", "Lam Ngọc"), ("tu-ngoc", "Tử Ngọc"),
    ("cau-vong", "Cầu Vồng"), ("lang-kinh", "Lăng Kính Huyền Thoại"),
]
# codes of the earlier ladders → the tier at the same place, so members keep their league history
OLD_TIER_CODES = {
    "bang-non": "tia-sang", "vay-dong": "anh-dong", "long-vu-bac": "anh-bac", "igloo-vang": "anh-vang",
    "tang-bang-bach-kim": "bach-kim", "cuc-quang-luc": "ngoc-luc", "dao-bang-lam": "lam-ngoc", "bao-tuyet-tim": "tu-ngoc",
    "thuyen-truong-nam-cuc": "cau-vong", "vuong-mien-cuc-quang": "lang-kinh",
    "tan-binh": "tia-sang", "igloo-dong": "anh-dong", "igloo-bac": "anh-bac", "igloo-kim-cuong": "lang-kinh",
}

_MASCOT_OLD = {
    "chim_vui1": AVATARS[0], "chim_vui": AVATARS[3], "chim_ok": mascot("ok"), "chim_mung": mascot("celebrate"),
    "chim_thich": mascot("love"), "chim_yeu": mascot("love"), "chim_xinchao": mascot("hello"), "chim_chaomung": mascot("hello"),
    "chim_chienthang": mascot("celebrate"), "chim_yes": mascot("celebrate"), "chim_thoibong": mascot("party"),
    "chim_moqua": mascot("gift"), "chim_camqua": mascot("wink"), "chim_camon": mascot("wink"), "chim_nhachoc": mascot("reminder"),
    "chim_hoi": mascot("think"), "chim_xinloi": mascot("sorry"), "chim_chupanh": mascot("camera"), "chim_totnghiep": mascot("graduate"),
}
_MASCOT_FAMILY = {"chim_buon": "sad", "chim_ngu": "sleepy", "chim_hocnhom": "group", "chim_muadong": "explore", "chim_lolang": "think"}
_OTHER = {"XP": XP, "XPx2": XP_DOUBLE, "binhcucquang": XP_POTION, "vay": "assets/brand/icons/scale.png",
          "ngoc": "assets/brand/icons/gem.png", "thongbao": "assets/brand/icons/bell.png", "streakbang": STREAK_FREEZE,
          "nhom_default": "assets/brand/group/group_default.png", "logo": "assets/brand/logo.png"}


def brand_path(path: str) -> str:
    """Old artwork path → LingoPrism artwork; anything else unchanged."""
    if not path or not path.startswith("assets/images/"):
        return path
    name = path.rsplit("/", 1)[-1].removesuffix(".png")
    if "/chimcanhcut/" in path:
        if name in _MASCOT_OLD:
            return _MASCOT_OLD[name]
        family = _MASCOT_FAMILY.get(re.sub(r"\d+$", "", name))
        return mascot(family or "happy")
    if m := re.fullmatch(r"streak(\d)", name):
        return streak(int(m.group(1)))
    if m := re.fullmatch(r"rank(\d+)", name):
        return rank(int(m.group(1)))
    if m := re.fullmatch(r"nhom(\d)", name):
        return group_icon(int(m.group(1)))
    return _OTHER.get(name, mascot("happy"))
