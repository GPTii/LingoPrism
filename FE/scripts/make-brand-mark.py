"""Prismo's face: the app icon, the opening screen picture and the web's PWA icons, from one drawing.

The same face is drawn in code on the app's opening screen (MOBILE/lib/app/core/widgets/prismo_face.dart),
where it moves; keep the two in step. PNGs are rendered with headless Edge or Chrome:

    python FE/scripts/make-brand-mark.py
"""
import os
import shutil
import subprocess
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")).replace(os.sep, "/") + "/"
BLUE, BODY, LIP, INK = "#1899f0", "#5cc6ff", "#0f78c8", "#15233b"


def face(beams=True):
    """Prismo on a 160 × 160 grid, no background."""
    tri = "M80 22 L138 124 L22 124 Z"
    return (
        (f'<g stroke-width="7" stroke-linecap="round">'
         f'<path d="M131 95 L152 84" stroke="#ffb020"/><path d="M134 104 L157 104" stroke="#10c79a"/>'
         f'<path d="M131 113 L152 124" stroke="#ff6b81"/></g>' if beams else "")
        + f'<path d="{tri}" transform="translate(0 7)" fill="{LIP}" stroke="{LIP}" stroke-width="22" stroke-linejoin="round"/>'
        + f'<path d="{tri}" fill="{BODY}" stroke="{BODY}" stroke-width="22" stroke-linejoin="round"/>'
        + '<path d="M67 43 L58 59" stroke="#fff" stroke-width="6" stroke-linecap="round" opacity="0.6"/>'
        + '<ellipse cx="44" cy="113" rx="7" ry="4.5" fill="#ff8fa3" opacity="0.75"/>'
        + '<ellipse cx="116" cy="113" rx="7" ry="4.5" fill="#ff8fa3" opacity="0.75"/>'
        + ''.join(
            f'<ellipse cx="{x}" cy="89" rx="17.5" ry="21" fill="#fff"/>'
            f'<ellipse cx="{x + 3}" cy="93" rx="8.5" ry="10.5" fill="{INK}"/>'
            f'<circle cx="{x + 6.5}" cy="87.5" r="3.4" fill="#fff"/>' for x in (60, 100))
        + f'<path d="M73 113 Q80 120 87 113" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>'
    )


def svg(body, size=None, bg=None, scale=1.0, rx=0):
    pad = 80 * (1 - scale)
    inner = f'<g transform="translate({pad} {pad}) scale({scale})">{body}</g>'
    back = f'<rect width="160" height="160" rx="{rx}" fill="{bg}"/>' if bg else ""
    dims = f' width="{size}" height="{size}"' if size else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160"{dims}>{back}{inner}</svg>\n'


def browser():
    for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe", shutil.which("chromium") or "", shutil.which("google-chrome") or ""):
        if p and os.path.exists(p):
            return p
    raise SystemExit("needs Edge or Chrome to render the PNGs")


def png(svg_text, out, px):
    tmp = tempfile.mkdtemp()
    page = os.path.join(tmp, "m.html")
    open(page, "w", encoding="utf-8").write(
        f'<!doctype html><style>html,body{{margin:0;background:transparent}}svg{{display:block;width:{px}px;height:{px}px}}</style>{svg_text}')
    subprocess.run([browser(), "--headless=new", f"--user-data-dir={tmp}/p", "--hide-scrollbars", "--default-background-color=00000000",
                    f"--window-size={px},{px}", f"--screenshot={os.path.abspath(out)}", "file:///" + page.replace(os.sep, "/")],
                   check=True, capture_output=True)


if __name__ == "__main__":
    F = face()
    open(ROOT + "FE/public/logo.svg", "w", encoding="utf-8", newline="\n").write(svg(F, bg=BLUE, rx=36, scale=0.9))
    B = ROOT + "MOBILE/assets/brand/"
    png(svg(F, bg=BLUE, scale=0.94), B + "logo.png", 1024)               # Android (legacy), full square
    png(svg(F, bg=BLUE, scale=0.94), B + "logo_square.png", 1024)        # iOS: no transparency
    png(svg(F, scale=0.56), B + "logo_foreground.png", 1024)             # Android adaptive: inside the safe zone
    png(svg(F, scale=0.94), B + "splash_face.png", 768)                  # the opening screen: 180 dp of face at 4×
    png(svg(F, scale=0.625), B + "splash_face_android12.png", 1152)      # Android 12+: 180 dp of face inside its 288 dp icon
    P = ROOT + "FE/public/icons/"
    png(svg(F, bg=BLUE, scale=0.94), P + "icon-512.png", 512)
    png(svg(F, bg=BLUE, scale=0.94), P + "icon-192.png", 192)
    png(svg(F, bg=BLUE, scale=0.66), P + "icon-maskable-512.png", 512)
    png(svg(F, bg=BLUE, scale=0.94), P + "apple-touch-icon.png", 180)
    print("ok")
