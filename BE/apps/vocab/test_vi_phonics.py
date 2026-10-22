"""Golden tests for Vietnamese early-literacy orthography (âm đầu + vần + thanh, đánh vần, chính tả)."""
import pytest

from apps.vocab.lang import vi_phonics as ph


@pytest.mark.parametrize("text,onset,rhyme,tone", [
    ("bà", "b", "a", "huyen"), ("cá", "c", "a", "sac"), ("quả", "qu", "a", "hoi"), ("của", "c", "ua", "hoi"),
    ("gà", "g", "a", "huyen"), ("ghế", "gh", "ê", "sac"), ("nghỉ", "ngh", "i", "hoi"), ("ngã", "ng", "a", "nga"),
    ("gì", "gi", "i", "huyen"), ("gìn", "gi", "in", "huyen"), ("gia", "gi", "a", "ngang"), ("giếng", "gi", "iêng", "sac"),
    ("giường", "gi", "ương", "huyen"), ("ăn", "", "ăn", "ngang"), ("ổi", "", "ôi", "hoi"), ("khỏe", "kh", "oe", "hoi"),
    ("hòa", "h", "oa", "huyen"), ("thuyền", "th", "uyên", "huyen"), ("quyển", "qu", "yên", "hoi"), ("đẹp", "đ", "ep", "nang"),
    ("nhà", "nh", "a", "huyen"), ("trường", "tr", "ương", "huyen"), ("Mẹ", "m", "e", "nang"),
])
def test_parse_and_compose_roundtrip(text, onset, rhyme, tone):
    s = ph.parse(text)
    assert (s.onset, s.rhyme, s.tone) == (onset, rhyme, tone)
    assert s.text == text.lower()


@pytest.mark.parametrize("onset,rhyme,expected", [
    ("c", "e", "k"), ("c", "i", "k"), ("k", "a", "c"), ("g", "ê", "gh"), ("gh", "a", "g"),
    ("ng", "e", "ngh"), ("ngh", "o", "ng"), ("c", "a", None), ("k", "ê", None), ("ngh", "iêng", None), ("qu", "a", None),
])
def test_spelling_rules(onset, rhyme, expected):
    assert ph.spelling_error(onset, rhyme) == expected


@pytest.mark.parametrize("text,steps", [
    ("bà", ["bờ", "a", "ba", "huyền", "bà"]),
    ("ba", ["bờ", "a", "ba"]),
    ("ổi", ["ôi", "hỏi", "ổi"]),
    ("quả", ["quờ", "a", "qua", "hỏi", "quả"]),
    ("kẹo", ["ca", "eo", "keo", "nặng", "kẹo"]),
])
def test_spell(text, steps):
    assert ph.spell(text) == steps


def test_spell_rhyme():
    assert ph.spell_rhyme("an") == ["a", "nờ", "an"]
    assert ph.spell_rhyme("ăm") == ["á", "mờ", "ăm"]
    assert ph.spell_rhyme("anh") == ["a", "nhờ", "anh"]
    assert ph.spell_rhyme("a") == ["a"]


def test_invalid():
    assert ph.parse("ngh") is None and ph.parse("qu") is None and ph.parse("") is None
