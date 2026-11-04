"""Writes every diagram of usecase_arch.py / activity.py / sequence.py to docs/diagrams/<kind>/<name>.mmd, renders a
PNG next to it, and writes the index (docs/diagrams/README.md) and one Markdown file with all the Mermaid code.

    pip install playwright        # uses the installed Microsoft Edge, else: playwright install chromium
    python docs/diagrams/src/build.py            # .mmd + PNG + README
    python docs/diagrams/src/build.py --no-png   # .mmd + README only
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import activity  # noqa: E402
import sequence  # noqa: E402
import usecase_arch  # noqa: E402

OUT = Path(__file__).resolve().parents[1]
KINDS = {"usecase": "Use case", "architecture": "Kiến trúc", "activity": "Activity", "sequence": "Sequence"}
PAGE = """<!doctype html><html><head><meta charset="utf-8">
<style>body{margin:0;background:#fff;font-family:Arial,sans-serif}#d{display:inline-block;padding:16px}</style></head>
<body><div id="d"></div><script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs";
mermaid.initialize({startOnLoad: false, theme: "default", securityLevel: "loose",
                    flowchart: {htmlLabels: true, wrappingWidth: 320}, sequence: {mirrorActors: false, wrap: true}});
mermaid.render("g", %s).then(r => {
  document.getElementById("d").innerHTML = r.svg;
  const s = document.querySelector("#d svg"), vb = s.viewBox.baseVal;
  s.style.maxWidth = "none"; s.setAttribute("width", vb.width); s.setAttribute("height", vb.height);
  document.title = "done"; })
  .catch(e => { document.title = "err:" + e.message; });
</script></body></html>"""


def all_diagrams() -> dict[str, str]:
    out = {}
    for mod in (usecase_arch, activity, sequence):
        out.update(mod.DIAGRAMS)
    return out


def title_of(code: str) -> str:
    m = re.search(r"^title:\s*(.+)$", code, re.M)
    return m.group(1).strip().strip('"') if m else ""


def quote_labels(code: str) -> str:
    """Flowchart node text in quotes, so brackets, slashes and colons inside a label are plain text
    (A[x (y)] is a Mermaid syntax error, A["x (y)"] is not). Cylinders A[(…)] and quoted labels stay as they are."""
    if "flowchart" not in code:
        return code
    code = re.sub(r'\b([A-Za-z]\w*)\[(?![\"(])([^\[\]]*?)\]', r'\1["\2"]', code)
    code = re.sub(r'\b([A-Za-z]\w*)\{(?!")([^{}]*?)\}', r'\1{"\2"}', code)
    return re.sub(r'\(\[(?!")([^\]]*?)\]\)', r'(["\1"])', code)


def write_sources(diagrams):
    for name, code in diagrams.items():
        code = quote_labels(code)
        # a colon in the title would break the YAML front matter
        code = re.sub(r'^title:\s*(?!")(.+)$', lambda m: 'title: "%s"' % m.group(1).replace('"', "'"), code, flags=re.M)
        diagrams[name] = code
        path = OUT / f"{name}.mmd"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code.strip() + "\n", encoding="utf-8")


def render(diagrams):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="msedge")
        except Exception:
            browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=2, viewport={"width": 1800, "height": 1200})
        for name in diagrams:
            mmd = OUT / f"{name}.mmd"
            page.set_content(PAGE % json.dumps(mmd.read_text(encoding="utf-8")))
            page.wait_for_function("document.title.length > 0", timeout=60000)
            if page.title() != "done":
                raise SystemExit(f"{name}: {page.title()}")
            page.locator("#d").screenshot(path=str(mmd.with_suffix(".png")))
            print("→", mmd.with_suffix(".png").relative_to(OUT))
        browser.close()


def write_index(diagrams):
    rows = {k: [] for k in KINDS}
    for name, code in diagrams.items():
        kind, base = name.split("/")
        rows[kind].append(f"| {title_of(code)} | [`{base}.mmd`]({kind}/{base}.mmd) | [PNG]({kind}/{base}.png) |")
    parts = [README_HEAD]
    for kind, label in KINDS.items():
        parts.append(f"## {label} ({len(rows[kind])} sơ đồ)\n\n| Sơ đồ | Mã Mermaid | Ảnh |\n|---|---|---|\n" + "\n".join(rows[kind]))
    (OUT / "README.md").write_text("\n\n".join(parts) + "\n", encoding="utf-8")

    blocks = ["# Toàn bộ mã Mermaid\n\nMỗi khối dưới đây dán thẳng được vào draw.io "
              "(Sắp xếp → Chèn → Nâng cao → Mermaid) hoặc mermaid.live."]
    for kind, label in KINDS.items():
        blocks.append(f"## {label}")
        for name, code in diagrams.items():
            if name.startswith(kind + "/"):
                blocks.append(f"### {title_of(code)}\n\n```mermaid\n{code.strip()}\n```")
    (OUT / "TAT_CA_MA_MERMAID.md").write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


README_HEAD = """# Sơ đồ phân tích thiết kế LingoPrism

Vẽ từ mã nguồn thật của máy chủ (`BE/apps/*`: 17 module, ~200 endpoint REST, 3 WebSocket), web React và app Flutter.
Nguồn của mọi sơ đồ: `src/usecase_arch.py`, `src/activity.py`, `src/sequence.py`; chạy `python docs/diagrams/src/build.py`
để ghi lại các file `.mmd` + PNG và trang này. ERD cơ sở dữ liệu ở [`docs/database/`](../database/README.md).

## Dùng trong draw.io

1. Mở [app.diagrams.net](https://app.diagrams.net) (hoặc draw.io Desktop).
2. **Sắp xếp → Chèn → Nâng cao → Mermaid…** (*Arrange → Insert → Advanced → Mermaid*).
3. Dán nội dung một file `.mmd` (hoặc một khối trong [`TAT_CA_MA_MERMAID.md`](TAT_CA_MA_MERMAID.md)) → **Chèn**.
4. Flowchart (use case, kiến trúc, activity) thành hình sửa được từng khối; sequence chèn thành một hình, bấm đúp để sửa mã.

Hoặc dán vào [mermaid.live](https://mermaid.live) để xem / xuất SVG, PNG. Ảnh PNG có sẵn cạnh mỗi file để chèn thẳng vào Word.

**Quy ước:** use case – tác nhân 👤, hệ thống ngoài 🖥 (viền đứt), «include» / «extend» là mũi tên đứt; activity – ● bắt đầu,
◉ kết thúc, hình thoi vàng là rẽ nhánh, khối xanh là việc máy chủ làm, khối đỏ là lỗi; sequence – đúng tên endpoint,
view, service và thành phần (PostgreSQL, Redis, Celery, dịch vụ ngoài) trong code."""


if __name__ == "__main__":
    diagrams = all_diagrams()
    write_sources(diagrams)
    write_index(diagrams)
    print(len(diagrams), "sơ đồ")
    if "--no-png" not in sys.argv:
        render(diagrams)
