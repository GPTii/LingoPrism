"""Download one real, freely-licensed photo per vocabulary word from Wikimedia Commons.

    python manage.py fetch_word_images            # resolve + download what is missing
    python manage.py fetch_word_images --only cat,dog --force

The photo is the lead image of the word's English Wikipedia article (``WIKI_TITLES`` disambiguates, e.g. "mouse" the
animal vs. the computer mouse), or an explicit Commons file set in ``seed/concepts/images.csv`` (column
``commons_file``) when a reviewer rejected the automatic one. Only CC0 / public-domain / CC BY / CC BY-SA files are
kept, and author + licence are stored next to the picture so the app can credit them. Colours get a generated swatch.

Result: ``seed/images/<slug>.jpg`` + ``seed/concepts/images.csv`` (committed). ``status``: ``unreviewed`` (new
automatic pick) → ``verified`` once a person looked at it; ``none`` = no suitable free photo, keep the emoji.
``build_vocab`` attaches only verified pictures to the words.
"""
import csv
import html
import io
import re
import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageDraw, ImageFont

API_WIKI = "https://en.wikipedia.org/w/api.php"
API_COMMONS = "https://commons.wikimedia.org/w/api.php"
UA = "LingoPrism/1.0 (graduation project; https://github.com/GPTii/LingoPrism)"
SIZE = 480
FIELDS = ["slug", "wiki_title", "commons_file", "license", "author", "source_url", "status"]
FREE = re.compile(r"^(cc0|public domain|pd\b|pd-|gfdl|fal\b|no restrictions|cc[ -]by(-sa)?[ -]?\d|cc by(-sa)? \d)", re.I)

# English Wikipedia article whose lead photo illustrates the word (default: the English word itself).
WIKI_TITLES = {
    "person": "Human", "friend": "Friendship", "doctor": "Physician", "subway": "Rapid transit",
    "bench": "Bench (furniture)", "mouse-animal": "House mouse", "hippo": "Hippopotamus", "tie": "Necktie",
    "baseball-bat": "Baseball bat", "tennis-racket": "Racket (sports equipment)", "orange": "Orange (fruit)",
    "donut": "Doughnut", "table": "Table (furniture)", "television": "Television set", "computer-mouse": "Computer mouse",
    "keyboard": "Computer keyboard", "microwave": "Microwave oven", "glue": "Adhesive", "corn": "Maize",
    "noodles": "Noodle", "egg": "Egg as food", "lamp": "Balanced-arm lamp", "light-bulb": "Incandescent light bulb",
    "fan": "Mechanical fan", "key": "Key (lock)", "trash-can": "Waste container", "plate": "Plate (dishware)",
    "pot": "Cookware and bakeware", "pants": "Trousers", "shoes": "Shoe", "socks": "Sock", "ring": "Ring (jewellery)",
    "gloves": "Glove", "belt": "Belt (clothing)", "eye": "Human eye", "nose": "Human nose", "mouth": "Lip",
    "head": "Human head", "leg": "Human leg", "tablet": "Tablet computer", "charger": "Battery charger",
    "printer": "Printer (computing)", "screen": "Computer monitor", "battery": "Electric battery", "grass": "Lawn",
    "stone": "Rock (geology)", "football": "Ball (association football)", "basketball": "Basketball (ball)",
    "volleyball": "Volleyball (ball)", "ticket": "Ticket (admission)", "market": "Marketplace",
    "cinema": "Movie theater", "pharmacy": "Pharmacy (shop)", "church": "Church (building)", "glasses": "Glasses",
    "mobile-phone": "Mobile phone", "pen": "Pen", "ruler": "Ruler", "map": "Map", "bank": "Bank",
}
COLORS = {
    "red": "#E53935", "blue": "#1E88E5", "yellow": "#FDD835", "green": "#43A047", "white": "#FFFFFF",
    "black": "#212121", "pink": "#F48FB1", "purple": "#8E24AA", "orange-color": "#FB8C00", "brown": "#795548",
    "gray": "#9E9E9E", "beige": "#E8D8B8", "cyan": "#00BCD4", "gold-color": "#D4AF37", "silver-color": "#C0C0C0",
}
# Numbers get a card with the numeral (drawn here, so no licence question).
NUMERALS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
    "nine": "9", "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14", "fifteen": "15",
    "sixteen": "16", "seventeen": "17", "eighteen": "18", "nineteen": "19", "twenty": "20", "thirty": "30",
    "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70", "eighty": "80", "ninety": "90", "hundred": "100",
    "thousand": "1000",
}


def _plain(text):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", text or ""))).strip()


class Command(BaseCommand):
    help = "Tải ảnh thật (Wikimedia Commons, giấy phép tự do) cho từng từ vựng"

    def add_arguments(self, parser):
        parser.add_argument("--only", help="slug1,slug2")
        parser.add_argument("--force", action="store_true", help="tải lại cả ảnh đã có")

    def handle(self, *args, only=None, force=False, **opts):
        seed = settings.BASE_DIR / "seed"
        self.out_dir = seed / "images"
        self.out_dir.mkdir(exist_ok=True)
        self.csv_path = seed / "concepts" / "images.csv"
        with open(seed / "concepts" / "words.csv", encoding="utf-8") as fh:
            words = {r["slug"]: r["en"] for r in csv.DictReader(fh)}
        rows = {}
        if self.csv_path.exists():
            with open(self.csv_path, encoding="utf-8") as fh:
                rows = {r["slug"]: r for r in csv.DictReader(fh)}
        for slug, en in words.items():
            rows.setdefault(slug, {"slug": slug, "wiki_title": WIKI_TITLES.get(slug, en[:1].upper() + en[1:])})
        wanted = set(only.split(",")) if only else set(words)
        if unknown := wanted - set(words):
            raise CommandError(f"Không có từ: {', '.join(sorted(unknown))}")
        for slug in words:  # a reviewer decided no photo fits (the app falls back to the emoji)
            if rows[slug].get("status") == "none":
                (self.out_dir / f"{slug}.jpg").unlink(missing_ok=True)
        todo = [s for s in words if s in wanted and rows[s].get("status") != "none"
                and (force or not (self.out_dir / f"{s}.jpg").exists())]
        self.session = requests.Session()
        self.session.headers["User-Agent"] = UA

        for slug in [s for s in todo if s in COLORS]:
            swatch = Image.new("RGB", (SIZE, SIZE), COLORS[slug])
            ImageDraw.Draw(swatch).rectangle((0, 0, SIZE - 1, SIZE - 1), outline="#BDBDBD", width=6)  # white on white
            swatch.save(self.out_dir / f"{slug}.jpg", quality=90)
            rows[slug].update(commons_file="", license="CC0", author="LingoPrism (ô màu tự tạo)", source_url="",
                              status=rows[slug].get("status") or "verified")
        for slug in [s for s in todo if s in NUMERALS]:
            self._numeral(NUMERALS[slug], self.out_dir / f"{slug}.jpg")
            rows[slug].update(commons_file="", license="CC0", author="LingoPrism (thẻ số tự tạo)", source_url="",
                              status=rows[slug].get("status") or "verified")
        photos = [s for s in todo if s not in COLORS and s not in NUMERALS]
        need_title = [s for s in photos if not rows[s].get("commons_file")]
        for slug, file in self._page_images([rows[s]["wiki_title"] for s in need_title], need_title).items():
            rows[slug]["commons_file"] = file
        files = {s: rows[s]["commons_file"] for s in photos if rows[s].get("commons_file")}
        info = self._file_info(set(files.values()))
        ok = 0
        for slug in photos:
            meta = info.get(files.get(slug))
            row = rows[slug]
            if not meta:
                row.update(license="", author="", source_url="", status="missing")
                self.stderr.write(f"  ✗ {slug}: không tìm thấy ảnh ({row['wiki_title']})")
                continue
            if not FREE.match(meta["license"]):
                row.update(license=meta["license"], status="rejected")
                self.stderr.write(f"  ✗ {slug}: giấy phép không tự do ({meta['license']})")
                continue
            try:
                self._download(meta["thumb"], self.out_dir / f"{slug}.jpg")
            except Exception as exc:  # noqa: BLE001 – keep going, report at the end
                row["status"] = "missing"
                self.stderr.write(f"  ✗ {slug}: tải lỗi {exc}")
                continue
            # a file picked by a reviewer stays verified; an automatic pick waits for review
            row.update(license=meta["license"], author=meta["author"][:200], source_url=meta["page"],
                       status="verified" if row.get("status") == "verified" else "unreviewed")
            ok += 1
        with open(self.csv_path, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
            w.writeheader()
            for slug in words:
                w.writerow({k: rows[slug].get(k, "") for k in FIELDS})
        self.stdout.write(self.style.SUCCESS(f"Đã tải {ok} ảnh, {len(photos) - ok} lỗi"))

    def _numeral(self, text, dest):
        img = Image.new("RGB", (SIZE, SIZE), "#FFF8E1")
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((8, 8, SIZE - 8, SIZE - 8), radius=48, outline="#FFB300", width=10)
        size = 300 if len(text) <= 2 else 200 if len(text) == 3 else 150
        try:
            font = ImageFont.truetype("arialbd.ttf", size)
        except OSError:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", size)
        d.text((SIZE / 2, SIZE / 2), text, fill="#E65100", font=font, anchor="mm")
        img.save(dest, quality=90)

    def _get(self, url, params):
        for attempt in range(4):
            r = self.session.get(url, params={**params, "format": "json", "formatversion": 2}, timeout=30)
            if r.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        r.raise_for_status()

    def _page_images(self, titles, slugs):
        """Wikipedia article title -> lead image file name (free images only)."""
        found = {}
        for i in range(0, len(titles), 50):
            chunk = titles[i:i + 50]
            data = self._get(API_WIKI, {"action": "query", "prop": "pageimages", "piprop": "name",
                                        "redirects": 1, "titles": "|".join(chunk)})
            q = data.get("query", {})
            alias = {n["from"]: n["to"] for n in q.get("normalized", []) + q.get("redirects", [])}
            by_title = {p["title"]: p.get("pageimage") for p in q.get("pages", [])}
            for t in chunk:
                final = alias.get(alias.get(t, t), alias.get(t, t))
                if by_title.get(final):
                    found[t] = by_title[final]
        return {s: found[t] for s, t in zip(slugs, titles) if t in found}

    def _file_info(self, files):
        info = {}
        files = sorted(f for f in files if f)
        for i in range(0, len(files), 50):
            chunk = files[i:i + 50]
            data = self._get(API_COMMONS, {"action": "query", "prop": "imageinfo", "iiprop": "url|extmetadata",
                                           "iiurlwidth": SIZE, "titles": "|".join(f"File:{f}" for f in chunk)})
            q = data.get("query", {})
            alias = {n["to"]: n["from"] for n in q.get("normalized", [])}
            for p in q.get("pages", []):
                ii = (p.get("imageinfo") or [None])[0]
                if not ii:
                    continue
                meta = ii.get("extmetadata", {})
                name = alias.get(p["title"], p["title"]).removeprefix("File:")
                info[name.replace(" ", "_")] = info[name] = {
                    "thumb": ii.get("thumburl") or ii["url"],
                    "page": ii.get("descriptionurl", ""),
                    "license": _plain(meta.get("LicenseShortName", {}).get("value")),
                    "author": _plain(meta.get("Artist", {}).get("value")) or "không rõ",
                }
        return info

    def _download(self, url, dest):
        r = self.session.get(url, timeout=60)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content))
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            bg = Image.new("RGB", img.size, "white")
            bg.paste(img, mask=img.split()[-1])
            img = bg
        img = img.convert("RGB")
        img.thumbnail((SIZE, SIZE))
        img.save(dest, "JPEG", quality=82, optimize=True)
