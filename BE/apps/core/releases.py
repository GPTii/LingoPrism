"""Release notes: apps/core/releases.json is the only source. The web and the app show it ("Có gì mới") through
GET /api/v1/releases/, and `manage.py changelog` writes CHANGELOG.md at the repository root from it (a test fails
when the two disagree). Adding a release = a new entry at the top of releases.json, then `manage.py changelog`."""
import json
from functools import cache
from pathlib import Path

SOURCE = Path(__file__).with_name("releases.json")
SECTIONS = (("new", "Mới"), ("improved", "Cải thiện"), ("fixed", "Sửa lỗi"))


@cache
def releases() -> list[dict]:
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def changelog_markdown() -> str:
    out = ["# Nhật ký phiên bản LingoPrism", "",
           "<!-- Sinh từ BE/apps/core/releases.json bằng `python manage.py changelog` – sửa ở file đó, không sửa ở đây. -->", ""]
    for r in releases():
        day = "/".join(reversed(r["date"].split("-")))
        out += [f"## {r['version']} – {day}: {r['title']}", ""]
        for key, heading in SECTIONS:
            if r.get(key):
                out += [f"### {heading}", "", *(f"- {line}" for line in r[key]), ""]
    return "\n".join(out).rstrip() + "\n"
