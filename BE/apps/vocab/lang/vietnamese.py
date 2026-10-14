"""Vietnamese text normalization: NFC + one consistent tone-mark placement ("kiểu cũ": hòa, thủy, khỏe)."""
import re
import unicodedata

TONES = {
    "̀": "huyền", "́": "sắc", "̃": "ngã", "̉": "hỏi", "̣": "nặng",
}
_TONE_RE = re.compile("[" + "".join(TONES) + "]")
VALID_LETTERS = re.compile(r"^[a-zàáảãạăằắẳẵặâầấẩẫậbcdđeèéẻẽẹêềếểễệghiìíỉĩịklmnoòóỏõọôồốổỗộơờớởỡợpqrstuùúủũụưừứửữựvxyỳýỷỹỵ]+$")


def _split_tone(syllable: str) -> tuple[str, str | None]:
    decomposed = unicodedata.normalize("NFD", syllable)
    tone = None
    chars = []
    for ch in decomposed:
        if ch in TONES:
            tone = ch
        else:
            chars.append(ch)
    return unicodedata.normalize("NFC", "".join(chars)), tone


def _apply_tone(base: str, tone: str | None) -> str:
    if not tone:
        return base
    lower = base.lower()
    vowels = "aăâeêioôơuưy"
    idx = [i for i, ch in enumerate(lower) if ch in vowels]
    if not idx:
        return base
    # 'qu' and 'gi' – the u / i belongs to the consonant
    if lower.startswith("qu") and len(idx) > 1 and idx[0] == 1:
        idx = idx[1:]
    elif lower.startswith("gi") and len(idx) > 1 and idx[0] == 1:
        idx = idx[1:]
    target = idx[0]
    special = [i for i in idx if lower[i] in "ăâêôơư"]
    if special:
        target = special[-1] if lower[special[-1]] == "ơ" and len(special) > 1 else special[0]
    elif len(idx) >= 2:
        ends_with_vowel = idx[-1] == len(lower) - 1
        if len(idx) == 3:
            target = idx[1]
        elif ends_with_vowel:
            target = idx[0]  # kiểu cũ: hòa, thủy, mía, mùa
        else:
            target = idx[1]  # hoàn, thuyền
    ch = unicodedata.normalize("NFD", base[target])
    return unicodedata.normalize("NFC", base[:target] + ch + tone + base[target + 1:])


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text.strip())

    def fix(m: re.Match) -> str:
        word = m.group(0)
        base, tone = _split_tone(word)
        return _apply_tone(base, tone)

    return re.sub(r"[^\W\d_]+", fix, text)


def problems(text: str) -> list[str]:
    issues = []
    if text != unicodedata.normalize("NFC", text):
        issues.append("vi: chưa chuẩn hoá Unicode NFC")
    if normalize(text) != text:
        issues.append(f"vi: vị trí dấu thanh không thống nhất (chuẩn: {normalize(text)})")
    for syl in re.findall(r"[^\W\d_]+", text.lower()):
        if not VALID_LETTERS.match(syl):
            issues.append(f"vi: âm tiết có ký tự lạ: {syl}")
        if len(_TONE_RE.findall(unicodedata.normalize("NFD", syl))) > 1:
            issues.append(f"vi: âm tiết có nhiều hơn một dấu thanh: {syl}")
    return issues
