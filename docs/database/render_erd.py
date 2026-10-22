"""Render docs/database/erd/*.mmd (Mermaid erDiagram) to PNG for the report.

    pip install playwright        # uses the installed Microsoft Edge, else: playwright install chromium
    python docs/database/render_erd.py

ELK layout (layered, orthogonal edges): the default dagre layout spreads 20 tables over one very wide row.
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ERD = Path(__file__).resolve().parent / "erd"
PAGE = """<!doctype html><html><head><meta charset="utf-8">
<style>body{margin:0;background:#fff;font-family:Arial,sans-serif}#d{display:inline-block;padding:16px}</style></head>
<body><div id="d"></div><script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs";
import elk from "https://cdn.jsdelivr.net/npm/@mermaid-js/layout-elk@0.1.7/dist/mermaid-layout-elk.esm.min.mjs";
mermaid.registerLayoutLoaders(elk);
mermaid.initialize({startOnLoad: false, theme: "neutral", layout: "elk",
                    elk: {mergeEdges: false, nodePlacementStrategy: "NETWORK_SIMPLEX"}, er: {fontSize: 14}});
mermaid.render("g", %s).then(r => {
  document.getElementById("d").innerHTML = r.svg;
  const s = document.querySelector("#d svg"), vb = s.viewBox.baseVal;  // natural size, not shrunk to the page
  s.style.maxWidth = "none"; s.setAttribute("width", vb.width); s.setAttribute("height", vb.height);
  document.title = "done"; })
  .catch(e => { document.title = "err:" + e.message; });
</script></body></html>"""


def main():
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="msedge")
        except Exception:
            browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=2, viewport={"width": 1600, "height": 1000})
        for mmd in sorted(ERD.glob("*.mmd")):
            page.set_content(PAGE % json.dumps(mmd.read_text(encoding="utf-8")))
            page.wait_for_function("document.title.length > 0", timeout=60000)
            if page.title() != "done":
                raise SystemExit(f"{mmd.name}: {page.title()}")
            page.locator("#d").screenshot(path=str(mmd.with_suffix(".png")))
            print("→", mmd.with_suffix(".png").name)
        browser.close()


if __name__ == "__main__":
    main()
