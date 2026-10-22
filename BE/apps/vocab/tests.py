import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.vocab.lang import pinyin as py
from apps.vocab.lang import sources, vietnamese
from apps.vocab.lang.ipa import arpabet_to_ipa
from apps.vocab.models import Language, ReviewStatus, Topic, TopicWord, Word, WordTranslation

# ------------------------------------------------------------------ pure functions


@pytest.mark.parametrize("numbered, marked", [
    ("ma3 ling2 shu3", "mǎ líng shǔ"),
    ("lu:4 se4", "lǜ sè"),
    ("tou2 fa5", "tóu fa"),
    ("xiong2 mao1", "xióng māo"),
    ("gou3", "gǒu"),
    ("liu2", "liú"),
    ("gui4", "guì"),
])
def test_numbered_to_marked(numbered, marked):
    assert py.numbered_to_marked(numbered) == marked
    assert py.marked_to_numbered(marked) == numbered.replace("u:", "ü")


@pytest.mark.parametrize("numbered, zhuyin", [
    ("ma3 ling2 shu3", "ㄇㄚˇ ㄌㄧㄥˊ ㄕㄨˇ"),
    ("tou2 fa5", "ㄊㄡˊ ˙ㄈㄚ"),
    ("zhi1 zhu1", "ㄓ ㄓㄨ"),
    ("ju2 se4", "ㄐㄩˊ ㄙㄜˋ"),
    ("yu3", "ㄩˇ"),
    ("xiong2", "ㄒㄩㄥˊ"),
    ("wei2 bo1 lu2", "ㄨㄟˊ ㄅㄛ ㄌㄨˊ"),
    ("le4 se4", "ㄌㄜˋ ㄙㄜˋ"),
])
def test_zhuyin(numbered, zhuyin):
    assert py.numbered_to_zhuyin(numbered) == zhuyin


def test_ipa():
    assert arpabet_to_ipa("P AH0 T EY1 T OW2".split()) == "pəˈteɪtoʊ"
    assert arpabet_to_ipa("K AE1 T".split()) == "kæt"
    assert arpabet_to_ipa("T R AE1 F IH0 K | L AY1 T".split()) == "ˈtræfɪk laɪt"


@pytest.mark.parametrize("raw, expected", [
    ("hoà", "hòa"), ("thuỷ", "thủy"), ("khoẻ", "khỏe"), ("hoàn", "hoàn"), ("người", "người"),
    ("quý", "quý"), ("giỏ", "giỏ"), ("xoài", "xoài"), ("chuối", "chuối"), ("của", "của"),
])
def test_vietnamese_tone_placement(raw, expected):
    assert vietnamese.normalize(raw) == expected


# ------------------------------------------------------------------ golden tests (need source files)

needs_sources = pytest.mark.skipif(not sources.sources_available(), reason="chạy manage.py fetch_sources trước")


@needs_sources
@pytest.mark.parametrize("hans, hant, en, regional", [
    ("头发", "頭髮", ["hair"], False),
    ("面条", "麵條", ["noodles"], False),
    ("猫", "貓", ["cat"], False),
    ("土豆", "馬鈴薯", ["potato"], True),
    ("出租车", "計程車", ["taxi"], True),
])
def test_golden_pairs_verify(hans, hant, en, regional):
    from apps.vocab.lang import checks

    a = checks.build_zh_hans(hans, en, True, prefer_trad=hant)
    b = checks.build_zh_hant(hant, en, True, allow_network=False)
    assert checks.check_hans_hant_pair(a, b) is regional
    assert a["errors"] == [] and b["errors"] == []


@needs_sources
@pytest.mark.parametrize("hant, en", [("頭發", ["hair"]), ("面條", ["noodles"]), ("后面", ["back"]), ("猫", ["cat"])])
def test_golden_wrong_traditional_is_flagged(hant, en):
    from apps.vocab.lang import checks

    assert checks.build_zh_hant(hant, en, True, allow_network=False)["errors"]


@needs_sources
@pytest.mark.parametrize("hans, en", [("頭髮", ["hair"]), ("貓", ["cat"])])
def test_golden_traditional_in_simplified_field_is_flagged(hans, en):
    from apps.vocab.lang import checks

    assert checks.build_zh_hans(hans, en, True)["errors"]


@needs_sources
def test_golden_readings():
    from apps.vocab.lang import checks

    assert checks.build_zh_hans("银行", ["bank"], True)["pinyin"] == "yín háng"
    assert checks.build_zh_hans("垃圾", ["trash", "garbage"], False)["pinyin"] == "lā jī"
    tw = checks.build_zh_hant("垃圾", ["trash", "garbage"], False, allow_network=False)
    assert tw["pinyin"] == "lè sè" and tw["zhuyin"] == "ㄌㄜˋ ㄙㄜˋ"
    assert checks.build_zh_hant("頭髮", ["hair"], True, allow_network=False)["pinyin"] == "tóu fǎ"


# ------------------------------------------------------------------ API

pytestmark_db = pytest.mark.django_db


@pytest.fixture
def vocab(db):
    for code, tts in [("vi", "vi-VN"), ("en", "en-US"), ("zh-Hans", "zh-CN"), ("zh-Hant", "zh-TW")]:
        Language.objects.create(code=code, name=code, native_name=code, tts_locale=tts)
    topic = Topic.objects.create(slug="animals", name_vi="Động vật")
    cat = Word.objects.create(slug="cat", yolo_label="cat")
    dog = Word.objects.create(slug="dog", yolo_label="dog")
    for w in (cat, dog):
        TopicWord.objects.create(topic=topic, word=w)
    V = ReviewStatus.VERIFIED
    WordTranslation.objects.create(word=cat, language_id="vi", text="con mèo", status=V)
    WordTranslation.objects.create(word=cat, language_id="en", text="cat", ipa="kæt", status=V)
    WordTranslation.objects.create(word=cat, language_id="zh-Hans", text="猫", pinyin="māo", status=V)
    WordTranslation.objects.create(word=cat, language_id="zh-Hant", text="貓", pinyin="māo", zhuyin="ㄇㄠ", status=V)
    WordTranslation.objects.create(word=dog, language_id="vi", text="con chó", status=V)
    WordTranslation.objects.create(word=dog, language_id="en", text="dog", status=V)
    WordTranslation.objects.create(word=dog, language_id="zh-Hans", text="狗", status=V)
    WordTranslation.objects.create(word=dog, language_id="zh-Hant", text="狗X", status=ReviewStatus.FLAGGED)
    return topic


@pytest.fixture
def learner(db):
    user = User.objects.create_user("learner@example.com", "Strong!Pass123", active_language="zh", zh_script="hant")
    client = APIClient()
    client.force_authenticate(user)
    return user, client


def test_flagged_translations_are_hidden(vocab, learner):
    _, client = learner
    res = client.get(f"/api/v1/topics/{vocab.id}/words/")
    assert res.status_code == 200
    slugs = [c["slug"] for c in res.data["results"]]
    assert slugs == ["cat"]  # dog's zh-Hant is flagged → not shown to learners
    target = res.data["results"][0]["target"]
    assert target["text"] == "貓" and target["zhuyin"] == "ㄇㄠ" and target["tts_locale"] == "zh-TW"

    res = client.get(f"/api/v1/topics/{vocab.id}/words/?script=hans")
    assert sorted(c["slug"] for c in res.data["results"]) == ["cat", "dog"]


def test_topic_word_count_and_save(vocab, learner):
    _, client = learner
    topics = client.get("/api/v1/topics/").data["results"]
    assert topics[0]["word_count"] == 1
    res = client.post(f"/api/v1/topics/{vocab.id}/save/")
    assert res.data == {"added": 1, "total": 1}


def test_by_labels(vocab, learner):
    _, client = learner
    res = client.get("/api/v1/words/by-labels/?labels=cat,dog,unknown&lang=en")
    assert set(res.data) == {"cat", "dog"}
    assert res.data["cat"]["target"]["ipa"] == "kæt"


def test_error_reports_flag_after_threshold(vocab, db):
    tr = WordTranslation.objects.get(word__slug="cat", language_id="zh-Hant")
    for i in range(3):
        u = User.objects.create_user(f"u{i}@example.com", "Strong!Pass123")
        c = APIClient()
        c.force_authenticate(u)
        res = c.post("/api/v1/reports/", {"word": tr.word_id, "translation": tr.id, "reason": "wrong_character"}, format="json")
        assert res.status_code == 201
    tr.refresh_from_db()
    assert tr.status == ReviewStatus.FLAGGED


def test_admin_translation_verify(vocab, db):
    admin = User.objects.create_user("admin@example.com", "Strong!Pass123", role="admin")
    c = APIClient()
    c.force_authenticate(admin)
    tr = WordTranslation.objects.get(word__slug="dog", language_id="zh-Hant")
    res = c.patch(f"/api/v1/admin/translations/{tr.id}/", {"text": "狗"}, format="json")
    assert res.status_code == 200 and res.data["status"] == "flagged"
    res = c.post(f"/api/v1/admin/translations/{tr.id}/verify/")
    assert res.data["status"] == "verified" and res.data["verified_method"] == "manual"


# ---------------------------------------------------------------- example sentences (Tatoeba)



@needs_sources
def test_sentence_segmentation_and_pinyin():
    from apps.vocab.lang import sentences as sl

    s = sl.build_zh("我们试试看！", "hans", "Wo3men5 shi4shi5 kan4!", reviewed=True)
    assert not s.errors
    assert [t["t"] for t in s.tokens][0] == "我们"
    assert s.tokens[0]["p"] == "wǒ men" and s.tokens[-1] == {"t": "！", "x": 1}

    t = sl.build_zh("這隻貓很可愛。", "hant", "Zhe4 zhi1 mao1 hen3 ke3ai4.", reviewed=True)
    assert not t.errors and any(tok.get("z") == "ㄇㄠ" for tok in t.tokens)


@needs_sources
@pytest.mark.parametrize("text,script", [
    ("你在圣誕節去教堂嗎？", "hant"),  # 圣 is the simplified form of 聖
    ("他看着我。", "hant"),            # Taiwan writes 著
    ("我們去學校。", "hans"),
])
def test_sentence_mixed_script_is_flagged(text, script):
    from apps.vocab.lang import sentences as sl

    pin = " ".join(["a1"] * sl.han_count(text))
    assert any("thể trong câu" in e for e in sl.build_zh(text, script, pin, reviewed=True).errors)


@needs_sources
def test_sentence_pinyin_mismatch_is_flagged():
    from apps.vocab.lang import sentences as sl

    assert sl.build_zh("我们试试看！", "hans", "Wo3men5 shi4shi5 kan1!", reviewed=False).errors
    assert sl.build_zh("我们试试看", "hans", "Wo3men5 shi4", reviewed=True).errors  # syllable count


def test_latin_tokens_and_spans():
    from apps.vocab.lang import sentences as sl

    toks = sl.tokens_latin("We're near the traffic light.", "en")
    assert [t["t"] for t in toks] == ["We're", "near", "the", "traffic", "light", "."]
    assert sl.word_spans(toks, "traffic light", "en") == [3, 4]
    vi = sl.tokens_latin("Ra bãi biển đi lối nào?", "vi")
    assert sl.word_spans(vi, "bãi biển", "vi") == [1, 2]
    assert sl.normalize_answer("We're near  the traffic light!") == sl.normalize_answer("we're near the traffic light")


def test_word_images_are_reviewed_free_and_present():
    """Every word photo was looked at by a person, is freely licensed and credited (seed/concepts/images.csv)."""
    import csv

    from apps.vocab.management.commands.fetch_word_images import FREE

    with open(sources.SEED_DIR / "concepts" / "words.csv", encoding="utf-8") as fh:
        slugs = {r["slug"] for r in csv.DictReader(fh)}
    with open(sources.SEED_DIR / "concepts" / "images.csv", encoding="utf-8") as fh:
        rows = {r["slug"]: r for r in csv.DictReader(fh)}
    assert set(rows) == slugs
    for slug, r in rows.items():
        assert r["status"] in ("verified", "none"), slug
        photo = sources.SEED_DIR / "images" / f"{slug}.jpg"
        if r["status"] == "none":
            assert not photo.exists(), slug
            continue
        assert photo.exists(), slug
        assert FREE.match(r["license"]), (slug, r["license"])
        assert r["author"], slug
        assert r["source_url"].startswith("https://commons.wikimedia.org/") or r["license"] == "CC0", slug


def test_candidate_queue_needs_review_and_checks(db, tmp_path, monkeypatch):
    """A suggested word is only added after a teacher fixes it and it passes the same source checks as the seed."""
    from apps.vocab import candidates
    from apps.vocab.models import WordCandidate

    monkeypatch.setattr(candidates, "APPROVED_CSV", tmp_path / "approved.csv")
    for code in ("vi", "en", "zh-Hans", "zh-Hant"):
        Language.objects.get_or_create(code=code, defaults={"name": code, "native_name": code, "tts_locale": code})
    Topic.objects.create(slug="time", name_vi="Thời gian")
    staff = User.objects.create_user("t@example.com", "Strong!Pass123", role="staff")
    c = WordCandidate.objects.create(zh_hans="半夜", zh_hant="半夜", pinyin="bàn yè", hsk_level=2,
                                     glosses=["midnight", "in the middle of the night"], en="midnight", vi="")
    client = APIClient()
    client.force_authenticate(staff)
    res = client.post(f"/api/v1/admin/candidates/{c.id}/approve/")
    assert res.status_code == 400 and "nghĩa tiếng Việt" in res.data["detail"] and "chủ đề" in res.data["detail"]
    assert not Word.objects.exists()

    client.patch(f"/api/v1/admin/candidates/{c.id}/", {"vi": "nửa đêm", "topics": "time"}, format="json")
    res = client.post(f"/api/v1/admin/candidates/{c.id}/approve/")
    assert res.status_code == 200 and res.data["status"] == "approved"
    word = Word.objects.get(slug="midnight")
    assert set(word.translations.values_list("language_id", "status")) == {
        ("vi", "verified"), ("en", "verified"), ("zh-Hans", "verified"), ("zh-Hant", "verified")}
    assert word.levels["zh"] == 2 and "半夜" in (tmp_path / "approved.csv").read_text(encoding="utf-8")
