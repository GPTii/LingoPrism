"""Automated cross-checking of vocabulary data against authoritative sources (PLAN.md §3b).

Each builder returns a dict with the fields of a WordTranslation plus:
  errors   – blocking problems → status "flagged" (hidden from learners)
  warnings – informational (shown in the admin review queue, do not block)
"""
import re
import unicodedata

from . import pinyin as py
from . import sources, vietnamese
from .ipa import arpabet_to_ipa

HAN_RE = re.compile(r"[一-鿿㐀-䶿\U00020000-\U0002a6df]")
COMPAT_RE = re.compile(r"[豈-﫿\U0002f800-\U0002fa1f]")


def unicode_issues(text: str, label: str) -> list[str]:
    issues = []
    if text != unicodedata.normalize("NFC", text):
        issues.append(f"{label}: chưa chuẩn hoá Unicode NFC")
    if COMPAT_RE.search(text):
        issues.append(f"{label}: chứa CJK Compatibility Ideograph (thường do copy-paste)")
    if label.startswith("zh"):
        bad = [ch for ch in text if not HAN_RE.match(ch)]
        if bad:
            issues.append(f"{label}: chứa ký tự không phải chữ Hán: {''.join(bad)!r}")
    return issues


def gloss_matches(glosses: list[str], terms: list[str]) -> bool:
    blob = " / ".join(glosses).lower()
    for term in terms:
        t = re.escape(term.lower().strip())
        if t and re.search(rf"(?<![a-z]){t}(e?s)?(?![a-z])", blob):
            return True
    return False


def _relevant(entries, terms):
    return [e for e in entries if gloss_matches(e.glosses, terms)]


_WEAK = ("(literary)", "(old)", "(archaic)", "variant of", "used in", "old variant", "(dialect)", "surname")


def _entry_score(entry, terms) -> tuple:
    """Lower is better: first matching gloss position, penalising literary/variant senses."""
    for i, g in enumerate(entry.glosses):
        if gloss_matches([g], terms):
            weak = any(w in g.lower() for w in _WEAK)
            return (1 if weak else 0, i)
    return (9, 99)


def _best_reading(matching, terms):
    ranked = sorted(matching, key=lambda e: _entry_score(e, terms))
    best = _entry_score(ranked[0], terms)
    top = {e.pinyin for e in ranked if _entry_score(e, terms) == best}
    return top, ranked


def _pypinyin(text: str) -> str:
    from pypinyin import Style, pinyin

    return " ".join(p[0] for p in pinyin(text, style=Style.TONE3, neutral_tone_with_five=True)).replace("v", "ü")


def _same_ignoring_neutral(a: str, b: str) -> bool:
    sa, sb = py.syllables(a), py.syllables(b)
    if len(sa) != len(sb):
        return False
    for x, y in zip(sa, sb):
        if x == y:
            continue
        if x[:-1] == y[:-1] and ("5" in (x[-1], y[-1])):
            continue
        return False
    return True


# ---------------------------------------------------------------- zh-Hans (mainland)

def build_zh_hans(text: str, en_terms: list[str], is_noun: bool, prefer_trad: str = "") -> dict:
    ced, hsk_ = sources.cedict(), sources.hsk()
    text = unicodedata.normalize("NFC", text.strip())
    out = {"text": text, "errors": unicode_issues(text, "zh-Hans"), "warnings": [], "sources": {}}

    leaked = sorted({ch for ch in text if ch in ced.traditional_only})
    if leaked:
        out["errors"].append(f"zh-Hans: lẫn chữ phồn thể: {''.join(leaked)}")

    entries = ced.by_simp.get(text, [])
    out["sources"]["cedict"] = [{"trad": e.traditional, "pinyin": e.pinyin, "glosses": e.glosses[:6]} for e in entries]
    if not entries:
        out["errors"].append("zh-Hans: không có trong CC-CEDICT")
        return out
    matching = _relevant(entries, en_terms)
    if not matching:
        out["errors"].append(f"zh-Hans: nghĩa trong CC-CEDICT không khớp với '{en_terms[0]}'")
        return out
    # Same simplified form can map to several traditional forms (球 ← 球 / 毬): prefer the one
    # matching the chosen zh-Hant word, then the identical form.
    same_trad = [e for e in matching if e.traditional == prefer_trad] or [e for e in matching if e.traditional == text]
    if same_trad:
        matching = same_trad

    hsk_forms = hsk_.readings(text)
    hsk_numeric = {py.normalize_numbered(f["transcriptions"]["numeric"]) for f in hsk_forms}
    out["sources"]["hsk"] = sorted(hsk_numeric)
    readings = {e.pinyin for e in matching}
    if len(readings) > 1:
        preferred = readings & hsk_numeric
        if len(preferred) != 1:
            preferred, _ = _best_reading(matching, en_terms)
        if len(preferred) == 1:
            out["warnings"].append(
                f"zh-Hans: có nhiều cách đọc ({', '.join(sorted(readings))}), chọn '{next(iter(preferred))}' theo nghĩa '{en_terms[0]}'"
            )
            readings = set(preferred)
        else:
            out["errors"].append(f"zh-Hans: nhiều cách đọc, cần chọn: {', '.join(sorted(readings))}")
            return out
    numbered = readings.pop()
    entry = next(e for e in matching if e.pinyin == numbered)

    if len(py.syllables(numbered)) != len(text):
        out["errors"].append(f"zh-Hans: số âm tiết pinyin ({numbered}) khác số chữ")
    if hsk_numeric and numbered not in hsk_numeric and not any(_same_ignoring_neutral(numbered, h) for h in hsk_numeric):
        out["errors"].append(f"zh-Hans: pinyin CC-CEDICT ({numbered}) khác HSK ({', '.join(sorted(hsk_numeric))})")
    pp = _pypinyin(text)
    out["sources"]["pypinyin"] = pp
    if not _same_ignoring_neutral(numbered, pp):
        out["warnings"].append(f"zh-Hans: pypinyin đọc là '{pp}' (CC-CEDICT: '{numbered}')")

    measure = next((s for _, s, _ in entry.classifiers), "")
    if not measure:
        for f in hsk_forms:
            if f.get("classifiers"):
                measure = f["classifiers"][0]
                break
    if is_noun and not measure:
        out["warnings"].append("zh-Hans: chưa có lượng từ trong nguồn")
    if measure and any(ch in ced.traditional_only for ch in measure):
        out["errors"].append(f"zh-Hans: lượng từ '{measure}' là chữ phồn thể")

    out.update(
        pinyin=py.numbered_to_marked(numbered),
        pinyin_numbered=numbered,
        measure_word=measure,
        level=hsk_.level(text) or "",
        meaning_en=next((g for g in entry.glosses if gloss_matches([g], en_terms)), entry.glosses[0])[:255],
        cedict_traditional=entry.traditional,
    )
    return out


# ---------------------------------------------------------------- zh-Hant (Taiwan)

def _moe_reading(raw: str) -> str:
    raw = raw.split("（")[0].split("(")[0]
    return " ".join(raw.replace("　", " ").split())


def build_zh_hant(text: str, en_terms: list[str], is_noun: bool, allow_network: bool = True) -> dict:
    ced = sources.cedict()
    text = unicodedata.normalize("NFC", text.strip())
    out = {"text": text, "errors": unicode_issues(text, "zh-Hant"), "warnings": [], "sources": {}}

    leaked = sorted({ch for ch in text if ch in ced.simplified_only})
    if leaked:
        out["errors"].append(f"zh-Hant: lẫn chữ giản thể: {''.join(leaked)}")

    entries = ced.by_trad.get(text, [])
    out["sources"]["cedict"] = [{"simp": e.simplified, "pinyin": e.pinyin, "glosses": e.glosses[:6]} for e in entries]
    matching = _relevant(entries, en_terms)
    if not entries:
        out["errors"].append("zh-Hant: không có trong CC-CEDICT")
    elif not matching:
        out["errors"].append(f"zh-Hant: nghĩa trong CC-CEDICT không khớp với '{en_terms[0]}'")

    ced_readings = set()
    if matching:
        top, _ = _best_reading(matching, en_terms)
        for e in matching:
            if e.pinyin in top:
                ced_readings.add(py.normalize_numbered(e.taiwan_pinyin) if e.taiwan_pinyin else e.pinyin)

    moe = sources.moedict().lookup(text, allow_network=allow_network)
    out["sources"]["moedict"] = moe
    if not moe or not moe.get("heteronyms"):
        return _hant_by_characters(text, matching, ced_readings, is_noun, out, allow_network, en_terms)

    candidates = []
    for h in moe["heteronyms"]:
        reading = _moe_reading(h.get("pinyin", ""))
        if not reading:
            continue
        candidates.append((py.marked_to_numbered(reading), reading, h.get("bopomofo", "")))
    if not candidates:
        out["errors"].append("zh-Hant: moedict không có pinyin")
        return out

    chosen = None
    if len(candidates) == 1:
        chosen = candidates[0]
    else:
        exact = [c for c in candidates if c[0] in ced_readings]
        agree = exact or [c for c in candidates if any(_same_ignoring_neutral(c[0], r) for r in ced_readings)]
        if len(agree) >= 1 and len({c[0] for c in agree}) == 1:
            chosen = agree[0]
        elif agree and all(_same_ignoring_neutral(agree[0][0], c[0]) for c in agree):
            chosen = agree[0]  # variants differ only by neutral tone; MOE lists the standard reading first
        else:
            out["errors"].append("zh-Hant: moedict có nhiều cách đọc, cần chọn: " + ", ".join(c[1] for c in candidates))
            return out
    numbered, marked, bopomofo = chosen

    if ced_readings and not any(_same_ignoring_neutral(numbered, r) for r in ced_readings):
        out["warnings"].append(
            f"zh-Hant: cách đọc Đài Loan ({marked}) khác CC-CEDICT ({', '.join(sorted(ced_readings))}) – dùng theo Bộ GD Đài Loan"
        )
    if len(py.syllables(numbered)) != len(text):
        out["errors"].append(f"zh-Hant: số âm tiết pinyin ({marked}) khác số chữ")

    expected_zhuyin = py.numbered_to_zhuyin(numbered)
    zhuyin = py.normalize_zhuyin(bopomofo.split("（")[0])
    if expected_zhuyin is None:
        out["errors"].append(f"zh-Hant: không chuyển được pinyin '{marked}' sang Zhuyin")
    elif py.normalize_zhuyin(expected_zhuyin) != zhuyin:
        out["errors"].append(f"zh-Hant: Zhuyin moedict ({zhuyin}) khác Zhuyin sinh từ pinyin ({expected_zhuyin})")

    return _finish_hant(out, text, matching, is_noun, numbered, marked, zhuyin, en_terms)


def _finish_hant(out, text, matching, is_noun, numbered, marked, zhuyin, en_terms):
    ced = sources.cedict()
    entry = matching[0] if matching else None
    measure = next((t for t, _, _ in entry.classifiers), "") if entry else ""
    if is_noun and not measure:
        out["warnings"].append("zh-Hant: chưa có lượng từ trong nguồn")
    if measure and any(ch in ced.simplified_only for ch in measure):
        out["errors"].append(f"zh-Hant: lượng từ '{measure}' là chữ giản thể")

    out.update(
        pinyin=marked,
        pinyin_numbered=numbered,
        zhuyin=zhuyin,
        measure_word=measure,
        meaning_en=(next((g for g in entry.glosses if gloss_matches([g], en_terms)), entry.glosses[0])[:255] if entry else ""),
        cedict_simplified=entry.simplified if entry else "",
    )
    return out


def _hant_by_characters(text, matching, ced_readings, is_noun, out, allow_network, en_terms):
    """Compound not listed in the MOE dictionary: every character must exist in it with the
    reading CC-CEDICT gives for that position (cross-check of glyph + pronunciation per character)."""
    if not matching or len(ced_readings) != 1:
        out["errors"].append("zh-Hant: không có trong từ điển Bộ Giáo dục Đài Loan (moedict) và không đủ dữ liệu để kiểm tra từng chữ")
        return out
    numbered = next(iter(ced_readings))
    syls = py.syllables(numbered)
    if len(syls) != len(text):
        out["errors"].append(f"zh-Hant: số âm tiết pinyin ({numbered}) khác số chữ")
        return out
    zh_parts, chars_info = [], []
    for ch, syl in zip(text, syls):
        info = sources.moedict().lookup(ch, allow_network=allow_network)
        readings = [py.marked_to_numbered(_moe_reading(h.get("pinyin", ""))) for h in (info or {}).get("heteronyms", [])]
        chars_info.append({"char": ch, "moe_readings": readings})
        if not info:
            out["errors"].append(f"zh-Hant: chữ '{ch}' không có trong từ điển Bộ GD Đài Loan")
            continue
        ok = any(r == syl or (syl.endswith("5") and r[:-1] == syl[:-1]) for r in readings)
        if not ok:
            out["errors"].append(f"zh-Hant: chữ '{ch}' đọc '{syl}' không khớp từ điển Bộ GD ({', '.join(readings)})")
        zh_parts.append(py.numbered_to_zhuyin(syl) or "")
    out["sources"]["moedict_chars"] = chars_info
    if out["errors"]:
        return out
    out["warnings"].append("zh-Hant: từ ghép chưa có trong từ điển Bộ GD – đã đối chiếu từng chữ (mặt chữ + cách đọc)")
    return _finish_hant(out, text, matching, is_noun, numbered, py.numbered_to_marked(numbered), " ".join(zh_parts), en_terms)


def check_hans_hant_pair(hans: dict, hant: dict) -> bool:
    """Returns regional_difference and appends errors when the pair is inconsistent."""
    expected_trad = hans.get("cedict_traditional")
    if not expected_trad or not hant.get("text"):
        return False
    if expected_trad == hant["text"]:
        if hant.get("cedict_simplified") and hant["cedict_simplified"] != hans["text"]:
            hant["errors"].append(f"zh-Hant: dạng giản thể của '{hant['text']}' là '{hant['cedict_simplified']}', không phải '{hans['text']}'")
        return False
    # Different words: allowed only as a deliberate regional difference (e.g. 土豆 / 馬鈴薯),
    # both sides already verified independently against their own sources.
    hant["warnings"].append(
        f"Từ vùng khác nhau: đại lục '{hans['text']}' (phồn thể của nó: {expected_trad}) – Đài Loan '{hant['text']}'"
    )
    return True


# ---------------------------------------------------------------- English & Vietnamese

def build_en(text: str) -> dict:
    text = " ".join(text.strip().lower().split())
    out = {"text": text, "errors": [], "warnings": [], "sources": {}}
    if not re.fullmatch(r"[a-z][a-z' \-]*", text):
        out["errors"].append("en: chứa ký tự không hợp lệ")
        return out
    prons = sources.cmudict().lookup(text.replace("-", " "))
    if not prons:
        out["errors"].append("en: không có trong CMUdict")
        return out
    ipas = [arpabet_to_ipa(p) for p in prons]
    out["sources"]["cmudict"] = [" ".join(p) for p in prons]
    if len(set(ipas)) > 1:
        out["warnings"].append("en: có nhiều cách phát âm: " + ", ".join(f"/{i}/" for i in dict.fromkeys(ipas)))
    out["ipa"] = ipas[0]
    return out


def build_vi(text: str) -> dict:
    normalized = vietnamese.normalize(text)
    out = {"text": normalized, "errors": [], "warnings": [], "sources": {}}
    if normalized != unicodedata.normalize("NFC", text.strip()):
        out["warnings"].append(f"vi: đã chuẩn hoá '{text}' → '{normalized}'")
    out["errors"].extend(vietnamese.problems(normalized))
    return out
