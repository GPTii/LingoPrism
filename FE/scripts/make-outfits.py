"""Prismo's wardrobe, drawn in code (no third-party art): one SVG layer per piece in catalog.OUTFITS.

Every layer uses the same frame, viewBox "-10 -24 180 180", which is Prismo's own 160 × 150 grid
(FE/src/components/brand/Brand.tsx, MOBILE/lib/app/core/widgets/prismo.dart) with room above for hats and on the
left for what Prismo holds. Stacked in slot order (background, Prismo, neck, hand, glasses, hat) they dress it.

Landmarks on the grid: the head's tip at (80, 7); the eyes at (64, 88) and (96, 88); the mouth from x 70 to 90 at
y 104–114; the body's left edge passes x ≈ 24 at y 100 and its bottom is y ≈ 131. Light beams leave on the right.

    python FE/scripts/make-outfits.py [sheet.png]   # writes FE/public/outfits and MOBILE/assets/outfits
"""
import importlib.util
import math
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")).replace(os.sep, "/") + "/"
OUT = [ROOT + "FE/public/outfits/", ROOT + "MOBILE/assets/outfits/"]

spec = importlib.util.spec_from_file_location("catalog", ROOT + "BE/apps/gamification/catalog.py")
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)

INK = "#15233b"
VIEW = "-10 -24 180 180"


def svg(body: str, defs: str = "") -> str:
    d = f"<defs>{defs}</defs>" if defs else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VIEW}" width="180" height="180">{d}{body}</svg>'


def lin(id_, *stops, x1=0, y1=0, x2=0, y2=1):
    s = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<linearGradient id="{id_}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{s}</linearGradient>'


def star_path(x, y, r, inner=0.45, n=5, rot=0):
    pts = []
    for i in range(n * 2):
        a = math.radians(rot - 90 + i * 180 / n)
        rr = r if i % 2 == 0 else r * inner
        pts.append(f"{x + rr * math.cos(a):.1f} {y + rr * math.sin(a):.1f}")
    return "M" + " L".join(pts) + " Z"


def flower(x, y, r, petal, centre, n=5, rot=0):
    out = ""
    for i in range(n):
        a = math.radians(rot + i * 360 / n)
        out += f'<circle cx="{x + r * math.cos(a):.1f}" cy="{y + r * math.sin(a):.1f}" r="{r * 0.95:.1f}" fill="{petal}"/>'
    return out + f'<circle cx="{x}" cy="{y}" r="{r * 0.7:.1f}" fill="{centre}"/>'


def heart_path(x, y, s):
    return (f"M{x} {y + 9 * s} C{x - 17 * s} {y - 3 * s} {x - 11 * s} {y - 17 * s} {x} {y - 7 * s} "
            f"C{x + 11 * s} {y - 17 * s} {x + 17 * s} {y - 3 * s} {x} {y + 9 * s} Z")


# Prismo holds things in a small blue paw at its left side
def paw(x=22, y=110):
    return (f'<ellipse cx="{x}" cy="{y}" rx="8" ry="6.5" fill="#1689d8"/>'
            f'<ellipse cx="{x - 1}" cy="{y - 2}" rx="4" ry="2.4" fill="#fff" opacity="0.35"/>')


ART = {}

# ---------------------------------------------------------------- hats (sit over the tip at (80, 7))

ART["hat_cap"] = svg(
    '<path d="M100 31 Q128 27 138 37 Q124 43 100 39 Z" fill="#c2410c"/>'
    '<path d="M52 37 Q50 3 80 1 Q110 3 108 37 Q80 31 52 37 Z" fill="url(#c)"/>'
    '<path d="M80 2 L80 34 M64 6 Q60 20 62 35 M96 6 Q100 20 98 35" stroke="#c2410c" stroke-width="2" fill="none" opacity="0.55"/>'
    '<path d="M52 37 Q80 30 108 37 L108 41 Q80 35 52 41 Z" fill="#9a3412"/>'
    '<circle cx="80" cy="2" r="4" fill="#9a3412"/>'
    '<path d="M64 12 Q70 6 78 6" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round" opacity="0.45"/>',
    lin("c", (0, "#ff8a3d"), (1, "#f2541b")))

ART["hat_beanie"] = svg(
    '<path d="M51 36 Q49 -2 80 -4 Q111 -2 109 36 Z" fill="url(#b)"/>'
    '<path d="M60 4 L60 32 M70 -1 L70 32 M80 -3 L80 32 M90 -1 L90 32 M100 4 L100 32" stroke="#6d28d9" stroke-width="2.4" opacity="0.35"/>'
    '<rect x="47" y="27" width="66" height="15" rx="7.5" fill="#c4b5fd"/>'
    '<path d="M53 31 L107 31 M53 37 L107 37" stroke="#8b5cf6" stroke-width="2" opacity="0.5"/>'
    '<circle cx="80" cy="-9" r="10" fill="#fff"/><circle cx="76" cy="-12" r="3.5" fill="#ede9fe"/>',
    lin("b", (0, "#a78bfa"), (1, "#7c3aed")))

ART["hat_party"] = svg(
    '<path d="M60 36 L80 -20 L100 36 Q80 42 60 36 Z" fill="url(#p)"/>'
    '<path d="M67 18 L88 10 M63 30 L94 18 M74 0 L84 -4" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity="0.8"/>'
    '<circle cx="74" cy="22" r="2.6" fill="#ffe066"/><circle cx="88" cy="28" r="2.6" fill="#10c79a"/><circle cx="82" cy="4" r="2.4" fill="#ffe066"/>'
    '<path d="M60 36 Q80 42 100 36" stroke="#ffb020" stroke-width="4" fill="none" stroke-linecap="round"/>'
    + flower(80, -22, 4.2, "#ffd43b", "#ff8a3d", n=6),
    lin("p", (0, "#ff7eb3"), (1, "#e8456f"), x2=1, y2=0))

ART["hat_non_la"] = svg(
    '<path d="M24 42 L80 -8 L136 42 Q80 54 24 42 Z" fill="url(#n)"/>'
    + "".join(f'<path d="M80 -6 L{x} {44 + abs(x - 80) * -0.06 + 3}" stroke="#c9a24a" stroke-width="1.4" opacity="0.7"/>'
              for x in (36, 50, 64, 80, 96, 110, 124))
    + '<path d="M24 42 Q80 54 136 42" stroke="#b38a2e" stroke-width="3" fill="none" stroke-linecap="round"/>'
    '<path d="M52 22 Q80 30 108 22" stroke="#d6b25c" stroke-width="1.6" fill="none" opacity="0.8"/>'
    '<path d="M64 8 Q80 13 96 8" stroke="#d6b25c" stroke-width="1.4" fill="none" opacity="0.8"/>'
    '<path d="M80 -8 L60 26" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity="0.35"/>',
    lin("n", (0, "#fbe7a8"), (1, "#e9c46a"), x1=0, y1=0, x2=1, y2=1))

_ring = ""
for i, (x, y, c) in enumerate([(52, 30, "#ff8fab"), (63, 22, "#ffd43b"), (76, 18, "#ff6b81"), (90, 19, "#a78bfa"),
                               (103, 24, "#ffd43b"), (111, 32, "#ff8fab")]):
    _ring += f'<ellipse cx="{x - 3}" cy="{y + 6}" rx="7" ry="3.5" fill="#34c38f" transform="rotate(-25 {x - 3} {y + 6})"/>'
    _ring += flower(x, y, 4.6, c, "#fff3bf", rot=i * 17)
ART["hat_flowers"] = svg('<path d="M48 34 Q80 14 114 34" stroke="#2f9e6e" stroke-width="4" fill="none" stroke-linecap="round"/>' + _ring)

ART["hat_beret"] = svg(
    '<path d="M47 30 Q40 6 74 2 Q116 -2 118 20 Q118 34 96 34 L64 35 Q50 36 47 30 Z" fill="url(#r)"/>'
    '<path d="M52 33 Q80 28 112 31 L112 37 Q80 34 52 39 Z" fill="#9f1239"/>'
    '<path d="M80 2 Q81 -6 86 -8" stroke="#9f1239" stroke-width="4" fill="none" stroke-linecap="round"/>'
    '<path d="M58 14 Q70 6 86 6" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round" opacity="0.35"/>',
    lin("r", (0, "#fb7185"), (1, "#e11d48")))

ART["hat_grad"] = svg(
    '<path d="M58 36 L58 18 Q80 26 102 18 L102 36 Q80 42 58 36 Z" fill="#2b3a5c"/>'
    '<path d="M80 -2 L128 13 L80 28 L32 13 Z" fill="#1b2741"/>'
    '<path d="M80 -2 L128 13 L80 18 L32 13 Z" fill="#33466e"/>'
    '<circle cx="80" cy="12" r="3.6" fill="#ffc94a"/>'
    '<path d="M80 12 Q104 12 118 16 L118 34" stroke="#ffc94a" stroke-width="2.6" fill="none" stroke-linecap="round"/>'
    '<path d="M114 32 L122 32 L124 46 L112 46 Z" fill="#ffc94a"/>'
    '<path d="M115 38 L115 46 M118 38 L118 46 M121 38 L121 46" stroke="#e0a21a" stroke-width="1.2"/>')

ART["hat_nightcap"] = svg(
    '<path d="M52 36 Q48 4 82 -4 Q114 -10 128 16 Q132 28 124 34 Q118 18 106 14 Q112 28 108 36 Z" fill="url(#m)"/>'
    + "".join(f'<path d="{star_path(x, y, r, rot=r * 7)}" fill="#ffe08a"/>'
              for x, y, r in [(70, 14, 4.5), (92, 6, 3.8), (110, 4, 3.2), (86, 24, 3)])
    + '<rect x="47" y="28" width="66" height="13" rx="6.5" fill="#f1f5ff"/>'
    '<circle cx="124" cy="37" r="8" fill="#f1f5ff"/>',
    lin("m", (0, "#4f7cf7"), (1, "#3049b8")))

ART["hat_flame"] = svg(
    '<path d="M52 38 L52 18 Q58 24 62 14 Q64 2 72 -6 Q72 8 80 -16 Q88 8 88 -6 Q96 2 98 14 Q102 24 108 18 L108 38 Z" fill="url(#f)"/>'
    '<path d="M62 38 Q62 24 68 18 Q70 26 74 20 Q76 8 80 2 Q84 8 86 20 Q90 26 92 18 Q98 24 98 38 Z" fill="url(#g)"/>'
    '<rect x="50" y="29" width="60" height="11" rx="4" fill="#d9480f"/>'
    '<circle cx="66" cy="34.5" r="2.6" fill="#ffe08a"/><circle cx="80" cy="34.5" r="3" fill="#fff"/><circle cx="94" cy="34.5" r="2.6" fill="#ffe08a"/>',
    lin("f", (0, "#ffd43b"), (0.5, "#ff922b"), (1, "#f03e3e")) + lin("g", (0, "#fff3bf"), (1, "#ffc078")))

ART["hat_crown"] = svg(
    '<path d="M52 38 L50 6 L66 20 L80 -6 L94 20 L110 6 L108 38 Q80 43 52 38 Z" fill="url(#k)" stroke="#d99a00" stroke-width="2" stroke-linejoin="round"/>'
    '<path d="M53 30 Q80 35 107 30" stroke="#d99a00" stroke-width="2" fill="none"/>'
    '<circle cx="50" cy="6" r="4.5" fill="#ffe066" stroke="#d99a00" stroke-width="1.6"/>'
    '<circle cx="80" cy="-6" r="5" fill="#ffe066" stroke="#d99a00" stroke-width="1.6"/>'
    '<circle cx="110" cy="6" r="4.5" fill="#ffe066" stroke="#d99a00" stroke-width="1.6"/>'
    '<path d="M80 14 L86 22 L80 30 L74 22 Z" fill="#ff4b6e"/>'
    '<circle cx="64" cy="27" r="3.6" fill="#1899f0"/><circle cx="96" cy="27" r="3.6" fill="#10c79a"/>'
    '<path d="M60 14 L62 26" stroke="#fff" stroke-width="2.4" stroke-linecap="round" opacity="0.6"/>',
    lin("k", (0, "#fff08a"), (1, "#ffc21a")))

ART["hat_witch"] = svg(
    '<ellipse cx="80" cy="36" rx="48" ry="9" fill="#3b1f5c"/>'
    '<path d="M58 36 Q64 14 74 -6 Q84 -26 108 -22 Q92 -14 94 4 L104 36 Z" fill="url(#w)"/>'
    '<path d="M60 28 Q81 34 102 28 L104 36 Q80 41 58 36 Z" fill="#ff922b"/>'
    '<rect x="76" y="28" width="10" height="10" rx="1.5" fill="none" stroke="#ffe066" stroke-width="2.4"/>'
    + f'<path d="{star_path(88, 6, 4.2)}" fill="#ffe066"/>'
    '<path d="M70 4 Q74 -6 80 -12" stroke="#fff" stroke-width="2.4" fill="none" stroke-linecap="round" opacity="0.3"/>',
    lin("w", (0, "#7c4dbd"), (1, "#4c2a85")))

ART["hat_santa"] = svg(
    '<path d="M52 36 Q54 0 86 -8 Q112 -12 124 14 L114 20 Q106 4 96 8 Q104 22 108 36 Z" fill="url(#s)"/>'
    '<path d="M64 10 Q74 0 88 -2" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round" opacity="0.35"/>'
    '<rect x="47" y="27" width="66" height="14" rx="7" fill="#fff"/>'
    '<circle cx="120" cy="20" r="8.5" fill="#fff"/>'
    '<path d="M53 34 Q80 30 107 34" stroke="#e9ecef" stroke-width="2" fill="none"/>',
    lin("s", (0, "#ff5a5f"), (1, "#d62839")))

# ---------------------------------------------------------------- glasses (eyes at (64, 88) and (96, 88))

ART["glasses_round"] = svg(
    '<circle cx="64" cy="88" r="13" fill="#fff" opacity="0.18"/><circle cx="96" cy="88" r="13" fill="#fff" opacity="0.18"/>'
    '<circle cx="64" cy="88" r="13" fill="none" stroke="#5c3d1e" stroke-width="3.4"/>'
    '<circle cx="96" cy="88" r="13" fill="none" stroke="#5c3d1e" stroke-width="3.4"/>'
    '<path d="M77 86 Q80 82 83 86" stroke="#5c3d1e" stroke-width="3" fill="none"/>'
    '<path d="M51 85 L36 82 M109 85 L124 82" stroke="#5c3d1e" stroke-width="3" stroke-linecap="round"/>'
    '<path d="M56 82 Q59 78 64 78" stroke="#fff" stroke-width="2.4" fill="none" stroke-linecap="round" opacity="0.7"/>'
    '<path d="M88 82 Q91 78 96 78" stroke="#fff" stroke-width="2.4" fill="none" stroke-linecap="round" opacity="0.7"/>')

_lens = "M{x0} 79 L{x1} 79 L{x1} 86 Q{x1} 99 {xc} 99 Q{x0} 99 {x0} 86 Z"
ART["glasses_sun"] = svg(
    '<path d="M47 80 L113 80" stroke="#15233b" stroke-width="4" stroke-linecap="round"/>'
    + f'<path d="{_lens.format(x0=48, x1=78, xc=63)}" fill="url(#d)"/>'
    + f'<path d="{_lens.format(x0=82, x1=112, xc=97)}" fill="url(#d)"/>'
    '<path d="M52 92 L60 82 M56 95 L66 83" stroke="#fff" stroke-width="2.2" stroke-linecap="round" opacity="0.45"/>'
    '<path d="M86 92 L94 82 M90 95 L100 83" stroke="#fff" stroke-width="2.2" stroke-linecap="round" opacity="0.45"/>'
    '<path d="M47 81 L34 78 M113 81 L126 78" stroke="#15233b" stroke-width="3" stroke-linecap="round"/>',
    lin("d", (0, "#33415c"), (1, "#0b1220")))

ART["glasses_heart"] = svg(
    f'<path d="{heart_path(64, 89, 1.05)}" fill="#ff6b9a" opacity="0.85" stroke="#e8336f" stroke-width="2.6" stroke-linejoin="round"/>'
    f'<path d="{heart_path(96, 89, 1.05)}" fill="#ff6b9a" opacity="0.85" stroke="#e8336f" stroke-width="2.6" stroke-linejoin="round"/>'
    '<path d="M76 84 Q80 81 84 84" stroke="#e8336f" stroke-width="2.6" fill="none"/>'
    '<path d="M52 84 L36 80 M108 84 L124 80" stroke="#e8336f" stroke-width="2.6" stroke-linecap="round"/>'
    '<ellipse cx="58" cy="81" rx="3.4" ry="2.2" fill="#fff" opacity="0.8"/><ellipse cx="90" cy="81" rx="3.4" ry="2.2" fill="#fff" opacity="0.8"/>')

ART["glasses_star"] = svg(
    f'<path d="{star_path(64, 89, 16, 0.55)}" fill="#ffd43b" opacity="0.9" stroke="#f08c00" stroke-width="2.4" stroke-linejoin="round"/>'
    f'<path d="{star_path(96, 89, 16, 0.55)}" fill="#ffd43b" opacity="0.9" stroke="#f08c00" stroke-width="2.4" stroke-linejoin="round"/>'
    '<circle cx="64" cy="90" r="6.5" fill="#fff" opacity="0.55"/><circle cx="96" cy="90" r="6.5" fill="#fff" opacity="0.55"/>'
    '<path d="M77 87 L83 87" stroke="#f08c00" stroke-width="3" stroke-linecap="round"/>'
    '<path d="M50 86 L36 82 M110 86 L124 82" stroke="#f08c00" stroke-width="2.6" stroke-linecap="round"/>')

_px = '<rect x="44" y="79" width="72" height="5" fill="#0b1220"/>'
for x0 in (48, 84):
    _px += (f'<rect x="{x0}" y="84" width="28" height="5" fill="#0b1220"/>'
            f'<rect x="{x0 + 3}" y="89" width="22" height="5" fill="#0b1220"/>'
            f'<rect x="{x0 + 7}" y="94" width="14" height="4" fill="#0b1220"/>'
            f'<rect x="{x0 + 5}" y="84" width="5" height="5" fill="#fff"/><rect x="{x0 + 10}" y="89" width="5" height="5" fill="#fff"/>')
ART["glasses_pixel"] = svg(_px)

ART["glasses_monocle"] = svg(
    '<circle cx="96" cy="88" r="13" fill="#fff" opacity="0.2"/>'
    '<circle cx="96" cy="88" r="13" fill="none" stroke="#e0a21a" stroke-width="3.6"/>'
    '<circle cx="96" cy="88" r="10.5" fill="none" stroke="#ffe08a" stroke-width="1.2"/>'
    '<path d="M88 82 Q91 78 96 78" stroke="#fff" stroke-width="2.4" fill="none" stroke-linecap="round" opacity="0.75"/>'
    '<path d="M106 96 Q116 108 112 122 Q110 128 116 132" stroke="#e0a21a" stroke-width="2" fill="none" stroke-dasharray="3 2.4"/>')

# ---------------------------------------------------------------- neck (under the mouth, y ≈ 114–130)

ART["neck_bow"] = svg(
    '<path d="M80 121 L62 111 Q56 121 62 131 Z" fill="#ef3e5c"/><path d="M80 121 L98 111 Q104 121 98 131 Z" fill="#ef3e5c"/>'
    '<path d="M66 116 L74 120 M66 126 L74 122 M94 116 L86 120 M94 126 L86 122" stroke="#c81e3f" stroke-width="2" stroke-linecap="round"/>'
    '<rect x="74.5" y="115.5" width="11" height="11" rx="3.5" fill="#c81e3f"/>'
    '<circle cx="64" cy="114" r="2" fill="#fff" opacity="0.6"/>')

ART["neck_tie"] = svg(
    '<path d="M68 112 L80 118 L74 124 Z" fill="#fff"/><path d="M92 112 L80 118 L86 124 Z" fill="#fff"/>'
    '<path d="M75 117 L85 117 L83 124 L77 124 Z" fill="#1d4ed8"/>'
    '<path d="M77 124 L83 124 L88 142 L80 149 L72 142 Z" fill="url(#t)"/>'
    '<path d="M76 130 L84 127 M75 137 L86 133 M76 144 L86 140" stroke="#ffd43b" stroke-width="2.2" stroke-linecap="round"/>',
    lin("t", (0, "#3b82f6"), (1, "#1e40af")))

_pearls = ""
for i in range(13):
    t = i / 12
    x = (1 - t) ** 2 * 40 + 2 * (1 - t) * t * 80 + t * t * 120
    y = (1 - t) ** 2 * 112 + 2 * (1 - t) * t * 134 + t * t * 112
    _pearls += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.3" fill="#fbf7ff" stroke="#d8cde8" stroke-width="0.8"/>'
    _pearls += f'<circle cx="{x - 1:.1f}" cy="{y - 1:.1f}" r="1" fill="#fff"/>'
ART["neck_pearls"] = svg(
    _pearls + '<path d="M80 125 L88 131 L80 142 L72 131 Z" fill="#1899f0"/><path d="M80 125 L88 131 L80 133 L72 131 Z" fill="#a6d8fb"/>')

ART["neck_medal"] = svg(
    '<path d="M64 108 L76 108 L84 122 L76 124 Z" fill="#1899f0"/><path d="M96 108 L84 108 L76 122 L84 124 Z" fill="#ef3e5c"/>'
    '<circle cx="80" cy="129" r="11" fill="url(#g)" stroke="#d99a00" stroke-width="2"/>'
    + f'<path d="{star_path(80, 129, 6.5)}" fill="#fff8d6"/>',
    lin("g", (0, "#fff08a"), (1, "#ffb700")))

ART["neck_bell"] = svg(
    '<path d="M42 112 Q80 128 118 112" stroke="#d62839" stroke-width="6" fill="none" stroke-linecap="round"/>'
    '<ellipse cx="70" cy="119" rx="8" ry="3.6" fill="#2f9e44" transform="rotate(-20 70 119)"/>'
    '<ellipse cx="90" cy="119" rx="8" ry="3.6" fill="#2f9e44" transform="rotate(20 90 119)"/>'
    '<circle cx="80" cy="131" r="10" fill="url(#g)" stroke="#d99a00" stroke-width="1.6"/>'
    '<path d="M71 131 L89 131" stroke="#d99a00" stroke-width="2"/><circle cx="80" cy="136" r="2.4" fill="#8a5a00"/>'
    '<circle cx="77" cy="119" r="2.6" fill="#e03131"/><circle cx="83" cy="119" r="2.6" fill="#e03131"/>',
    lin("g", (0, "#fff08a"), (1, "#f5b400")))

# ---------------------------------------------------------------- held at the left side (paw at (22, 110))

ART["hand_book"] = svg(
    '<g transform="rotate(-12 12 110)">'
    '<rect x="-4" y="92" width="32" height="36" rx="3" fill="#e8456f"/>'
    '<rect x="0" y="94" width="26" height="32" rx="2" fill="#fff"/>'
    '<rect x="-4" y="92" width="8" height="36" rx="2" fill="#c81e5a"/>'
    '<path d="M9 102 L22 102 M9 108 L22 108 M9 114 L18 114" stroke="#a5b4c8" stroke-width="2" stroke-linecap="round"/>'
    '<path d="M20 92 L20 102 L23 99 L26 102 L26 92" fill="#ffd43b"/></g>' + paw(26, 112))

ART["hand_pencil"] = svg(
    '<g transform="rotate(-20 14 108)">'
    '<rect x="8" y="70" width="13" height="50" fill="#ffc21a"/><rect x="8" y="70" width="4.3" height="50" fill="#ffd95a"/>'
    '<rect x="16.7" y="70" width="4.3" height="50" fill="#f0a500"/>'
    '<rect x="8" y="62" width="13" height="9" rx="2" fill="#ff8fab"/><rect x="7" y="69" width="15" height="4" fill="#adb5bd"/>'
    '<path d="M8 120 L21 120 L14.5 136 Z" fill="#f5d3a3"/><path d="M12.3 130.5 L16.7 130.5 L14.5 136 Z" fill="#343a40"/></g>'
    + paw(22, 108))

ART["hand_balloon"] = svg(
    '<path d="M22 110 Q8 92 18 74 Q26 60 12 46" stroke="#868e96" stroke-width="1.6" fill="none"/>'
    '<ellipse cx="10" cy="24" rx="16" ry="20" fill="url(#l)"/>'
    '<path d="M7 44 L13 44 L10 48 Z" fill="#e03131"/>'
    '<ellipse cx="4" cy="16" rx="4" ry="7" fill="#fff" opacity="0.45" transform="rotate(20 4 16)"/>' + paw(22, 110),
    lin("l", (0, "#ff8787"), (1, "#e03131"), x2=0.4))

ART["hand_icecream"] = svg(
    '<path d="M2 98 L26 98 L14 130 Z" fill="#e9b872"/>'
    '<path d="M6 104 L20 118 M12 98 L24 108 M18 98 L8 112 M24 100 L12 124" stroke="#c48a3a" stroke-width="1.4"/>'
    '<circle cx="14" cy="92" r="12" fill="#ff8fb1"/><circle cx="8" cy="83" r="8" fill="#8ce99a"/>'
    '<path d="M3 96 Q8 101 13 97 Q18 102 25 96" stroke="#ff8fb1" stroke-width="5" fill="none" stroke-linecap="round"/>'
    '<circle cx="17" cy="86" r="2" fill="#fff" opacity="0.8"/><circle cx="5" cy="80" r="1.6" fill="#fff" opacity="0.8"/>'
    '<rect x="16" y="73" width="2.6" height="6" rx="1.3" fill="#ff6b6b" transform="rotate(30 17 76)"/>' + paw(24, 112))

ART["hand_flag"] = svg(
    '<rect x="12" y="34" width="4" height="98" rx="2" fill="#868e96"/><circle cx="14" cy="33" r="4" fill="#ffc21a"/>'
    '<path d="M16 38 L48 38 Q44 48 48 58 L16 58 Z" fill="#fff"/>'
    '<path d="M16 38 L48 38 L47 44 L16 44 Z" fill="#ffb020"/><path d="M16 45 L46 45 L46 51 L16 51 Z" fill="#10c79a"/>'
    '<path d="M16 52 L46 52 L48 58 L16 58 Z" fill="#ff6b81"/>'
    '<path d="M20 40 L27 52 L13 52 Z" fill="#1899f0" transform="translate(4 -1)"/>' + paw(18, 110))

ART["hand_camera"] = svg(
    '<path d="M18 96 Q30 80 44 76" stroke="#495057" stroke-width="2.4" fill="none"/>'
    '<rect x="-6" y="96" width="36" height="26" rx="5" fill="#343a40"/>'
    '<rect x="2" y="91" width="12" height="7" rx="2" fill="#495057"/>'
    '<circle cx="12" cy="109" r="9.5" fill="#868e96"/><circle cx="12" cy="109" r="6.5" fill="#1b2741"/>'
    '<circle cx="10" cy="107" r="2.2" fill="#a6d8fb"/>'
    '<rect x="22" y="99" width="5" height="3.5" rx="1" fill="#ffd43b"/>' + paw(28, 114))

ART["hand_trophy"] = svg(
    '<path d="M-1 82 Q-11 82 -9 92 Q-7 100 2 100" stroke="#e0a21a" stroke-width="3.4" fill="none"/>'
    '<path d="M29 82 Q39 82 37 92 Q35 100 26 100" stroke="#e0a21a" stroke-width="3.4" fill="none"/>'
    '<path d="M-2 78 L30 78 L28 96 Q14 108 0 96 Z" fill="url(#g)" stroke="#e0a21a" stroke-width="1.6"/>'
    '<rect x="11" y="103" width="6" height="10" fill="#e0a21a"/><rect x="2" y="112" width="24" height="7" rx="2" fill="#8a5a00"/>'
    + f'<path d="{star_path(14, 89, 6)}" fill="#fff8d6"/>' + paw(26, 116),
    lin("g", (0, "#fff08a"), (1, "#ffb700")))

ART["hand_pumpkin"] = svg(
    '<path d="M2 96 Q14 82 26 96" stroke="#495057" stroke-width="2.4" fill="none"/>'
    '<ellipse cx="14" cy="112" rx="17" ry="14" fill="#ff8c1a"/>'
    '<ellipse cx="14" cy="112" rx="8" ry="14" fill="#ffa94d" opacity="0.7"/>'
    '<path d="M14 98 Q15 94 18 93" stroke="#2f9e44" stroke-width="3" fill="none" stroke-linecap="round"/>'
    '<path d="M5 107 L10 104 L11 109 Z M23 107 L18 104 L17 109 Z" fill="#fff3bf"/>'
    '<path d="M5 116 Q14 124 23 116 L20 116 L18 119 L16 116 L12 116 L10 119 L8 116 Z" fill="#fff3bf"/>' + paw(26, 98))

ART["hand_lixi"] = svg(
    '<g transform="rotate(-10 12 108)">'
    '<rect x="-3" y="88" width="30" height="40" rx="3.5" fill="url(#r)"/>'
    '<path d="M-3 92 Q12 104 27 92" stroke="#ffc94a" stroke-width="2" fill="none"/>'
    '<circle cx="12" cy="111" r="7.5" fill="none" stroke="#ffc94a" stroke-width="2.4"/>'
    + flower(12, 111, 2.2, "#ffc94a", "#e03131") +
    '<path d="M0 124 L24 124" stroke="#ffc94a" stroke-width="1.6" opacity="0.8"/></g>' + paw(26, 112),
    lin("r", (0, "#ff4d4f"), (1, "#c92a2a")))

_mai = ('<path d="M22 110 Q12 86 10 64 Q8 46 -2 32 M10 70 Q20 60 22 48 M8 52 Q0 50 -6 54" stroke="#6b3e1d" '
        'stroke-width="3.2" fill="none" stroke-linecap="round"/>')
for x, y, r in [(-2, 32, 4.6), (22, 48, 4.4), (-6, 54, 4), (10, 64, 4.4), (16, 86, 4), (4, 44, 3.6), (14, 98, 3.4)]:
    _mai += flower(x, y, r, "#ffd43b", "#e8590c", rot=x * 3)
ART["hand_mai"] = svg(_mai + '<circle cx="20" cy="74" r="2.6" fill="#94d82d"/><circle cx="2" cy="40" r="2.2" fill="#94d82d"/>' + paw(22, 110))

# ---------------------------------------------------------------- backgrounds (fill the whole frame)

FRAME = '<rect x="-10" y="-24" width="180" height="180" fill="url(#bg)"/>'


def bg(body="", defs=""):
    return svg(FRAME + body, defs)


def cloud(x, y, s=1.0, o=0.95):
    return (f'<g transform="translate({x} {y}) scale({s})" fill="#fff" opacity="{o}">'
            '<ellipse cx="0" cy="0" rx="16" ry="9"/><ellipse cx="12" cy="-6" rx="11" ry="10"/><ellipse cx="24" cy="1" rx="13" ry="8"/></g>')


ART["bg_sky"] = bg(
    cloud(-6, 4, 1.1) + cloud(112, -6, 0.9) + cloud(118, 48, 0.7, 0.8)
    + '<path d="M-10 136 Q40 118 90 132 Q130 124 170 130 L170 156 L-10 156 Z" fill="#8ce99a"/>'
    '<path d="M-10 144 Q60 132 170 142 L170 156 L-10 156 Z" fill="#51cf66"/>',
    lin("bg", (0, "#74c0fc"), (1, "#d0ebff")))

ART["bg_classroom"] = bg(
    '<rect x="-2" y="-14" width="164" height="76" rx="5" fill="#8a5a2b"/>'
    '<rect x="3" y="-9" width="154" height="66" rx="3" fill="#2f6b4f"/>'
    '<path d="M14 6 L22 -2 L30 6 M17 3 L27 3 M38 -2 L38 10 Q46 10 46 5 Q46 2 38 2 Q45 2 45 -1 Q45 -2 38 -2" stroke="#e9f5ee" '
    'stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/>'
    '<path d="M120 2 Q130 -6 140 2 Q130 10 120 2 Z" stroke="#ffe08a" stroke-width="2" fill="none" opacity="0.85"/>'
    '<path d="M12 30 Q30 22 48 30 T84 30" stroke="#e9f5ee" stroke-width="2" fill="none" opacity="0.6"/>'
    + f'<path d="{star_path(140, 34, 7)}" fill="none" stroke="#ffe08a" stroke-width="1.8" opacity="0.85"/>'
    '<rect x="40" y="57" width="80" height="5" rx="2" fill="#6b3e1d"/><rect x="58" y="54" width="14" height="4" rx="1" fill="#fff"/>'
    '<rect x="-10" y="128" width="180" height="28" fill="#c9915a"/>'
    '<path d="M-10 128 L170 128 M30 128 L30 156 M80 128 L80 156 M130 128 L130 156" stroke="#a87442" stroke-width="2"/>',
    lin("bg", (0, "#fff4dc"), (1, "#ffe8b8")))

_books = ""
_cols = ["#e8456f", "#1899f0", "#ffb020", "#10c79a", "#845ef7", "#ff8a3d", "#20c997"]
for row, y in enumerate((-18, 26, 70)):
    x = -8
    i = row * 3
    _books += f'<rect x="-10" y="{y + 36}" width="180" height="6" fill="#8a5a2b"/>'
    while x < 166:
        w = 8 + (i * 7) % 6
        h = 26 + (i * 5) % 9
        _books += f'<rect x="{x}" y="{y + 36 - h}" width="{w}" height="{h}" rx="1.5" fill="{_cols[i % len(_cols)]}" opacity="0.8"/>'
        x += w + 2
        i += 1
ART["bg_library"] = bg(
    _books + '<rect x="-10" y="118" width="180" height="38" fill="#b07a45"/><rect x="-10" y="118" width="180" height="4" fill="#8a5a2b"/>',
    lin("bg", (0, "#f3dfc1"), (1, "#e8cba0")))

ART["bg_beach"] = bg(
    '<circle cx="128" cy="6" r="16" fill="#ffe066"/><circle cx="128" cy="6" r="22" fill="#ffe066" opacity="0.3"/>'
    + cloud(4, 2, 0.8)
    + '<rect x="-10" y="64" width="180" height="50" fill="url(#sea)"/>'
    '<path d="M-10 74 Q5 70 20 74 T50 74 T80 74 T110 74 T140 74 T170 74" stroke="#fff" stroke-width="2" fill="none" opacity="0.6"/>'
    '<path d="M-10 92 Q5 88 20 92 T50 92 T80 92 T110 92 T140 92 T170 92" stroke="#fff" stroke-width="2" fill="none" opacity="0.4"/>'
    '<path d="M-10 112 Q40 104 90 112 Q130 118 170 108 L170 156 L-10 156 Z" fill="#f8dca0"/>'
    '<circle cx="138" cy="138" r="3" fill="#ff8787"/><path d="M16 140 l4 -6 4 6 Z" fill="#ffa8a8"/>',
    lin("bg", (0, "#4dabf7"), (1, "#a5d8ff")) + lin("sea", (0, "#1c7ed6"), (1, "#3bc9db")))

ART["bg_mountain"] = bg(
    cloud(98, -2, 0.8)
    + '<path d="M-10 92 L30 30 L56 66 L88 14 L130 74 L150 50 L170 72 L170 156 L-10 156 Z" fill="#74b816" opacity="0.55"/>'
    '<path d="M88 14 L100 32 L92 30 L86 36 L78 30 Z" fill="#fff"/><path d="M30 30 L38 42 L30 40 L24 44 Z" fill="#fff"/>'
    '<path d="M-10 110 L26 70 L66 104 L104 64 L146 100 L170 84 L170 156 L-10 156 Z" fill="#37b24d"/>'
    '<path d="M-10 132 Q60 118 170 130 L170 156 L-10 156 Z" fill="#2b8a3e"/>',
    lin("bg", (0, "#a5d8ff"), (1, "#e7f5ff")))

_sakura = ('<path d="M170 -18 Q130 -6 110 10 Q96 22 80 22 M128 -4 Q122 14 128 28 M-10 -8 Q20 0 34 18 Q42 28 40 40" '
           'stroke="#7a4a3a" stroke-width="3.4" fill="none" stroke-linecap="round"/>')
for x, y in [(110, 10), (96, 20), (128, 28), (140, -6), (156, -12), (82, 22), (34, 18), (40, 40), (14, 2), (122, 14)]:
    _sakura += flower(x, y, 4, "#ffc9de", "#ff8fb1", rot=x)
for x, y, a in [(20, 70, 20), (140, 60, -30), (60, 50, 60), (150, 100, 10), (8, 110, -40), (100, 46, 30)]:
    _sakura += f'<ellipse cx="{x}" cy="{y}" rx="3.4" ry="2" fill="#ffb3cf" transform="rotate({a} {x} {y})"/>'
ART["bg_sakura"] = bg(_sakura + '<path d="M-10 134 Q80 124 170 134 L170 156 L-10 156 Z" fill="#ffd6e7"/>',
                      lin("bg", (0, "#fff0f6"), (1, "#ffdeeb")))

_stars = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" opacity="{o}"/>' for x, y, r, o in [
    (0, -10, 1.4, 0.9), (30, 12, 1, 0.7), (60, -16, 1.6, 0.9), (150, 30, 1.2, 0.8), (4, 60, 1.2, 0.6), (40, 96, 1, 0.6),
    (156, 100, 1.4, 0.8), (110, -14, 1, 0.7), (20, 130, 1.2, 0.6), (140, 136, 1, 0.6), (96, 4, 1, 0.6)])
ART["bg_space"] = bg(
    _stars + f'<path d="{star_path(18, 30, 5, 0.4, 4)}" fill="#ffe066"/><path d="{star_path(142, 66, 4, 0.4, 4)}" fill="#a5d8ff"/>'
    '<circle cx="132" cy="2" r="16" fill="url(#pl)"/>'
    '<ellipse cx="132" cy="2" rx="27" ry="7" fill="none" stroke="#ffd8a8" stroke-width="3" transform="rotate(-18 132 2)"/>'
    '<circle cx="4" cy="128" r="9" fill="#dee2e6"/><circle cx="1" cy="125" r="2.4" fill="#ced4da"/><circle cx="8" cy="131" r="1.6" fill="#ced4da"/>',
    lin("bg", (0, "#1b1f4b"), (1, "#3b2a78")) + lin("pl", (0, "#ffa94d"), (1, "#e8590c")))

ART["bg_sunrise"] = bg(
    '<circle cx="80" cy="122" r="44" fill="#ffe066" opacity="0.35"/><circle cx="80" cy="122" r="30" fill="#ffd43b"/>'
    + "".join(f'<path d="M80 122 L{80 + 90 * math.cos(math.radians(a)):.0f} {122 - 90 * math.sin(math.radians(a)):.0f}" '
              f'stroke="#fff3bf" stroke-width="6" opacity="0.35"/>' for a in range(20, 170, 25))
    + cloud(0, 30, 0.8, 0.7) + cloud(120, 14, 0.7, 0.7)
    + '<path d="M-10 126 Q80 116 170 126 L170 156 L-10 156 Z" fill="#f08c00" opacity="0.7"/>',
    lin("bg", (0, "#ff8fab"), (0.55, "#ffc078"), (1, "#ffe8a3")))

_flames = ""
for x, h, c in [(-4, 70, "#ff6b1a"), (24, 96, "#ff922b"), (56, 64, "#ff6b1a"), (104, 70, "#ff6b1a"), (136, 100, "#ff922b"), (164, 74, "#ff6b1a")]:
    _flames += (f'<path d="M{x - 18} 156 Q{x - 20} {156 - h * 0.5} {x} {156 - h} Q{x + 4} {156 - h * 0.6} {x + 12} {156 - h * 0.7} '
                f'Q{x + 22} {156 - h * 0.4} {x + 18} 156 Z" fill="{c}" opacity="0.85"/>')
    _flames += f'<path d="M{x - 8} 156 Q{x - 8} {156 - h * 0.35} {x + 2} {156 - h * 0.6} Q{x + 10} {156 - h * 0.3} {x + 8} 156 Z" fill="#ffd43b" opacity="0.85"/>'
ART["bg_flame"] = bg(_flames + "".join(f'<circle cx="{x}" cy="{y}" r="1.8" fill="#ffd43b" opacity="0.8"/>'
                                       for x, y in [(20, 10), (60, -8), (110, 4), (146, 20), (90, 30), (8, 50)]),
                     lin("bg", (0, "#3b0a0a"), (1, "#8f1d14")))

_beams = ""
for i, c in enumerate(["#ff6b81", "#ff922b", "#ffd43b", "#10c79a", "#1899f0", "#845ef7"]):
    a0, a1 = 200 + i * 23, 200 + (i + 1) * 23
    p0 = (80 + 200 * math.cos(math.radians(a0)), -10 - 200 * math.sin(math.radians(a0)))
    p1 = (80 + 200 * math.cos(math.radians(a1)), -10 - 200 * math.sin(math.radians(a1)))
    _beams += f'<path d="M80 -10 L{p0[0]:.0f} {p0[1]:.0f} L{p1[0]:.0f} {p1[1]:.0f} Z" fill="{c}" opacity="0.32"/>'
ART["bg_prism"] = bg(
    _beams + '<path d="M80 -24 L96 4 L64 4 Z" fill="#fff" opacity="0.9"/>'
    + "".join(f'<path d="{star_path(x, y, r, 0.35, 4)}" fill="#fff"/>' for x, y, r in [(16, 10, 5), (146, 20, 6), (8, 80, 4), (150, 90, 4)]),
    lin("bg", (0, "#f3f0ff"), (1, "#e7f5ff")))


def bat(x, y, s=1.0):
    return (f'<path transform="translate({x} {y}) scale({s})" d="M0 0 Q-6 -6 -14 -4 Q-10 0 -12 4 Q-6 2 -3 5 Q0 2 3 5 Q6 2 12 4 '
            f'Q10 0 14 -4 Q6 -6 0 0 Z" fill="#1b1030"/>')


ART["bg_halloween"] = bg(
    '<circle cx="124" cy="8" r="22" fill="#fff3bf"/><circle cx="116" cy="2" r="4" fill="#ffe8a3"/><circle cx="130" cy="16" r="3" fill="#ffe8a3"/>'
    + bat(30, 10, 1.1) + bat(60, -8, 0.8) + bat(150, 46, 0.9)
    + '<path d="M-10 128 Q40 114 90 126 Q130 136 170 120 L170 156 L-10 156 Z" fill="#2b1846"/>'
    '<ellipse cx="136" cy="134" rx="13" ry="10" fill="#ff8c1a"/><path d="M136 124 L138 119" stroke="#2f9e44" stroke-width="2.4"/>'
    '<path d="M130 132 L133 130 L133 134 Z M142 132 L139 130 L139 134 Z" fill="#2b1846"/>',
    lin("bg", (0, "#2b1452"), (1, "#7048a8")))

_snow = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" opacity="0.85"/>' for x, y, r in [
    (6, -6, 2), (40, 14, 1.6), (70, -14, 2.2), (110, 6, 1.8), (150, -8, 2), (20, 50, 1.6), (146, 44, 2.2), (4, 96, 1.8),
    (156, 90, 1.6), (120, 30, 1.4), (90, 40, 1.2)])
_tree = ('<path d="M{x} {y} L{x2} {y3} L{x1} {y3} Z M{x} {y4} L{x5} {y6} L{x7} {y6} Z" fill="#2b8a3e"/>'
         '<rect x="{xt}" y="{yt}" width="5" height="8" fill="#6b3e1d"/>')
ART["bg_snow"] = bg(
    _snow
    + _tree.format(x=8, y=70, x1=-10, x2=26, y3=104, y4=88, x5=30, x7=-14, y6=124, xt=5.5, yt=124)
    + _tree.format(x=152, y=76, x1=136, x2=168, y3=106, y4=92, x5=172, x7=132, y6=126, xt=149.5, yt=126)
    + '<path d="M-10 124 Q80 112 170 124 L170 156 L-10 156 Z" fill="#f1f5ff"/>'
    '<path d="M-10 136 Q80 128 170 138 L170 156 L-10 156 Z" fill="#dbe4ff"/>',
    lin("bg", (0, "#1e3a8a"), (1, "#5b8def")))


def lantern(x, y, s=1.0):
    return (f'<g transform="translate({x} {y}) scale({s})">'
            '<path d="M0 -26 L0 -12" stroke="#8a5a00" stroke-width="1.4"/>'
            '<rect x="-6" y="-13" width="12" height="4" rx="1" fill="#ffc94a"/>'
            '<ellipse cx="0" cy="0" rx="13" ry="11" fill="#e03131"/>'
            '<path d="M-5 -10 Q-9 0 -5 10 M5 -10 Q9 0 5 10 M0 -11 L0 11" stroke="#c92a2a" stroke-width="1.2" fill="none"/>'
            '<rect x="-6" y="9" width="12" height="4" rx="1" fill="#ffc94a"/>'
            '<path d="M-3 13 L-4 22 M0 13 L0 23 M3 13 L4 22" stroke="#ffc94a" stroke-width="1.2"/></g>')


def burst(x, y, r, c):
    return "".join(f'<path d="M{x + r * 0.35 * math.cos(math.radians(a)):.1f} {y + r * 0.35 * math.sin(math.radians(a)):.1f} '
                   f'L{x + r * math.cos(math.radians(a)):.1f} {y + r * math.sin(math.radians(a)):.1f}" stroke="{c}" '
                   f'stroke-width="2" stroke-linecap="round"/>' for a in range(0, 360, 30))


_tet = lantern(14, 6) + lantern(146, 14, 0.9) + burst(80, -6, 13, "#ffd43b") + burst(130, 52, 9, "#ffa8a8")
for x, y in [(-4, 104), (6, 92), (154, 98), (162, 112), (148, 86)]:
    _tet += flower(x, y, 3.6, "#ffd43b", "#e8590c", rot=x)
ART["bg_tet"] = bg(
    _tet + '<path d="M-10 132 Q80 122 170 132 L170 156 L-10 156 Z" fill="#c92a2a"/>'
    '<path d="M-10 140 Q80 132 170 142" stroke="#ffc94a" stroke-width="2" fill="none" opacity="0.7"/>',
    lin("bg", (0, "#ffe3c2"), (1, "#ffc9a8")))


# ---------------------------------------------------------------- Prismo, for the contact sheet only

PRISMO = (
    '<defs><linearGradient id="pb" x1="0.2" y1="0" x2="0.8" y2="1"><stop offset="0" stop-color="#62c6ff"/>'
    '<stop offset="0.6" stop-color="#1899f0"/><stop offset="1" stop-color="#0f6fb0"/></linearGradient></defs>'
    '<ellipse cx="80" cy="141" rx="44" ry="6" fill="#000" opacity="0.12"/>'
    '<g stroke-linecap="round" stroke-width="6"><path d="M128 92 L151 80" stroke="#ffb020"/>'
    '<path d="M131 100 L155 99" stroke="#10c79a"/><path d="M128 108 L150 118" stroke="#ff6b81"/></g>'
    '<ellipse cx="62" cy="132" rx="11" ry="6" fill="#0b5a94"/><ellipse cx="98" cy="132" rx="11" ry="6" fill="#0b5a94"/>'
    '<path d="M80 16 L140 122 L20 122 Z" fill="url(#pb)" stroke="url(#pb)" stroke-width="18" stroke-linejoin="round"/>'
    '<path d="M80 24 L80 124 L26 124 Z" fill="#fff" opacity="0.12"/>'
    '<path d="M66 46 L56 64" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity="0.65"/>'
    '<ellipse cx="55" cy="101" rx="7" ry="4.5" fill="#ff8fa3" opacity="0.55"/><ellipse cx="105" cy="101" rx="7" ry="4.5" fill="#ff8fa3" opacity="0.55"/>'
    + "".join(f'<ellipse cx="{x}" cy="88" rx="7.5" ry="8.5" fill="#fff"/><circle cx="{x + 1}" cy="89" r="4.4" fill="{INK}"/>'
              f'<circle cx="{x + 2.5}" cy="86" r="1.6" fill="#fff"/>' for x in (64, 96))
    + f'<path d="M70 104 Q80 114 90 104" stroke="{INK}" stroke-width="4" fill="none" stroke-linecap="round"/>')

ORDER = ["background", "neck", "hand", "glasses", "hat"]


def dressed(codes, size=150):
    by_slot = {o["code"]: o["slot"] for o in catalog.OUTFITS}
    layers = sorted(codes, key=lambda c: ORDER.index(by_slot[c]))
    bgs = [c for c in layers if by_slot[c] == "background"]
    rest = [c for c in layers if by_slot[c] != "background"]
    img = lambda c: f'<image href="file:///{OUT[0]}{c}.svg" x="-10" y="-24" width="180" height="180"/>'
    return (f'<svg viewBox="{VIEW}" width="{size}" height="{size}" style="background:#eef6ff;border-radius:16px;margin:5px">'
            + "".join(img(c) for c in bgs) + PRISMO + "".join(img(c) for c in rest) + "</svg>")


def browser():
    for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe", shutil.which("chromium") or "", shutil.which("google-chrome") or ""):
        if p and os.path.exists(p):
            return p
    raise SystemExit("needs Edge or Chrome to draw the contact sheet")


def main():
    missing = [o["code"] for o in catalog.OUTFITS if o["code"] not in ART]
    if missing:
        raise SystemExit(f"no art for: {', '.join(missing)}")
    for root in OUT:
        os.makedirs(root, exist_ok=True)
        for code, text in ART.items():
            open(root + f"{code}.svg", "w", encoding="utf-8", newline="\n").write(text)
    print(f"{len(ART)} SVG -> {', '.join(OUT)}")
    if len(sys.argv) > 1:  # contact sheet: each piece on Prismo, then a few full outfits
        cells = [dressed([o["code"]]) for o in catalog.OUTFITS]
        cells += [dressed(c) for c in (["bg_beach", "hat_non_la", "glasses_sun", "hand_icecream"],
                                       ["bg_space", "hat_crown", "glasses_star", "neck_medal", "hand_trophy"],
                                       ["bg_halloween", "hat_witch", "hand_pumpkin"],
                                       ["bg_tet", "hand_lixi", "neck_bow", "hat_flowers"],
                                       ["bg_classroom", "hat_grad", "glasses_round", "neck_tie", "hand_book"],
                                       ["bg_snow", "hat_santa", "neck_bell", "glasses_heart"])]
        tmp = tempfile.mkdtemp()
        page = os.path.join(tmp, "s.html")
        open(page, "w", encoding="utf-8").write("<!doctype html><body style='margin:0;background:#fff;width:1280px;display:flex;flex-wrap:wrap'>"
                                                + "".join(cells) + "</body>")
        rows = (len(cells) + 7) // 8
        subprocess.run([browser(), "--headless=new", f"--user-data-dir={tmp}/p", "--allow-file-access-from-files", "--hide-scrollbars",
                        f"--window-size=1280,{rows * 160 + 20}", f"--screenshot={os.path.abspath(sys.argv[1])}",
                        "file:///" + page.replace(os.sep, "/")], check=True, capture_output=True)


if __name__ == "__main__":
    main()
