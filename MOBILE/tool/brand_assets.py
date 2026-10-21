"""Draw LingoPrism's own artwork (no third-party images) and export it as PNG for the Flutter app.

Same design as the web (FE/src/components/brand/Brand.tsx): the prism logo, Prismo the mascot, the game icons,
league badges and group icons. Rendered with Playwright + Microsoft Edge (transparent background).

    C:/lpvenv/Scripts/python MOBILE/tool/brand_assets.py      # writes MOBILE/assets/brand/**
"""
import math
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "assets" / "brand"
INK = "#2a1f5c"

BODY = {  # mascot colour schemes: (top, middle, bottom, feet)
    "violet": ("#8f74ff", "#6d4aff", "#3fb5e8", "#4a2fd6"),
    "mint": ("#5eead4", "#10c79a", "#0ea5e9", "#0d8f6f"),
    "coral": ("#ffa3b1", "#ff6b81", "#ffb020", "#d94a63"),
    "amber": ("#ffd36b", "#ffb020", "#ff7a3d", "#d98a00"),
    "sky": ("#93c5fd", "#3fa9f5", "#6d4aff", "#2b7fd0"),
    "pink": ("#f9a8d4", "#ec4899", "#8b5cf6", "#be3a82"),
}


# ---------------------------------------------------------------- mascot
def prismo(mood="happy", color="violet", prop=None, uid="p"):
    """Prismo in a 160x150 box (same geometry as the web component)."""
    top, mid, bot, feet = BODY[color]

    def eye(x):
        if mood in ("celebrate", "party"):
            return f'<path d="M{x-7} 90 Q{x} 81 {x+7} 90" stroke="{INK}" stroke-width="4.5" fill="none" stroke-linecap="round"/>'
        if mood == "sleepy":
            return f'<path d="M{x-7} 88 Q{x} 94 {x+7} 88" stroke="{INK}" stroke-width="4" fill="none" stroke-linecap="round"/>'
        if mood == "love":
            return (f'<path transform="translate({x} 88) scale(0.55)" d="M0 8 C-14 -2 -10 -14 0 -6 C10 -14 14 -2 0 8 Z" fill="#ff4d6d"/>')
        if mood == "wink" and x > 80:
            return f'<path d="M{x-7} 89 Q{x} 84 {x+7} 89" stroke="{INK}" stroke-width="4.5" fill="none" stroke-linecap="round"/>'
        big = mood == "wow"
        dy = 3 if mood in ("sad", "sorry") else -2 if mood == "think" else 1
        rx, ry, r = (9, 10, 5) if big else (7.5, 8.5, 4.4)
        return (f'<ellipse cx="{x}" cy="88" rx="{rx}" ry="{ry}" fill="#fff"/>'
                f'<circle cx="{x + (2 if mood == "think" else 1)}" cy="{88 + dy}" r="{r}" fill="{INK}"/>'
                f'<circle cx="{x + 2.5}" cy="{85 + dy}" r="1.6" fill="#fff"/>')

    mouth = {
        "happy": f'<path d="M70 104 Q80 114 90 104" stroke="{INK}" stroke-width="4" fill="none" stroke-linecap="round"/>',
        "wink": f'<path d="M70 104 Q80 114 90 104" stroke="{INK}" stroke-width="4" fill="none" stroke-linecap="round"/>',
        "love": f'<path d="M70 104 Q80 114 90 104" stroke="{INK}" stroke-width="4" fill="none" stroke-linecap="round"/>',
        "celebrate": f'<path d="M67 101 Q80 122 93 101 Z" fill="{INK}"/><path d="M74 110 Q80 116 86 110 Q80 107 74 110 Z" fill="#ff6b81"/>',
        "party": f'<path d="M67 101 Q80 122 93 101 Z" fill="{INK}"/><path d="M74 110 Q80 116 86 110 Q80 107 74 110 Z" fill="#ff6b81"/>',
        "sleepy": f'<ellipse cx="80" cy="106" rx="4" ry="3" fill="{INK}"/>',
        "think": f'<path d="M72 107 L88 104" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>',
        "sad": f'<path d="M70 110 Q80 101 90 110" stroke="{INK}" stroke-width="4" fill="none" stroke-linecap="round"/>',
        "sorry": f'<path d="M70 110 Q80 103 90 110" stroke="{INK}" stroke-width="4" fill="none" stroke-linecap="round"/>',
        "wow": f'<ellipse cx="80" cy="107" rx="5.5" ry="6.5" fill="{INK}"/>',
    }[mood]

    extra = ""
    if mood == "sad":
        extra += '<path d="M101 97 q4 7 0 9 q-4 -2 0 -9 Z" fill="#7dd3fc"/>'
    if mood == "sorry":
        extra += '<path d="M112 62 q5 8 0 11 q-5 -3 0 -11 Z" fill="#7dd3fc"/>'
    if mood == "sleepy":
        extra += '<text x="112" y="58" font-size="20" font-weight="900" fill="#8f74ff" font-family="Arial Black, sans-serif">z</text><text x="126" y="40" font-size="14" font-weight="900" fill="#b8a8ff" font-family="Arial Black, sans-serif">z</text>'
    if mood == "think":
        extra += '<text x="114" y="60" font-size="26" font-weight="900" fill="#ffb020" font-family="Arial Black, sans-serif">?</text>'
    if mood in ("celebrate", "party"):
        extra += ('<g fill="#ffb020"><path d="M26 40 l3 7 7 3 -7 3 -3 7 -3 -7 -7 -3 7 -3 Z"/></g>'
                  '<path d="M132 34 l2 5 5 2 -5 2 -2 5 -2 -5 -5 -2 5 -2 Z" fill="#10c79a"/>')
    if mood == "love":
        extra += '<path transform="translate(128 46) scale(0.8)" d="M0 8 C-14 -2 -10 -14 0 -6 C10 -14 14 -2 0 8 Z" fill="#ff6b81"/>'

    props = {
        None: "",
        "camera": ('<g transform="translate(54 106)"><rect x="0" y="4" width="52" height="34" rx="8" fill="#2a2f45"/>'
                   '<rect x="14" y="0" width="16" height="8" rx="3" fill="#2a2f45"/>'
                   '<circle cx="26" cy="21" r="11" fill="#5b6280"/><circle cx="26" cy="21" r="7" fill="#9fe8ff"/>'
                   '<circle cx="29" cy="18" r="2.2" fill="#fff"/><circle cx="44" cy="11" r="2.5" fill="#ffb020"/></g>'),
        "cap": ('<g transform="translate(80 18)"><path d="M-34 0 L0 -16 L34 0 L0 16 Z" fill="#2a1f5c"/>'
                '<rect x="-18" y="2" width="36" height="12" rx="3" fill="#2a1f5c"/>'
                '<path d="M28 2 L28 22" stroke="#ffb020" stroke-width="3"/><circle cx="28" cy="24" r="4" fill="#ffb020"/></g>'),
        "gift": ('<g transform="translate(54 108)"><rect x="0" y="8" width="52" height="30" rx="5" fill="#ff6b81"/>'
                 '<rect x="-3" y="0" width="58" height="12" rx="4" fill="#ff8fa3"/><rect x="22" y="0" width="8" height="38" fill="#ffd36b"/>'
                 '<path d="M26 0 C14 -14 6 -2 26 0 C46 -2 38 -14 26 0 Z" fill="#ffd36b"/></g>'),
        "balloons": ('<g><path d="M24 70 L40 116" stroke="#94a3b8" stroke-width="2"/><ellipse cx="22" cy="50" rx="14" ry="18" fill="#ff6b81"/>'
                     '<path d="M138 66 L122 116" stroke="#94a3b8" stroke-width="2"/><ellipse cx="140" cy="46" rx="14" ry="18" fill="#10c79a"/>'
                     '<path d="M12 40 q4 -6 10 -6" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round" opacity="0.7"/></g>'),
        "bell": ('<g transform="translate(124 30) rotate(14)"><path d="M-14 16 Q-14 -10 0 -12 Q14 -10 14 16 L18 20 L-18 20 Z" fill="#ffb020"/>'
                 '<circle cx="0" cy="24" r="4.5" fill="#f08a00"/><circle cx="0" cy="-14" r="3" fill="#f08a00"/></g>'),
        "pin": ('<g transform="translate(130 34)"><path d="M0 26 C-14 8 -14 -6 0 -10 C14 -6 14 8 0 26 Z" fill="#ff6b81"/>'
                '<circle cx="0" cy="0" r="5" fill="#fff"/></g>'),
        "bubble": ('<g transform="translate(104 8)"><rect x="0" y="0" width="54" height="32" rx="12" fill="#fff" stroke="#e4dcff" stroke-width="2"/>'
                   '<path d="M12 30 L8 42 L22 31 Z" fill="#fff"/>'
                   '<text x="27" y="22" text-anchor="middle" font-size="16" font-weight="900" fill="#6d4aff" font-family="Arial Black, sans-serif">Hi!</text></g>'),
        "ok": ('<g transform="translate(128 52)"><circle r="16" fill="#10c79a"/>'
               '<path d="M-7 0 L-2 6 L8 -6" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>'),
    }[prop]

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 150">
<defs><linearGradient id="{uid}b" x1="0.2" y1="0" x2="0.8" y2="1">
<stop offset="0" stop-color="{top}"/><stop offset="0.6" stop-color="{mid}"/><stop offset="1" stop-color="{bot}"/></linearGradient></defs>
<ellipse cx="80" cy="141" rx="44" ry="6" fill="#000" opacity="0.12"/>
<g stroke-linecap="round" stroke-width="6"><path d="M128 92 L151 80" stroke="#ffb020"/><path d="M131 100 L155 99" stroke="#10c79a"/><path d="M128 108 L150 118" stroke="#ff6b81"/></g>
<ellipse cx="62" cy="132" rx="11" ry="6" fill="{feet}"/><ellipse cx="98" cy="132" rx="11" ry="6" fill="{feet}"/>
<path d="M80 16 L140 122 L20 122 Z" fill="url(#{uid}b)" stroke="url(#{uid}b)" stroke-width="18" stroke-linejoin="round"/>
<path d="M80 24 L80 124 L26 124 Z" fill="#fff" opacity="0.12"/>
<path d="M66 46 L56 64" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity="0.65"/>
<ellipse cx="55" cy="101" rx="7" ry="4.5" fill="#ff8fa3" opacity="0.55"/><ellipse cx="105" cy="101" rx="7" ry="4.5" fill="#ff8fa3" opacity="0.55"/>
{eye(64)}{eye(96)}{mouth}{extra}{props}
</svg>'''


def group_of_three():
    """Three Prismos together (studying in a group)."""
    a = prismo("happy", "mint", uid="ga").split(">", 1)[1].rsplit("</svg>", 1)[0]
    b = prismo("celebrate", "violet", uid="gb").split(">", 1)[1].rsplit("</svg>", 1)[0]
    c = prismo("wink", "coral", uid="gc").split(">", 1)[1].rsplit("</svg>", 1)[0]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 150">
<g transform="translate(30 0) scale(0.62)">{b}</g>
<g transform="translate(-4 44) scale(0.62)">{a}</g><g transform="translate(64 44) scale(0.62)">{c}</g></svg>'''


# ---------------------------------------------------------------- logo & icons
LOGO = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#7c5cff"/><stop offset="1" stop-color="#4a2fd6"/></linearGradient></defs>
{bg}<path d="M5 37 L23 33" stroke="#fff" stroke-width="3.5" stroke-linecap="round" opacity="0.9"/>
<path d="M32 13 L49 46 L15 46 Z" fill="#fff" stroke="#fff" stroke-width="5" stroke-linejoin="round"/><path d="M32 16 L32 44 L19 44 Z" fill="#e4dcff"/>
<path d="M43 32 L60 25" stroke="#ffb020" stroke-width="4" stroke-linecap="round"/><path d="M44 36 L61 35" stroke="#10c79a" stroke-width="4" stroke-linecap="round"/>
<path d="M43 40 L59 45" stroke="#ff6b81" stroke-width="4" stroke-linecap="round"/></svg>'''


def flame(c1, c2, inner="#ffe08a", glow=None, sparkle=False):
    g = f'<circle cx="12" cy="13" r="10.5" fill="{glow}" opacity="0.25"/>' if glow else ""
    s = '<path d="M19 3 l0.8 1.9 1.9 0.8 -1.9 0.8 -0.8 1.9 -0.8 -1.9 -1.9 -0.8 1.9 -0.8 Z" fill="#ffd36b"/>' if sparkle else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><defs><linearGradient id="f" x1="0.5" y1="0" x2="0.5" y2="1">
<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>{g}
<path d="M12 2.5C13.2 6 17.5 8 17.5 13.2C17.5 17.4 15 20.5 12 20.5C9 20.5 6.5 17.4 6.5 13.6C6.5 10.8 8 9.3 9 8.2C9.2 10 10 11 11 11.3C10.6 8 11 5 12 2.5Z" fill="url(#f)"/>
<path d="M12 12C13.4 13.4 14.6 14.6 14.6 16.4C14.6 18 13.4 19.2 12 19.2C10.6 19.2 9.4 18 9.4 16.6C9.4 15 10.6 14 12 12Z" fill="{inner}"/>{s}</svg>'''


SCALE = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><defs><linearGradient id="s" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#34e3b5"/><stop offset="1" stop-color="#0891b2"/></linearGradient></defs>
<circle cx="12" cy="12" r="9.5" fill="url(#s)"/><circle cx="12" cy="12" r="9.5" fill="none" stroke="#0e7490" stroke-width="1.2" opacity="0.5"/>
<g fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" opacity="0.9"><path d="M6.5 11 a2.75 2.75 0 0 1 5.5 0"/>
<path d="M12 11 a2.75 2.75 0 0 1 5.5 0"/><path d="M9.25 15 a2.75 2.75 0 0 1 5.5 0"/></g></svg>'''

GEM = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2 L20.5 8.5 L12 22 L3.5 8.5 Z" fill="#6d4aff"/>
<path d="M12 2 L20.5 8.5 L12 10.5 L3.5 8.5 Z" fill="#b8a8ff"/><path d="M3.5 8.5 L12 10.5 L12 22 Z" fill="#8f74ff"/>
<path d="M12 2 L8 8.9 L12 10.5 L16 8.9 Z" fill="#e4dcff" opacity="0.9"/><path d="M12 10.5 L20.5 8.5 L12 22 Z" fill="#06b6d4" opacity="0.55"/></svg>'''

XP = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
<path d="M12 2.2 L14.7 8.4 L21.4 9 L16.3 13.4 L17.9 20 L12 16.5 L6.1 20 L7.7 13.4 L2.6 9 L9.3 8.4 Z" fill="#ffb020" stroke="#f08a00" stroke-width="1" stroke-linejoin="round"/>
<path d="M12.8 7.5 L10.3 12.4 L12.4 12.4 L11.3 16.4 L14.2 11.3 L12.1 11.3 Z" fill="#fff"/>{extra}</svg>'''

XP_X2 = XP.replace("{extra}", '<g transform="translate(14.5 14.5)"><rect x="0" y="0" width="9" height="8" rx="2.5" fill="#6d4aff"/>'
                   '<text x="4.5" y="6.3" text-anchor="middle" font-size="6" font-weight="900" fill="#fff" font-family="Arial Black, sans-serif">x2</text></g>')
XP = XP.replace("{extra}", "")

POTION = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><defs><linearGradient id="l" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#8f74ff"/><stop offset="0.5" stop-color="#3fa9f5"/><stop offset="1" stop-color="#10c79a"/></linearGradient></defs>
<rect x="9" y="2" width="6" height="3" rx="1" fill="#c4b5fd"/><path d="M9.5 5 L14.5 5 L14.5 8.5 C18 9.8 20 12.6 20 15.6 C20 19.6 16.4 22 12 22 C7.6 22 4 19.6 4 15.6 C4 12.6 6 9.8 9.5 8.5 Z" fill="#ede9fe"/>
<path d="M5.2 14 C8 12.6 16 12.6 18.8 14 C19.4 18.6 16 20.8 12 20.8 C8 20.8 4.6 18.6 5.2 14 Z" fill="url(#l)"/>
<path d="M12.5 9.5 L10.8 13 L12.4 13 L11.5 16.5 L13.8 12.3 L12.2 12.3 Z" fill="#fff"/></svg>'''

FREEZE = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><defs><linearGradient id="i" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#e0f2fe"/><stop offset="1" stop-color="#7dd3fc"/></linearGradient></defs>
<path d="M12 2 L20.5 7 L20.5 17 L12 22 L3.5 17 L3.5 7 Z" fill="url(#i)" stroke="#38bdf8" stroke-width="1.2"/>
<path d="M12 7.5C12.8 9.6 15 10.6 15 13.4C15 15.6 13.7 17.2 12 17.2C10.3 17.2 9 15.6 9 13.6C9 12.1 9.8 11.2 10.4 10.6C10.5 11.6 11 12.1 11.5 12.3C11.3 10.5 11.4 9 12 7.5Z" fill="#ff8a3d"/>
<path d="M6 7.5 L9 9.2" stroke="#fff" stroke-width="1.4" stroke-linecap="round" opacity="0.9"/></svg>'''

BELL = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><defs><linearGradient id="b" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#9178ff"/><stop offset="1" stop-color="#5534e0"/></linearGradient></defs>
<path d="M5 17 Q5 7 12 6 Q19 7 19 17 L21 19 L3 19 Z" fill="url(#b)"/><circle cx="12" cy="20.5" r="2.3" fill="#ffb020"/>
<circle cx="12" cy="5" r="1.6" fill="#5534e0"/><path d="M8.5 9.5 Q9 8 10.5 7.6" stroke="#fff" stroke-width="1.3" fill="none" stroke-linecap="round" opacity="0.8"/></svg>'''

# league tiers: light → legendary prism
TIERS = [("Tia Sáng", "#94a3b8", "#cbd5e1"), ("Ánh Đồng", "#c2703d", "#f0a87a"), ("Ánh Bạc", "#7c8aa5", "#dbe3f0"),
         ("Ánh Vàng", "#e0a100", "#ffd76b"), ("Bạch Kim", "#3fa9f5", "#bfe6ff"), ("Ngọc Lục", "#10b981", "#8ff0cf"),
         ("Lam Ngọc", "#2563eb", "#93b8ff"), ("Tử Ngọc", "#7c3aed", "#c4b0ff"), ("Cầu Vồng", "#ec4899", "#ffb3d9"),
         ("Lăng Kính Huyền Thoại", "#6d4aff", "#ffd36b")]


def rank_badge(i):
    name, dark, light = TIERS[i]
    stars = (i % 3) + 1 if i < 9 else 3
    star = lambda x: f'<path transform="translate({x} 53)" d="M0 -4 L1.2 -1.2 L4 -1 L1.9 0.9 L2.5 3.8 L0 2.3 L-2.5 3.8 L-1.9 0.9 L-4 -1 L-1.2 -1.2 Z" fill="#ffd36b"/>'
    sx = [32] if stars == 1 else [27, 37] if stars == 2 else [22, 32, 42]
    rainbow = ('<path d="M14 30 Q32 6 50 30" stroke="#ffb020" stroke-width="3" fill="none"/>'
               '<path d="M17 31 Q32 11 47 31" stroke="#10c79a" stroke-width="3" fill="none"/>'
               '<path d="M20 32 Q32 16 44 32" stroke="#ff6b81" stroke-width="3" fill="none"/>') if i >= 8 else ""
    crown = '<path d="M20 8 L24 14 L32 6 L40 14 L44 8 L42 18 L22 18 Z" fill="#ffd36b" stroke="#e0a100" stroke-width="1"/>' if i == 9 else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs><linearGradient id="r" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="{light}"/><stop offset="1" stop-color="{dark}"/></linearGradient></defs>
<path d="M32 4 L54 12 L54 32 C54 46 44 55 32 60 C20 55 10 46 10 32 L10 12 Z" fill="url(#r)" stroke="{dark}" stroke-width="2"/>
<path d="M32 9 L49 15.5 L49 32 C49 43 41 50.5 32 54.5" fill="#fff" opacity="0.12"/>{rainbow}
<path d="M32 18 L43 38 L21 38 Z" fill="#fff" stroke="#fff" stroke-width="3" stroke-linejoin="round" opacity="0.95"/>
<path d="M32 21 L32 37 L24 37 Z" fill="{light}"/>{crown}
<text x="32" y="48" text-anchor="middle" font-size="9" font-weight="900" fill="#fff" font-family="Arial Black, sans-serif">{i + 1}</text>
{"".join(star(x) for x in sx)}</svg>'''


RANK_LOCKED = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<path d="M32 4 L54 12 L54 32 C54 46 44 55 32 60 C20 55 10 46 10 32 L10 12 Z" fill="#e5e7eb" stroke="#cbd5e1" stroke-width="2"/>
<rect x="22" y="28" width="20" height="16" rx="3" fill="#94a3b8"/><path d="M26 28 V23 a6 6 0 0 1 12 0 V28" stroke="#94a3b8" stroke-width="3.5" fill="none"/>
<circle cx="32" cy="35" r="2.5" fill="#e5e7eb"/></svg>'''


GROUP_COLORS = [("#6d4aff", "#3fa9f5"), ("#10c79a", "#0ea5e9"), ("#ff6b81", "#ffb020"), ("#ffb020", "#ff7a3d"), ("#ec4899", "#8b5cf6"),
                ("#64748b", "#94a3b8")]


def group_icon(i):
    a, b = GROUP_COLORS[i]
    shapes = ['<path d="M32 16 L46 42 L18 42 Z" fill="#fff" stroke="#fff" stroke-width="4" stroke-linejoin="round"/>',
              '<g fill="#fff"><circle cx="24" cy="26" r="7"/><circle cx="40" cy="26" r="7"/><path d="M12 46 Q24 32 32 44 Q40 32 52 46 Z"/></g>',
              '<path d="M32 46 C14 34 18 18 32 26 C46 18 50 34 32 46 Z" fill="#fff"/>',
              '<path d="M32 14 L36 27 L50 27 L39 35 L43 48 L32 40 L21 48 L25 35 L14 27 L28 27 Z" fill="#fff"/>',
              '<g fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round"><path d="M16 40 Q32 12 48 40"/><path d="M22 42 Q32 24 42 42"/></g>',
              '<g fill="#fff"><circle cx="32" cy="24" r="8"/><path d="M16 48 Q32 30 48 48 Z"/></g>'][i]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient></defs>
<rect x="2" y="2" width="60" height="60" rx="18" fill="url(#g)"/><circle cx="52" cy="10" r="14" fill="#fff" opacity="0.12"/>{shapes}</svg>'''


def assets():
    out = {}
    mascots = {
        "prismo_happy": ("happy", "violet", None), "prismo_wink": ("wink", "violet", None),
        "prismo_love": ("love", "violet", None), "prismo_hello": ("happy", "violet", "bubble"),
        "prismo_celebrate": ("celebrate", "violet", None), "prismo_party": ("party", "violet", "balloons"),
        "prismo_gift": ("celebrate", "violet", "gift"), "prismo_think": ("think", "violet", None),
        "prismo_reminder": ("wow", "violet", "bell"), "prismo_sad": ("sad", "violet", None),
        "prismo_sorry": ("sorry", "violet", None), "prismo_sleepy": ("sleepy", "violet", None),
        "prismo_camera": ("happy", "violet", "camera"), "prismo_explore": ("wow", "violet", "pin"),
        "prismo_graduate": ("celebrate", "violet", "cap"), "prismo_ok": ("wink", "violet", "ok"),
        "prismo_wow": ("wow", "violet", None),
    }
    for name, (mood, color, prop) in mascots.items():
        out[f"mascot/{name}.png"] = (prismo(mood, color, prop, uid=name), 512, 480)
    out["mascot/prismo_group.png"] = (group_of_three(), 512, 480)
    for i, (color, mood) in enumerate([("violet", "happy"), ("mint", "wink"), ("coral", "celebrate"),
                                       ("amber", "happy"), ("sky", "love"), ("pink", "wow")], 1):
        out[f"avatar/avatar_{i}.png"] = (prismo(mood, color, uid=f"a{i}"), 384, 360)
    for i, (c1, c2, inner, glow, sp) in enumerate([
        ("#d6d3e3", "#9893b3", "#eceaf3", None, False), ("#ffd36b", "#ff9a3c", "#fff1b8", None, False),
        ("#ffc04d", "#ff7a3d", "#ffe08a", None, True), ("#ffb020", "#ff5a3c", "#ffe08a", "#ffb020", True),
        ("#ff8a3d", "#f43f5e", "#ffd36b", "#ff6b81", True), ("#f472b6", "#8b5cf6", "#ffd6f0", "#ec4899", True),
        ("#7dd3fc", "#6d4aff", "#e0f2fe", "#8b5cf6", True)]):
        out[f"icons/streak_{i}.png"] = (flame(c1, c2, inner, glow, sp), 256, 256)
    out.update({"icons/streak_freeze.png": (FREEZE, 256, 256), "icons/scale.png": (SCALE, 256, 256),
                "icons/gem.png": (GEM, 256, 256), "icons/xp.png": (XP, 256, 256), "icons/xp_x2.png": (XP_X2, 256, 256),
                "icons/xp_potion.png": (POTION, 256, 256), "icons/bell.png": (BELL, 256, 256)})
    for i in range(10):
        out[f"rank/rank_{i + 1}.png"] = (rank_badge(i), 256, 256)
    out["rank/rank_locked.png"] = (RANK_LOCKED, 256, 256)
    for i in range(6):
        out[f"group/group_{i + 1 if i < 5 else 'default'}.png"] = (group_icon(i), 256, 256)
    rect = '<rect width="64" height="64" rx="16" fill="url(#bg)"/>'
    out["logo.png"] = (LOGO.replace("{bg}", rect), 1024, 1024)
    out["logo_square.png"] = (LOGO.replace("{bg}", '<rect width="64" height="64" fill="url(#bg)"/>'), 1024, 1024)
    # adaptive icon foreground: the mark inside the 66% safe zone, transparent around it
    fg = LOGO.replace("{bg}", "").replace('viewBox="0 0 64 64"', 'viewBox="-17 -17 98 98"')
    out["logo_foreground.png"] = (fg, 1024, 1024)
    return out


def main():
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    items = assets()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_page()
        for rel, (svg, w, h) in items.items():
            page.set_viewport_size({"width": w, "height": h})
            page.set_content(f'<html><body style="margin:0;background:transparent">'
                             f'<div style="width:{w}px;height:{h}px">{svg.replace("<svg ", f"<svg width={chr(34)}{w}{chr(34)} height={chr(34)}{h}{chr(34)} ", 1)}</div></body></html>')
            target = OUT / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            page.locator("div").first.screenshot(path=str(target), omit_background=True)
        browser.close()
    print(f"{len(items)} ảnh → {OUT}")


if __name__ == "__main__":
    main()
