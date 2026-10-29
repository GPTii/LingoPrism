"""LingoPrism rewards artwork: sticker packs, badge medals and shop item icons, drawn in code (no third-party art).

Writes the same PNGs for the web (FE/public/rewards/...) and the app (MOBILE/assets/rewards/...). Codes and captions
come from the server's catalogue (BE/apps/gamification/catalog.py), so the files always match what can be bought or
earned. Rendered with headless Edge or Chrome; text uses Be Vietnam Pro from MOBILE/assets/fonts.

    python FE/scripts/make-rewards.py [sheet.png]
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")).replace(os.sep, "/") + "/"
OUT = [ROOT + "FE/public/rewards/", ROOT + "MOBILE/assets/rewards/"]
FONT = ROOT + "MOBILE/assets/fonts/BeVietnamPro-ExtraBold.ttf"

spec = importlib.util.spec_from_file_location("catalog", ROOT + "BE/apps/gamification/catalog.py")
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)

BODY, LIP, INK = "#5cc6ff", "#0f78c8", "#15233b"
HEART, GOLD, MINT, CORAL = "#ff4b6e", "#ffc800", "#10c79a", "#ff6b81"


# ---------------------------------------------------------------- Prismo, sticker edition (160 grid)

def heart(x, y, s=1.0, fill=HEART):
    return (f'<path transform="translate({x} {y}) scale({s})" d="M0 9 C-17 -3 -11 -17 0 -7 C11 -17 17 -3 0 9 Z" '
            f'fill="{fill}" stroke="{fill}" stroke-width="3" stroke-linejoin="round"/>')


def star(x, y, r=10, fill=GOLD, rot=0):
    import math
    pts = []
    for i in range(10):
        a = math.radians(rot - 90 + i * 36)
        rr = r if i % 2 == 0 else r * 0.48
        pts.append(f"{x + rr * math.cos(a):.1f} {y + rr * math.sin(a):.1f}")
    return f'<path d="M{" L".join(pts)} Z" fill="{fill}" stroke="{fill}" stroke-width="2.5" stroke-linejoin="round"/>'


def sparkle(x, y, s=1.0, fill=GOLD):
    return (f'<path transform="translate({x} {y}) scale({s})" d="M0 -10 Q2 -2 10 0 Q2 2 0 10 Q-2 2 -10 0 Q-2 -2 0 -10 Z" '
            f'fill="{fill}"/>')


def eyes(kind):
    out = ""
    for i, x in enumerate((60, 100)):
        k = kind
        if kind == "wink":
            k = "normal" if i == 0 else "happy"
        if k in ("normal", "side", "up", "teary", "puppy", "determined"):
            px = {"side": 6, "up": 2}.get(k, 3)
            py = {"side": 2, "up": -7}.get(k, 4)
            pupil = (10.5, 12.5) if k in ("puppy", "teary") else (8.5, 10.5)
            out += (f'<ellipse cx="{x}" cy="89" rx="17.5" ry="21" fill="#fff"/>'
                    f'<ellipse cx="{x + px}" cy="{89 + py}" rx="{pupil[0]}" ry="{pupil[1]}" fill="{INK}"/>'
                    f'<circle cx="{x + px + 3.5}" cy="{89 + py - 5.5}" r="3.6" fill="#fff"/>')
            if k in ("puppy", "teary"):
                out += f'<circle cx="{x + px - 3}" cy="{89 + py + 5}" r="1.8" fill="#fff"/>'
            if k == "teary":
                out += f'<path d="M{x - 13} 99 Q{x} 106 {x + 13} 99 L{x + 13} 104 Q{x} 112 {x - 13} 104 Z" fill="#7dd3fc" opacity="0.9"/>'
        elif k == "happy":
            out += f'<path d="M{x - 12} 95 Q{x} 77 {x + 12} 95" fill="none" stroke="{INK}" stroke-width="6.5" stroke-linecap="round"/>'
        elif k == "laugh":
            d = (f"M{x - 10} 82 L{x + 8} 91 L{x - 10} 100" if i == 0 else f"M{x + 10} 82 L{x - 8} 91 L{x + 10} 100")
            out += f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round"/>'
        elif k == "sleepy":
            out += f'<path d="M{x - 12} 90 Q{x} 99 {x + 12} 90" fill="none" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
        elif k == "hearts":
            out += heart(x, 88, 1.25)
            out += f'<ellipse cx="{x - 5}" cy="83" rx="3.5" ry="2.5" fill="#fff" opacity="0.7"/>'
        elif k == "stars":
            out += star(x, 89, 16, GOLD, rot=8 if i else -8)
            out += f'<circle cx="{x - 4}" cy="84" r="2.6" fill="#fff" opacity="0.85"/>'
        elif k == "wide":
            out += (f'<ellipse cx="{x}" cy="88" rx="19" ry="23" fill="#fff"/>'
                    f'<circle cx="{x + 2}" cy="89" r="6.5" fill="{INK}"/><circle cx="{x + 4.5}" cy="86" r="2.2" fill="#fff"/>')
    if kind == "determined":
        out += (f'<path d="M44 66 L74 74" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
                f'<path d="M116 66 L86 74" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>')
    if kind in ("puppy", "teary"):
        out += (f'<path d="M48 70 Q58 62 70 66" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
                f'<path d="M112 70 Q102 62 90 66" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>')
    if kind == "side":
        out += f'<path d="M86 68 Q100 60 114 67" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
    return out


def mouth(kind):
    return {
        "smile": f'<path d="M72 113 Q80 121 88 113" fill="none" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>',
        "big": (f'<path d="M66 109 Q80 133 94 109 Z" fill="{INK}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
                f'<path d="M72 121 Q80 127 88 121 Q80 116 72 121 Z" fill="{CORAL}"/>'),
        "o": f'<ellipse cx="80" cy="117" rx="6.5" ry="8.5" fill="{INK}"/>',
        "sad": f'<path d="M71 120 Q80 111 89 120" fill="none" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>',
        "wobbly": f'<path d="M70 118 Q75 113 80 118 Q85 123 90 118" fill="none" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>',
        "cat": f'<path d="M70 113 Q75 120 80 113 Q85 120 90 113" fill="none" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>',
        "grin": (f'<path d="M65 108 L95 108 Q93 126 80 126 Q67 126 65 108 Z" fill="{INK}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
                 f'<path d="M68 109 L92 109 L91 114 L69 114 Z" fill="#fff"/>'),
        "flat": f'<path d="M73 116 L87 114" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>',
        "small": f'<ellipse cx="80" cy="117" rx="4" ry="3.2" fill="{INK}"/>',
    }[kind]


ARMS = {  # (from, to) per arm, drawn behind the body; the hand is drawn on top
    "wave_r": [((124, 104), (150, 66))],
    "wave_l": [((36, 104), (10, 66))],
    "cheer": [((36, 104), (12, 62)), ((124, 104), (148, 62))],
    "rest": [((40, 112), (16, 128)), ((120, 112), (144, 128))],
    "hold": [((40, 108), (52, 128)), ((120, 108), (108, 128))],
    "fist": [((124, 104), (150, 70)), ((40, 112), (18, 126))],
    "point": [((124, 104), (152, 92))],
    "clap": [((40, 110), (68, 144)), ((120, 110), (92, 144))],
    "hold_wide": [((38, 106), (36, 134)), ((122, 106), (124, 134))],
    "cheek": [((40, 108), (40, 122)), ((120, 108), (120, 122))],
}


def arms(kind):
    if not kind:
        return "", ""
    back = front = ""
    for (x1, y1), (x2, y2) in ARMS[kind]:
        back += (f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{LIP}" stroke-width="19" stroke-linecap="round"/>'
                 f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{BODY}" stroke-width="13" stroke-linecap="round"/>')
        front += f'<circle cx="{x2}" cy="{y2}" r="10" fill="{BODY}" stroke="{LIP}" stroke-width="3.5"/>'
    return back, front


def prismo(eye="normal", mouth_kind="smile", arm=None, prop_back="", prop_front="", hat="", beams=True, blush=True):
    tri = "M80 22 L138 124 L22 124 Z"
    back, hands = arms(arm)
    return (
        prop_back
        + (f'<g stroke-width="7" stroke-linecap="round"><path d="M131 95 L152 84" stroke="#ffb020"/>'
           f'<path d="M134 104 L157 104" stroke="{MINT}"/><path d="M131 113 L152 124" stroke="{CORAL}"/></g>' if beams else "")
        + back
        + f'<ellipse cx="62" cy="139" rx="12" ry="7" fill="{LIP}"/><ellipse cx="98" cy="139" rx="12" ry="7" fill="{LIP}"/>'
        + f'<path d="{tri}" transform="translate(0 7)" fill="{LIP}" stroke="{LIP}" stroke-width="22" stroke-linejoin="round"/>'
        + f'<path d="{tri}" fill="{BODY}" stroke="{BODY}" stroke-width="22" stroke-linejoin="round"/>'
        + '<path d="M80 22 L80 124 L22 124 Z" fill="#fff" opacity="0.10"/>'
        + '<path d="M67 43 L58 59" stroke="#fff" stroke-width="6" stroke-linecap="round" opacity="0.65"/>'
        + ('<ellipse cx="42" cy="112" rx="8" ry="5" fill="#ff8fa3" opacity="0.8"/>'
           '<ellipse cx="118" cy="112" rx="8" ry="5" fill="#ff8fa3" opacity="0.8"/>' if blush else "")
        + eyes(eye) + mouth(mouth_kind) + hat + prop_front + hands
    )


# props --------------------------------------------------------------

def bubble(text, x=118, y=20, fill="#fff", color=INK, size=17):
    w = max(44, len(text) * size * 0.62 + 18)
    return (f'<g transform="translate({x} {y})"><rect x="{-w / 2}" y="-17" width="{w}" height="34" rx="14" fill="{fill}" stroke="{LIP}" stroke-width="3"/>'
            f'<path d="M-14 15 L-22 30 L-2 16 Z" fill="{fill}" stroke="{LIP}" stroke-width="3" stroke-linejoin="round"/>'
            f'<rect x="-15" y="10" width="14" height="6" fill="{fill}"/>'
            f'<text x="0" y="6" text-anchor="middle" font-size="{size}" fill="{color}" {FONTATTR}>{text}</text></g>')


FONTATTR = 'font-family="LP, Be Vietnam Pro, Microsoft YaHei, sans-serif" font-weight="800"'
ZZZ = (f'<text x="120" y="40" font-size="26" fill="#6d7cff" {FONTATTR}>z</text>'
       f'<text x="138" y="22" font-size="18" fill="#9aa6ff" {FONTATTR}>z</text>')
MOON = '<path d="M30 20 A18 18 0 1 0 50 44 A14 14 0 1 1 30 20 Z" fill="#ffd23f" stroke="#e0a800" stroke-width="2.5"/>'
NIGHTCAP = (f'<path d="M58 30 Q78 -6 112 8 Q96 14 100 34 Z" fill="#6d7cff" stroke="#4f5bd5" stroke-width="3" stroke-linejoin="round"/>'
            f'<path d="M54 32 Q80 22 104 34" stroke="#fff" stroke-width="8" stroke-linecap="round" fill="none"/>'
            f'<circle cx="114" cy="8" r="7" fill="#fff"/>')
TEAR = '<path d="M134 64 Q142 76 134 82 Q126 76 134 64 Z" fill="#7dd3fc" stroke="#38bdf8" stroke-width="2"/>'
SWEAT = '<path d="M126 52 Q136 66 126 72 Q116 66 126 52 Z" fill="#9fe3ff" stroke="#38bdf8" stroke-width="2.5"/>'
CLOUD = ('<g transform="translate(118 26)"><path d="M-22 6 Q-24 -8 -10 -8 Q-6 -20 8 -16 Q20 -18 22 -4 Q32 -2 28 8 Z" fill="#b8c4d6" '
         'stroke="#8d9bb2" stroke-width="2.5" stroke-linejoin="round"/>'
         '<path d="M-10 14 l-3 8 M2 14 l-3 8 M14 14 l-3 8" stroke="#7dd3fc" stroke-width="3" stroke-linecap="round"/></g>')
QUESTION = (f'<text x="122" y="44" font-size="38" fill="#ff9600" stroke="#fff" stroke-width="2" {FONTATTR}>?</text>'
            f'<text x="20" y="40" font-size="26" fill="#ffc800" {FONTATTR} transform="rotate(-14 26 30)">?</text>')
EXCLAIM = (f'<g transform="translate(130 36) rotate(12)"><rect x="-6" y="-24" width="12" height="28" rx="6" fill="{CORAL}"/>'
           f'<circle cx="0" cy="13" r="6.5" fill="{CORAL}"/></g>'
           f'<g transform="translate(26 40) rotate(-16)"><rect x="-4.5" y="-18" width="9" height="21" rx="4.5" fill="#ffc800"/>'
           f'<circle cx="0" cy="10" r="5" fill="#ffc800"/></g>')
HEADBAND = (f'<path d="M30 62 Q80 46 130 62 L127 74 Q80 59 33 74 Z" fill="{CORAL}" stroke="#d94a63" stroke-width="2.5" stroke-linejoin="round"/>'
            f'<path d="M128 66 L150 56 L146 72 Z M128 68 L148 80 L134 84 Z" fill="{CORAL}" stroke="#d94a63" stroke-width="2.5" stroke-linejoin="round"/>')
CAP = (f'<g transform="translate(80 20)"><path d="M-40 2 L0 -16 L40 2 L0 18 Z" fill="{INK}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
       f'<path d="M-22 8 L-22 20 Q0 30 22 20 L22 8 L0 18 Z" fill="#2e3d58"/>'
       f'<path d="M34 4 L34 26" stroke="{GOLD}" stroke-width="4"/><circle cx="34" cy="29" r="5" fill="{GOLD}"/></g>')
BOOK = ('<g transform="translate(80 126)"><path d="M-36 -18 Q-18 -24 0 -16 Q18 -24 36 -18 L36 12 Q18 6 0 14 Q-18 6 -36 12 Z" '
        'fill="#fff" stroke="#1290cf" stroke-width="4" stroke-linejoin="round"/>'
        '<path d="M0 -16 L0 14" stroke="#1290cf" stroke-width="3.5"/>'
        '<path d="M-28 -10 L-8 -12 M-28 -2 L-8 -4 M8 -12 L28 -10 M8 -4 L28 -2" stroke="#9fd8ff" stroke-width="3" stroke-linecap="round"/></g>')
PAPER100 = (f'<g transform="translate(80 136) rotate(-5)"><rect x="-40" y="-20" width="80" height="38" rx="6" fill="#fff" stroke="#d5dce6" stroke-width="3"/>'
            f'<text x="0" y="10" text-anchor="middle" font-size="27" fill="{CORAL}" {FONTATTR}>100</text>'
            f'<path d="M-24 13 Q0 19 24 13" stroke="{CORAL}" stroke-width="3" fill="none" stroke-linecap="round"/></g>')
CLOCK = (f'<g transform="translate(130 34)"><circle r="20" fill="#fff" stroke="#ff9600" stroke-width="5"/>'
         f'<path d="M0 -11 L0 0 L8 5" stroke="{INK}" stroke-width="4" stroke-linecap="round" fill="none"/>'
         f'<path d="M-18 -18 L-24 -24 M18 -18 L24 -24" stroke="#ff9600" stroke-width="5" stroke-linecap="round"/></g>'
         f'<path d="M100 18 l-6 -6 M98 28 l-9 -1" stroke="#ff9600" stroke-width="3.5" stroke-linecap="round"/>')
FLAME = ('<g transform="translate(134 40) scale(1.7)"><path d="M0 -14 C2 -8 9 -5 9 3 C9 9 5 13 0 13 C-5 13 -9 9 -9 3 C-9 -1 -7 -3 -5 -5 '
         'C-5 -2 -4 0 -2 0 C-3 -5 -2 -10 0 -14 Z" fill="#ff9600" stroke="#ff7a00" stroke-width="1.5" stroke-linejoin="round"/>'
         '<path d="M0 0 C2 2 4 4 4 7 C4 10 2 11 0 11 C-2 11 -4 10 -4 7 C-4 4 -2 2 0 0 Z" fill="#ffe08a"/></g>')
CHECK = (f'<g transform="translate(134 38)"><circle r="18" fill="{MINT}" stroke="#0d9f7a" stroke-width="3"/>'
         '<path d="M-8 0 L-2 7 L9 -7" stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>')
THUMB = (f'<g transform="translate(150 70) rotate(-10)"><rect x="-11" y="-6" width="22" height="20" rx="6" fill="{BODY}" stroke="{LIP}" stroke-width="3.5"/>'
         f'<rect x="-6" y="-22" width="10" height="20" rx="5" fill="{BODY}" stroke="{LIP}" stroke-width="3.5"/></g>')


def sparkles(*pts):
    return "".join(sparkle(x, y, s, c) for x, y, s, c in pts)


def confetti():
    bits = [(18, 30, "#ffc800", 20), (140, 22, CORAL, -30), (30, 70, MINT, 45), (150, 60, "#ce82ff", 15), (60, 6, "#1cb0f6", -10)]
    return "".join(f'<rect x="{x}" y="{y}" width="9" height="5" rx="2" fill="{c}" transform="rotate({r} {x} {y})"/>' for x, y, c, r in bits)


def hearts_float():
    return heart(132, 40, 0.9) + heart(24, 52, 0.6, "#ff86c8") + heart(146, 70, 0.5, "#ff86c8")


STICKER_ART = {
    # chào hỏi
    "hello": lambda: prismo("normal", "big", "wave_r", prop_front=sparkles((22, 34, 0.9, GOLD))),
    "thanks": lambda: prismo("happy", "cat", "cheek", prop_front=hearts_float()),
    "sticker_ok": lambda: prismo("wink", "smile", "wave_r", prop_front=CHECK.replace("translate(134 38)", "translate(26 40)") + THUMB),
    "great": lambda: prismo("stars", "big", "cheer", prop_front=sparkles((80, 4, 1.1, GOLD), (16, 92, 0.8, MINT), (146, 98, 0.8, CORAL))),
    "good_night": lambda: prismo("sleepy", "small", None, prop_back=MOON, hat=NIGHTCAP, prop_front=ZZZ),
    "bye": lambda: prismo("wink", "big", "wave_l", prop_front=sparkles((142, 34, 0.8, MINT))),
    # cảm xúc
    "sticker_love": lambda: prismo("hearts", "big", "cheek", prop_front=hearts_float()),
    "sticker_sad": lambda: prismo("teary", "wobbly", "rest", prop_front=CLOUD),
    "wow": lambda: prismo("wide", "o", "cheer", prop_front=EXCLAIM),
    "huh": lambda: prismo("side", "flat", "point", prop_front=QUESTION),
    "sorry": lambda: prismo("puppy", "wobbly", "hold", prop_front=SWEAT),
    "haha": lambda: prismo("laugh", "big", "clap", prop_front=TEAR + TEAR.replace("134", "26").replace("142", "34").replace("126", "18")),
    # học cùng nhau
    "fighting": lambda: prismo("determined", "grin", "fist", hat=HEADBAND, prop_front=sparkles((22, 40, 0.9, GOLD))),
    "study_yet": lambda: prismo("side", "smile", "hold", prop_front=BOOK + QUESTION.split("</text>")[0] + "</text>"),
    "smart": lambda: prismo("happy", "big", "clap", hat=CAP, prop_front=sparkles((20, 52, 0.9, GOLD), (142, 60, 0.8, MINT))),
    "score100": lambda: prismo("stars", "big", "hold_wide", prop_front=PAPER100 + confetti()),
    "keep_fire": lambda: prismo("determined", "big", "fist", prop_front=FLAME.replace("translate(134 40)", "translate(26 44)")),
    "review_time": lambda: prismo("wide", "o", "point", prop_front=CLOCK),
    # thế giới
    "en_hello": lambda: prismo("normal", "big", "wave_r", prop_front=bubble("Hi!", 40, 18)),
    "zh_hello": lambda: prismo("happy", "smile", "wave_r", prop_front=bubble("你好", 40, 18)),
    "zh_jiayou": lambda: prismo("determined", "grin", "cheer", hat=HEADBAND),
    "en_thanks": lambda: prismo("happy", "cat", "cheek", prop_front=heart(132, 38, 0.9) + heart(28, 44, 0.7)),
    "en_goodjob": lambda: prismo("wink", "big", None, prop_front=THUMB.replace("translate(150 70)", "translate(142 70)") + CHECK.replace("translate(134 38)", "translate(26 40)")),
    "en_bye": lambda: prismo("happy", "big", "wave_l", prop_front=sparkles((142, 30, 0.9, GOLD))),
}


def caption(text, color):
    size = min(25, 146 / (0.6 * max(len(text), 4)))
    return (f'<text x="80" y="164" text-anchor="middle" font-size="{size:.1f}" fill="{color}" stroke="#fff" stroke-width="7" '
            f'paint-order="stroke" stroke-linejoin="round" transform="rotate(-4 80 156)" {FONTATTR}>{text}</text>')


DIECUT = ('<filter id="cut" x="-10%" y="-10%" width="120%" height="120%">'
          '<feMorphology in="SourceAlpha" operator="dilate" radius="{r}" result="d"/>'
          '<feFlood flood-color="#fff"/><feComposite in2="d" operator="in" result="w"/>'
          '<feGaussianBlur in="d" stdDeviation="2.5" result="b"/><feOffset in="b" dy="3" result="o"/>'
          '<feFlood flood-color="#0b2b4a" flood-opacity="0.28"/><feComposite in2="o" operator="in" result="s"/>'
          '<feMerge><feMergeNode in="s"/><feMergeNode in="w"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')


def sticker_svg(code, text, color):
    art = STICKER_ART[code]()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-14 -14 188 196"><defs>{DIECUT.format(r=5)}</defs>'
            f'<g filter="url(#cut)"><g transform="translate(14 6) scale(0.82)">{art}</g>{caption(text, color)}</g></svg>')


# ---------------------------------------------------------------- badge medals (120 grid)

TIER = [("#f3a865", "#c46f2c"), ("#e2e8f0", "#9aa8bc"), ("#ffd23f", "#d99a00"), ("#5eead4", "#0d9f7a"),
        ("#7cc8ff", "#2f86d6"), ("#d6a8ff", "#9a5fe0"), ("prism", "#6d4aff")]

G = {  # white glyphs in a 40 × 40 box centred on 0 0
    "book": '<path d="M-17 -12 Q-8 -16 0 -11 Q8 -16 17 -12 L17 13 Q8 9 0 14 Q-8 9 -17 13 Z" fill="#fff"/><path d="M0 -11 L0 14" stroke="{c}" stroke-width="2.5"/>',
    "cap": '<path d="M-19 -4 L0 -13 L19 -4 L0 5 Z" fill="#fff"/><path d="M-11 0 L-11 9 Q0 15 11 9 L11 0 L0 5 Z" fill="#fff"/><path d="M16 -3 L16 9" stroke="#fff" stroke-width="2.5"/><circle cx="16" cy="11" r="3" fill="#fff"/>',
    "flame": '<path d="M0 -17 C3 -9 12 -6 12 4 C12 12 6 17 0 17 C-6 17 -12 12 -12 4 C-12 -1 -9 -4 -7 -6 C-7 -2 -5 0 -3 0 C-4 -7 -3 -12 0 -17 Z" fill="#fff"/><path d="M0 2 C3 5 5 7 5 10 C5 13 3 14 0 14 C-3 14 -5 13 -5 10 C-5 7 -3 5 0 2 Z" fill="{c}"/>',
    "star": '<path d="M0 -18 L5.3 -6.5 L17.6 -5.6 L8.2 2.6 L11 14.6 L0 8.2 L-11 14.6 L-8.2 2.6 L-17.6 -5.6 L-5.3 -6.5 Z" fill="#fff" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>',
    "camera": '<rect x="-17" y="-9" width="34" height="23" rx="6" fill="#fff"/><rect x="-7" y="-15" width="14" height="8" rx="3" fill="#fff"/><circle cx="0" cy="2" r="7.5" fill="{c}"/><circle cx="0" cy="2" r="4" fill="#fff"/>',
    "image": '<rect x="-17" y="-14" width="34" height="28" rx="6" fill="#fff"/><path d="M-12 9 L-3 -1 L3 5 L7 1 L12 9 Z" fill="{c}"/><circle cx="7" cy="-6" r="3.5" fill="{c}"/>',
    "heart": '<path d="M0 15 C-22 1 -15 -18 0 -7 C15 -18 22 1 0 15 Z" fill="#fff" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>',
    "friends": '<circle cx="-8" cy="-6" r="7" fill="#fff"/><circle cx="9" cy="-6" r="7" fill="#fff"/><path d="M-20 15 Q-8 -1 0 11 Q8 -1 20 15 Z" fill="#fff"/>',
    "flag": '<path d="M-11 -16 L-11 17" stroke="#fff" stroke-width="4" stroke-linecap="round"/><path d="M-9 -15 L15 -8 L-9 2 Z" fill="#fff" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>',
    "bolt": '<path d="M4 -18 L-12 3 L-1 3 L-5 18 L12 -4 L1 -4 Z" fill="#fff" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>',
    "target": '<circle r="16" fill="#fff"/><circle r="10.5" fill="{c}"/><circle r="5.5" fill="#fff"/><circle r="2" fill="{c}"/>',
    "sun": '<circle r="8" fill="#fff"/><g stroke="#fff" stroke-width="3.5" stroke-linecap="round"><path d="M0 -17 L0 -13 M0 13 L0 17 M-17 0 L-13 0 M13 0 L17 0 M-12 -12 L-9 -9 M9 9 L12 12 M-12 12 L-9 9 M9 -9 L12 -12"/></g>',
    "moon": '<path d="M-2 -16 A16 16 0 1 0 15 7 A12 12 0 1 1 -2 -16 Z" fill="#fff"/><path d="M10 -12 l1.5 3.5 3.5 1.5 -3.5 1.5 -1.5 3.5 -1.5 -3.5 -3.5 -1.5 3.5 -1.5 Z" fill="#fff"/>',
    "trophy": '<path d="M-11 -15 L11 -15 L10 0 Q0 9 -10 0 Z" fill="#fff"/><path d="M-11 -11 Q-20 -11 -17 -3 Q-15 1 -9 1 M11 -11 Q20 -11 17 -3 Q15 1 9 1" stroke="#fff" stroke-width="3" fill="none"/><path d="M-3 4 L3 4 L4 11 L-4 11 Z M-9 11 L9 11 L9 16 L-9 16 Z" fill="#fff"/>',
    "gamepad": '<path d="M-12 -9 L12 -9 Q20 -9 21 1 L22 9 Q22 15 16 14 L10 7 L-10 7 L-16 14 Q-22 15 -22 9 L-21 1 Q-20 -9 -12 -9 Z" fill="#fff"/><path d="M-12 -4 L-12 4 M-16 0 L-8 0" stroke="{c}" stroke-width="3" stroke-linecap="round"/><circle cx="10" cy="-3" r="2.6" fill="{c}"/><circle cx="15" cy="2" r="2.6" fill="{c}"/>',
    "crown": '<path d="M-18 -8 L-9 2 L0 -15 L9 2 L18 -8 L15 12 L-15 12 Z" fill="#fff" stroke="#fff" stroke-width="2.5" stroke-linejoin="round"/><circle cx="0" cy="5" r="3" fill="{c}"/><rect x="-15" y="13" width="30" height="4" rx="2" fill="#fff"/>',
    "prism": '<path d="M0 -16 L15 13 L-15 13 Z" fill="#fff" stroke="#fff" stroke-width="4" stroke-linejoin="round"/><path d="M0 -12 L0 12 L-11 12 Z" fill="{c}" opacity="0.35"/>',
}


def medal(glyph, colour, tier, label=""):
    face, lip = TIER[min(tier, len(TIER) - 1)]
    defs = ""
    if face == "prism":
        defs = ('<defs><linearGradient id="pr" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffb020"/>'
                '<stop offset="0.35" stop-color="#ff6b81"/><stop offset="0.65" stop-color="#ce82ff"/><stop offset="1" stop-color="#1cb0f6"/></linearGradient></defs>')
        face = "url(#pr)"
    dark = shade(colour, 0.78)
    ribbon = (f'<path d="M40 74 L30 112 L42 104 L50 114 L58 80 Z" fill="{dark}"/>'
              f'<path d="M80 74 L90 112 L78 104 L70 114 L62 80 Z" fill="{dark}"/>'
              f'<path d="M40 74 L34 98 L58 80 Z M80 74 L86 98 L62 80 Z" fill="{colour}"/>')
    ring = (f'<circle cx="60" cy="56" r="42" fill="{lip}"/><circle cx="60" cy="51" r="42" fill="{face}"/>'
            f'<circle cx="60" cy="53" r="32" fill="{dark}"/><circle cx="60" cy="51" r="32" fill="{colour}"/>'
            f'<path d="M36 34 A32 32 0 0 1 72 21" stroke="#fff" stroke-width="5" stroke-linecap="round" fill="none" opacity="0.35"/>')
    g = G[glyph].replace("{c}", colour)
    tag = ""
    if label:
        w = max(30, len(label) * 9.5 + 14)
        tag = (f'<rect x="{60 - w / 2}" y="78" width="{w}" height="22" rx="11" fill="{lip}"/>'
               f'<rect x="{60 - w / 2}" y="75" width="{w}" height="22" rx="11" fill="#fff"/>'
               f'<text x="60" y="91.5" text-anchor="middle" font-size="15" fill="{dark}" {FONTATTR}>{label}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">{defs}{ribbon}{ring}'
            f'<g transform="translate(60 51) scale(1.12)">{g}</g>{tag}</svg>')


def shade(hex_colour, k):
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % (int(r * k), int(g * k), int(b * k))


def short(n):
    return f"{n // 1000}K" if n >= 1000 and n % 1000 == 0 else str(n)


# ---------------------------------------------------------------- shop items (120 grid)

ITEM_ART = {
    "streak_repair": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">'
        '<g transform="translate(60 62) scale(4.2)"><path d="M0 -14 C2 -8 9 -5 9 3 C9 9 5 13 0 13 C-5 13 -9 9 -9 3 C-9 -1 -7 -3 -5 -5 '
        'C-5 -2 -4 0 -2 0 C-3 -5 -2 -10 0 -14 Z" fill="#ff9600" stroke="#e07800" stroke-width="1.2" stroke-linejoin="round"/>'
        '<path d="M0 0 C2 2 4 4 4 7 C4 10 2 11 0 11 C-2 11 -4 10 -4 7 C-4 4 -2 2 0 0 Z" fill="#ffe08a"/></g>'
        '<g transform="translate(60 66) rotate(-35)"><rect x="-34" y="-10" width="68" height="20" rx="10" fill="#ffd6b0" stroke="#e8a971" stroke-width="3"/>'
        '<rect x="-12" y="-10" width="24" height="20" fill="#ffe8d1"/><g fill="#e8a971"><circle cx="-5" cy="-4" r="1.8"/><circle cx="5" cy="-4" r="1.8"/>'
        '<circle cx="-5" cy="4" r="1.8"/><circle cx="5" cy="4" r="1.8"/></g></g></svg>'),
    "gem_exchange": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120"><defs><linearGradient id="s" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#34e3b5"/><stop offset="1" stop-color="#0891b2"/></linearGradient></defs>'
        '<circle cx="36" cy="44" r="26" fill="#0e7490"/><circle cx="36" cy="40" r="26" fill="url(#s)"/>'
        '<g fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity="0.9"><path d="M22 38 a7 7 0 0 1 14 0"/><path d="M36 38 a7 7 0 0 1 14 0"/><path d="M29 49 a7 7 0 0 1 14 0"/></g>'
        '<path d="M50 74 L66 74 L66 66 L80 80 L66 94 L66 86 L50 86 Z" fill="#ff9600" stroke="#e07800" stroke-width="3" stroke-linejoin="round"/>'
        '<g transform="translate(90 70) scale(1.5)"><path d="M0 -18 L17 -5 L0 20 L-17 -5 Z" fill="#6d4aff"/><path d="M0 -18 L17 -5 L0 -1 L-17 -5 Z" fill="#b8a8ff"/>'
        '<path d="M-17 -5 L0 -1 L0 20 Z" fill="#8f74ff"/><path d="M0 -1 L17 -5 L0 20 Z" fill="#06b6d4" opacity="0.55"/></g></svg>'),
}


# ---------------------------------------------------------------- render

def browser():
    for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe", shutil.which("chromium") or "", shutil.which("google-chrome") or ""):
        if p and os.path.exists(p):
            return p
    raise SystemExit("needs Edge or Chrome to render the PNGs")


def render(svg_text, rel, w, h=None):
    """One PNG per output root (web, app)."""
    h = h or w
    tmp = tempfile.mkdtemp()
    page = os.path.join(tmp, "r.html")
    open(page, "w", encoding="utf-8").write(
        f'<!doctype html><meta charset="utf-8"><style>@font-face{{font-family:LP;src:url("file:///{FONT}")}}'
        f'html,body{{margin:0;background:transparent}}svg{{display:block;width:{w}px;height:{h}px}}</style>{svg_text}')
    first = OUT[0] + rel
    os.makedirs(os.path.dirname(first), exist_ok=True)
    subprocess.run([browser(), "--headless=new", f"--user-data-dir={tmp}/p", "--hide-scrollbars", "--allow-file-access-from-files",
                    "--default-background-color=00000000", f"--window-size={w},{h}", f"--screenshot={os.path.abspath(first)}",
                    "file:///" + page.replace(os.sep, "/")], check=True, capture_output=True)
    for root in OUT[1:]:
        os.makedirs(os.path.dirname(root + rel), exist_ok=True)
        shutil.copyfile(first, root + rel)
    shutil.rmtree(tmp, ignore_errors=True)
    return first


def main():
    made = []
    for pack in catalog.STICKER_PACKS:
        for code, text in pack["stickers"]:
            made.append(render(sticker_svg(code, text, pack["colour"]), f"stickers/{code}.png", 282, 294))
    by_condition = {}
    for b in catalog.BADGES:
        by_condition.setdefault(b["condition"], []).append(b)
    for cond, rows in by_condition.items():
        glyph, colour = catalog.CONDITION_ART[cond]
        for tier, b in enumerate(sorted(rows, key=lambda r: r["threshold"])):
            label = "" if b.get("no_label") else short(b["threshold"])
            made.append(render(medal(glyph, colour, b.get("tier", tier), label), f"badges/{b['code']}.png", 240))
    for code, art in ITEM_ART.items():
        made.append(render(art, f"items/{code}.png", 240))
    print(f"{len(made)} PNG -> {', '.join(OUT)}")
    if len(sys.argv) > 1:  # contact sheet to check by eye
        cells = "".join(f'<img src="file:///{p}" style="width:120px;margin:6px;background:#eef3f8">' for p in made)
        svg = f'<div style="width:1100px;display:flex;flex-wrap:wrap;background:#fff">{cells}</div>'
        tmp = tempfile.mkdtemp()
        page = os.path.join(tmp, "s.html")
        open(page, "w", encoding="utf-8").write(f"<!doctype html><body style='margin:0'>{svg}</body>")
        rows = (len(made) + 7) // 8
        subprocess.run([browser(), "--headless=new", f"--user-data-dir={tmp}/p", "--allow-file-access-from-files", "--hide-scrollbars",
                        f"--window-size=1100,{rows * 135 + 20}", f"--screenshot={os.path.abspath(sys.argv[1])}",
                        "file:///" + page.replace(os.sep, "/")], check=True, capture_output=True)


if __name__ == "__main__":
    main()
