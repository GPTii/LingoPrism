""""It is something else": the learner types the object's name in Vietnamese and gets the word in the language they
learn – from the checked dictionary only (no machine translation: a wrong word would be taught).

"cái ly", "ly", "Ly" and "ly" without accents ("ly", "coc") all find the dictionary's words. Ranking:
  0  the same name, classifier left out ("cái cốc" = "cốc")
  1  the typed name is a whole part of the word ("ly" -> "ly rượu")
  2  the word is a whole part of what was typed ("cốc thuỷ tinh" -> "cái cốc")
  3  the same name, accents ignored (typed without a Vietnamese keyboard: "coc" -> "cốc")
  4  part of the name, when nothing was typed with accents
Words the detector knows (yolo_label) come first among equals: a correction to them also teaches the detector.
"""
import re
import unicodedata

from django.core.cache import cache

from apps.vocab.models import ReviewStatus, Word, WordTranslation
from apps.vocab.services import words_for_target

CLASSIFIERS = {"cái", "con", "chiếc", "quả", "trái", "cây", "tờ", "cuốn", "quyển", "tấm", "đôi", "bộ", "chú", "bông",
               "củ", "bức", "ngôi", "căn", "toà", "tòa", "lọ", "hũ"}
LIMIT = 6
_CACHE_KEY = "detection:lookup:vi:v1"


def norm(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "").lower()
    text = text.replace("òa", "oà").replace("óa", "oá").replace("ỏa", "oả").replace("õa", "oã").replace("ọa", "oạ")
    text = text.replace("òe", "oè").replace("óe", "oé").replace("ủy", "uỷ").replace("úy", "uý").replace("ùy", "uỳ")
    return " ".join(re.sub(r"[^\w\s]", " ", text).split())


def core(text: str) -> str:
    words = text.split()
    while len(words) > 1 and words[0] in CLASSIFIERS:
        words = words[1:]
    return " ".join(words)


def plain(text: str) -> str:
    text = unicodedata.normalize("NFD", text.replace("đ", "d"))
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def _contains(outer: str, inner: str) -> bool:
    return f" {inner} " in f" {outer} "


def _index() -> list[tuple[int, str, str, bool, bool]]:
    """(word id, normalised name, the same without accents, detector knows it, noun) for every checked word."""
    rows = cache.get(_CACHE_KEY)
    if rows is None:
        rows = []
        for wid, text, variants, yolo, pos in WordTranslation.objects.filter(
                language_id="vi", status=ReviewStatus.VERIFIED).values_list(
                "word_id", "text", "accepted_variants", "word__yolo_label", "word__part_of_speech"):
            for name in {text, *(variants or [])}:
                n = core(norm(name))
                if n:
                    rows.append((wid, n, plain(n), bool(yolo), pos == Word.PartOfSpeech.NOUN))
        cache.set(_CACHE_KEY, rows, 600)
    return rows


def rank(query: str) -> list[int]:
    q = core(norm(query))
    if not q:
        return []
    qp = plain(q)
    best: dict[int, tuple] = {}
    for wid, name, name_plain, known, noun in _index():
        if name == q:
            score = 0
        elif _contains(name, q):
            score = 1
        elif _contains(q, name):
            score = 2
        elif name_plain == qp:
            score = 3
        elif q == qp and len(qp) >= 4 and (_contains(name_plain, qp) or _contains(qp, name_plain)):
            score = 4  # typed without any accent: "dien thoai" -> "điện thoại di động"
        else:
            continue
        key = (score, not known, not noun, len(name))
        if wid not in best or key < best[wid]:
            best[wid] = key
    return [wid for wid, _ in sorted(best.items(), key=lambda kv: kv[1])]


def find(user, target, query: str, limit: int = LIMIT) -> list[Word]:
    """Words for `query` the learner may see in the language they learn, best first."""
    ids = rank(query)[: limit * 3]
    words = {w.id: w for w in words_for_target(Word.objects.filter(id__in=ids), user, target)}
    return [words[i] for i in ids if i in words][:limit]


def label_of(word: Word) -> str:
    """The label a correction to `word` is stored under: the detector's class, else the word itself (a new class)."""
    return word.yolo_label or word.slug
