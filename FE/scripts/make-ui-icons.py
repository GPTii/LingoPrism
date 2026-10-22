"""LingoPrism UI icons: chunky, filled, each shape sitting on a darker lip (the same idea as the buttons).
Writes one SVG per icon to the web and the app, plus an optional contact sheet for checking them by eye:

    python FE/scripts/make-ui-icons.py [sheet.html]
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")).replace(os.sep, "/") + "/"
OUT = [ROOT + "FE/public/icons/ui/", ROOT + "MOBILE/assets/icons/ui/"]

# colour pairs: face, lip
RED = ("#ff4b4b", "#d93636")
ORANGE = ("#ff9600", "#d97f00")
YELLOW = ("#ffc800", "#e0a800")
GREEN = ("#58cc02", "#43a000")
TEAL = ("#14c9a8", "#0ea287")
BLUE = ("#1cb0f6", "#1290cf")
PURPLE = ("#ce82ff", "#a95fe0")
PINK = ("#ff86c8", "#e062a8")
BROWN = ("#c98546", "#a0662f")
WHITE = ("#ffffff", "#d5dce6")
GREY = ("#c4cfdb", "#9aa8b8")
DARK = "#3c4a5c"
SKY = "#bfe9ff"

LIP = 3  # px of lip below every face, in the 48-unit box


def lip(shape, pair, dy=LIP):
    """A shape drawn twice: its darker lip a little lower, then its face."""
    face, under = pair
    return (f'<g transform="translate(0 {dy})">{shape.format(f=under)}</g>' if dy else "") + shape.format(f=face)


def round_path(d):
    # filled and stroked in the same colour: every corner comes out rounded
    return f'<path d="{d}" fill="{{f}}" stroke="{{f}}" stroke-width="4" stroke-linejoin="round"/>'


def shine(d, w=3, o=0.55):
    return f'<path d="{d}" fill="none" stroke="#fff" stroke-width="{w}" stroke-linecap="round" opacity="{o}"/>'


def line(d, color, w=4):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'


def person(cx, head_y, r, body_top, body_w, bottom, pair):
    body = f'<path d="M{cx - body_w + 2} {bottom - 2} Q{cx - body_w + 2} {body_top + 2} {cx} {body_top + 2} Q{cx + body_w - 2} {body_top + 2} {cx + body_w - 2} {bottom - 2} Z" fill="{{f}}" stroke="{{f}}" stroke-width="4" stroke-linejoin="round"/>'
    head = f'<circle cx="{cx}" cy="{head_y}" r="{r}" fill="{{f}}"/>'
    return lip(body, pair) + lip(head, pair)


I = {}

I["home"] = (
    lip('<rect x="10" y="20" width="28" height="20" rx="3" fill="{f}"/>', YELLOW)
    + lip(round_path("M24 7 L41 21 L7 21 Z"), RED)
    + '<rect x="20" y="28" width="8" height="15" rx="3" fill="#a0662f"/>'
    + '<rect x="30" y="26" width="5" height="5" rx="1.5" fill="#bfe9ff"/>'
    + shine("M15 18 L21 13")
)

I["learn"] = (  # an open book
    lip('<path d="M4 13 Q14 9 24 14 Q34 9 44 13 V40 Q34 37 24 42 Q14 37 4 40 Z" fill="{f}"/>', BLUE)
    + lip('<path d="M8 12 Q16 9 22.5 13.5 V37 Q16 33.5 8 35.5 Z" fill="{f}"/>', ("#ffffff", "#cfe9f8"), 2)
    + lip('<path d="M40 12 Q32 9 25.5 13.5 V37 Q32 33.5 40 35.5 Z" fill="{f}"/>', ("#ffffff", "#cfe9f8"), 2)
    + line("M12 18 Q16 17 19 19 M12 24 Q16 23 19 25", "#9fd8f7", 2.5)
    + line("M29 19 Q32 17 36 18 M29 25 Q32 23 36 24", "#9fd8f7", 2.5)
)

I["vocab"] = (  # flashcards
    '<g transform="rotate(-12 20 26)">' + lip('<rect x="7" y="11" width="24" height="30" rx="5" fill="{f}"/>', PURPLE) + '</g>'
    + lip('<rect x="17" y="8" width="24" height="31" rx="5" fill="{f}"/>', ORANGE)
    + line("M23 32 L29 16 L35 32 M25.4 26.5 H32.6", "#fff", 3.6)
)

I["camera"] = (
    lip('<rect x="16" y="9" width="15" height="9" rx="3" fill="{f}"/>', RED)
    + lip('<rect x="5" y="14" width="38" height="26" rx="7" fill="{f}"/>', RED)
    + f'<circle cx="24" cy="28" r="9.5" fill="#fff"/><circle cx="24" cy="28" r="6.2" fill="{BLUE[0]}"/>'
    + '<circle cx="21.8" cy="25.8" r="2.1" fill="#fff"/>'
    + f'<rect x="34" y="18" width="5" height="3.5" rx="1.5" fill="{YELLOW[0]}"/>'
    + shine("M9 21 V25")
)

I["community"] = person(31, 14, 6, 24, 10, 38, PURPLE) + person(18, 18, 7.5, 29, 12.5, 42, GREEN)

I["trophy"] = (
    line("M14 13 H8.5 Q8 23 15.5 24", YELLOW[1], 3.6) + line("M34 13 H39.5 Q40 23 32.5 24", YELLOW[1], 3.6)
    + lip('<rect x="20.5" y="27" width="7" height="9" fill="{f}"/>', YELLOW)
    + lip(round_path("M14 8 H34 V17 Q34 29 24 29 Q14 29 14 17 Z"), YELLOW)
    + lip('<rect x="13" y="35" width="22" height="7" rx="2.5" fill="{f}"/>', ORANGE)
    + shine("M19 12 V18")
)

I["chat"] = (
    lip(round_path("M9 9 H39 Q41 9 41 11 V29 Q41 31 39 31 H23 L14 39 V31 H9 Q7 31 7 29 V11 Q7 9 9 9 Z"), TEAL)
    + '<circle cx="16" cy="20" r="2.8" fill="#fff"/><circle cx="24" cy="20" r="2.8" fill="#fff"/><circle cx="32" cy="20" r="2.8" fill="#fff"/>'
)

I["bell"] = (
    lip('<circle cx="24" cy="39" r="4.5" fill="{f}"/>', ORANGE)
    + lip(round_path("M24 8 Q14.5 8 14 19 V27 L9.5 33 H38.5 L34 27 V19 Q33.5 8 24 8 Z"), YELLOW)
    + lip('<circle cx="24" cy="7" r="3" fill="{f}"/>', YELLOW, 0)
    + shine("M19 15 Q19 13 21 12")
)

I["sparkle"] = (  # new words
    lip('<path d="M21 5 Q23.5 18 35 21 Q23.5 24 21 37 Q18.5 24 7 21 Q18.5 18 21 5 Z" fill="{f}"/>', YELLOW)
    + lip('<path d="M36 28 Q37.2 34.5 42 36 Q37.2 37.5 36 44 Q34.8 37.5 30 36 Q34.8 34.5 36 28 Z" fill="{f}"/>', BLUE, 2)
    + lip('<path d="M36 4 Q36.8 8.5 40 9.5 Q36.8 10.5 36 15 Q35.2 10.5 32 9.5 Q35.2 8.5 36 4 Z" fill="{f}"/>', PINK, 2)
)

def _review(c):
    arrow = line("M37.2 28.8 A14 14 0 1 1 23 10", c, 6)
    head = f'<path d="M22 3.5 L31.5 10 L22 16.5 Z" fill="{c}" stroke="{c}" stroke-width="3" stroke-linejoin="round"/>'
    return arrow + head


I["review"] = f'<g transform="translate(0 {LIP})">{_review(GREEN[1])}</g>' + _review(GREEN[0])

I["tiles"] = (  # sentence building: word tiles
    lip('<rect x="4" y="10" width="19" height="12" rx="3.5" fill="{f}"/>', ORANGE)
    + lip('<rect x="26" y="10" width="18" height="12" rx="3.5" fill="{f}"/>', BLUE)
    + lip('<rect x="9" y="27" width="30" height="12" rx="3.5" fill="{f}"/>', GREEN)
    + '<rect x="8" y="14.5" width="11" height="3" rx="1.5" fill="#fff" opacity="0.8"/>'
    + '<rect x="30" y="14.5" width="10" height="3" rx="1.5" fill="#fff" opacity="0.8"/>'
    + '<rect x="13" y="31.5" width="22" height="3" rx="1.5" fill="#fff" opacity="0.8"/>'
)

I["mic"] = (
    line("M11 22 Q11 34.5 24 34.5 Q37 34.5 37 22", GREY[1], 4) + line("M24 35 V41", GREY[1], 4) + line("M16.5 42 H31.5", GREY[1], 4.5)
    + lip('<rect x="16.5" y="5" width="15" height="24" rx="7.5" fill="{f}"/>', RED)
    + shine("M21 10 V16")
)

I["pencil"] = (
    '<g transform="rotate(40 24 24)">'
    + lip('<rect x="18.5" y="9" width="11" height="25" fill="{f}"/>', YELLOW)
    + lip('<path d="M18.5 3 H29.5 V9 H18.5 Z" fill="{f}"/>', PINK, 0)
    + '<rect x="18.5" y="8" width="11" height="3" fill="#c4cfdb"/>'
    + '<path d="M18.5 34 H29.5 L24 44 Z" fill="#f6d5a8" stroke="#f6d5a8" stroke-width="1.5" stroke-linejoin="round"/>'
    + f'<path d="M22.2 40.7 H25.8 L24 44 Z" fill="{DARK}" stroke="{DARK}" stroke-width="1.5" stroke-linejoin="round"/>'
    + '<rect x="25.5" y="9" width="4" height="25" fill="#e0a800"/></g>'
)

I["exam"] = (  # clipboard with a tick
    lip('<rect x="8" y="8" width="32" height="35" rx="5" fill="{f}"/>', BROWN)
    + '<rect x="12" y="13" width="24" height="26" rx="2.5" fill="#fff"/>'
    + lip('<rect x="17" y="5" width="14" height="7" rx="3" fill="{f}"/>', GREY, 2)
    + line("M17 24 L22 29 L31 18", GREEN[0], 4)
    + line("M17 34.5 H31", "#d5dce6", 3)
)

I["shapes"] = (  # topics
    lip('<circle cx="15" cy="16" r="9" fill="{f}"/>', RED)
    + lip('<rect x="26" y="7" width="16" height="16" rx="3.5" fill="{f}"/>', YELLOW)
    + lip(round_path("M24 27 L35 42 L13 42 Z"), BLUE)
)

I["bookmark"] = (  # my words
    lip(round_path("M13 6 H35 V41 L24 33 L13 41 Z"), PINK)
    + '<path d="M24 25.5 C17 21 18 14.5 21.3 14.5 C22.8 14.5 23.6 15.6 24 16.5 C24.4 15.6 25.2 14.5 26.7 14.5 C30 14.5 31 21 24 25.5 Z" fill="#fff"/>'
)

I["photo"] = (  # photo history
    '<g transform="rotate(-8 24 24)">' + lip('<rect x="8" y="6" width="32" height="27" rx="4" fill="{f}"/>', PURPLE) + '</g>'
    + lip('<rect x="6" y="13" width="34" height="29" rx="4" fill="{f}"/>', WHITE)
    + f'<rect x="10" y="17" width="26" height="21" rx="2" fill="{SKY}"/>'
    + f'<path d="M10 38 L19 26 L25.5 33 L29.5 29 L36 38 Z" fill="{GREEN[0]}"/>'
    + f'<circle cx="29.5" cy="22.5" r="3" fill="{YELLOW[0]}"/>'
)

I["pin"] = (  # map
    '<ellipse cx="24" cy="44" rx="9" ry="2.6" fill="#000" opacity="0.14"/>'
    + lip('<path d="M24 43 Q9.5 29 9.5 19 A14.5 14.5 0 0 1 38.5 19 Q38.5 29 24 43 Z" fill="{f}"/>', RED, 2.5)
    + '<circle cx="24" cy="19" r="5.5" fill="#fff"/>'
    + shine("M15 15 Q16 11 19 9.5")
)

I["news"] = (  # feed
    lip('<rect x="30" y="13" width="12" height="28" rx="4" fill="{f}"/>', GREY)
    + lip('<rect x="6" y="8" width="30" height="33" rx="4" fill="{f}"/>', WHITE)
    + f'<rect x="10" y="12.5" width="11" height="10" rx="2" fill="{BLUE[0]}"/>'
    + line("M25 14 H32 M25 20 H31 M10.5 28 H31.5 M10.5 34 H27", "#c4cfdb", 3)
)

I["group"] = person(36, 15, 5.5, 24, 8.5, 36, PURPLE) + person(12, 15, 5.5, 24, 8.5, 36, GREEN) + person(24, 18, 7, 28, 12, 42, ORANGE)

I["podium"] = (  # leaderboard
    lip('<rect x="4" y="25" width="13" height="17" rx="2.5" fill="{f}"/>', GREY)
    + lip('<rect x="31" y="29" width="13" height="13" rx="2.5" fill="{f}"/>', BROWN)
    + lip('<rect x="17" y="17" width="14" height="25" rx="2.5" fill="{f}"/>', YELLOW)
    + lip('<path d="M24 3 L26.4 8 L31.8 8.6 L27.8 12.2 L28.9 17.5 L24 14.8 L19.1 17.5 L20.2 12.2 L16.2 8.6 L21.6 8 Z" fill="{f}" stroke="{f}" stroke-width="1.5" stroke-linejoin="round"/>', ORANGE, 1.5)
)

I["mail"] = (  # messages
    lip('<rect x="5" y="10" width="38" height="28" rx="5" fill="{f}"/>', PURPLE)
    + line("M9 15 L24 26.5 L39 15", "#fff", 3.6)
)

I["chart"] = (  # stats
    lip('<rect x="6" y="25" width="10" height="16" rx="3" fill="{f}"/>', BLUE)
    + lip('<rect x="19" y="15" width="10" height="26" rx="3" fill="{f}"/>', GREEN)
    + lip('<rect x="32" y="6" width="10" height="35" rx="3" fill="{f}"/>', ORANGE)
)

I["target"] = (  # quests
    lip('<circle cx="22" cy="26" r="17" fill="{f}"/>', RED)
    + '<circle cx="22" cy="26" r="12" fill="#fff"/>'
    + f'<circle cx="22" cy="26" r="7.5" fill="{RED[0]}"/><circle cx="22" cy="26" r="3" fill="#fff"/>'
    + line("M22 26 L39 9", DARK, 3)
    + f'<path d="M36 7 L43 5 L41 12 L37 12 Z" fill="{BLUE[0]}" stroke="{BLUE[0]}" stroke-width="1.5" stroke-linejoin="round"/>'
)

I["calendar"] = (
    lip('<rect x="6" y="9" width="36" height="33" rx="5" fill="{f}"/>', WHITE)
    + f'<path d="M6 14 Q6 9 11 9 H37 Q42 9 42 14 V19 H6 Z" fill="{RED[0]}"/>'
    + f'<rect x="14" y="4" width="5" height="10" rx="2.5" fill="{DARK}"/><rect x="29" y="4" width="5" height="10" rx="2.5" fill="{DARK}"/>'
    + ''.join(f'<rect x="{x}" y="{y}" width="6" height="5" rx="1.5" fill="#d5dce6"/>' for x, y in ((11, 24), (21, 24), (11, 32), (31, 32), (21, 32)))
    + f'<rect x="30" y="23" width="8" height="7" rx="2" fill="{GREEN[0]}"/>'
)

I["medal"] = (  # badges
    lip('<path d="M13 3 H22 L27 18 H19 Z" fill="{f}"/>', BLUE, 0)
    + lip('<path d="M35 3 H26 L21 18 H29 Z" fill="{f}"/>', RED, 0)
    + lip('<circle cx="24" cy="30" r="13" fill="{f}"/>', YELLOW)
    + '<circle cx="24" cy="30" r="8.5" fill="#ffde5c"/>'
    + '<path d="M24 24.5 L25.7 28 L29.5 28.4 L26.7 31 L27.4 34.8 L24 32.9 L20.6 34.8 L21.3 31 L18.5 28.4 L22.3 28 Z" fill="#e0a800"/>'
)

I["bag"] = (  # shop
    line("M17 19 V14 A7 7 0 0 1 31 14 V19", GREEN[1], 3.6)
    + lip(round_path("M9.5 17 H38.5 L36.5 41 H11.5 Z"), GREEN)
    + '<circle cx="17" cy="23" r="2" fill="#fff"/><circle cx="31" cy="23" r="2" fill="#fff"/>'
)

I["cap"] = (  # ask a teacher
    lip(round_path("M14 22 V31 Q24 37 34 31 V22 L24 27 Z"), ("#7a5af0", "#5a3fc8"))
    + lip(round_path("M24 9 L43 17.5 L24 26 L5 17.5 Z"), PURPLE)
    + line("M24 17.5 L37 21.5 V31", YELLOW[0], 2.6)
    + f'<circle cx="37" cy="32" r="3" fill="{YELLOW[0]}"/>'
)

I["profile"] = (
    lip('<path d="M8 43 Q8 28 24 28 Q40 28 40 43 Z" fill="{f}"/>', BLUE)
    + lip('<circle cx="24" cy="16" r="9.5" fill="{f}"/>', ("#ffb98a", "#e8956a"))
    + '<path d="M14.5 15 Q15 6 24 6 Q33 6 33.5 15 Q29 10.5 24 11.5 Q19 10.5 14.5 15 Z" fill="#8a4b22"/>'
)

I["check"] = (  # words mastered
    lip('<circle cx="24" cy="23" r="18" fill="{f}"/>', GREEN)
    + line("M15.5 23.5 L21.5 29.5 L33 17.5", "#fff", 5)
)

I["book"] = (  # words being learnt
    lip('<rect x="9" y="6" width="30" height="36" rx="4" fill="{f}"/>', BLUE)
    + '<rect x="12" y="34" width="27" height="5" fill="#fff"/>'
    + '<rect x="9" y="6" width="5" height="36" rx="2" fill="#1290cf"/>'
    + '<rect x="19" y="13" width="15" height="7" rx="2" fill="#fff" opacity="0.85"/>'
)

I["more"] = (  # everything else
    lip('<rect x="6" y="6" width="16" height="16" rx="4.5" fill="{f}"/>', RED)
    + lip('<rect x="26" y="6" width="16" height="16" rx="4.5" fill="{f}"/>', YELLOW)
    + lip('<rect x="6" y="25" width="16" height="16" rx="4.5" fill="{f}"/>', BLUE)
    + lip('<rect x="26" y="25" width="16" height="16" rx="4.5" fill="{f}"/>', GREEN)
)


def svg(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">{body}</svg>\n'


if __name__ == "__main__":
    for d in OUT:
        os.makedirs(d, exist_ok=True)
        for name, body in I.items():
            open(d + name + ".svg", "w", encoding="utf-8", newline="\n").write(svg(body))
    sheet = sys.argv[1] if len(sys.argv) > 1 else None
    if sheet:
        cells = "".join(
            f'<div class="c"><div class="i">{svg(b)}</div><div class="i s">{svg(b)}</div><span>{n}</span></div>' for n, b in I.items())
        html = ('<!doctype html><meta charset=utf-8><style>body{margin:0;padding:16px;font:13px Segoe UI;display:grid;grid-template-columns:repeat(8,1fr);gap:10px;background:#fff}'
                '.c{display:flex;flex-direction:column;align-items:center;gap:4px;padding:8px;border:1px solid #eee;border-radius:10px}'
                '.i svg{width:64px;height:64px}.s svg{width:24px;height:24px}</style>' + cells)
        open(sheet, "w", encoding="utf-8").write(html)
    print(len(I), "icons")
