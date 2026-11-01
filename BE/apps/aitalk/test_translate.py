import json
from types import SimpleNamespace

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.vocab.models import Language, ReviewStatus, Word, WordTranslation

from . import translator

pytestmark = pytest.mark.django_db


@pytest.fixture
def client(db, settings):
    settings.GEMINI_API_KEY = "g-key"
    settings.ANTHROPIC_API_KEY = ""
    for code in ("vi", "en", "zh-Hans", "zh-Hant"):
        Language.objects.create(code=code, name=code, native_name=code, tts_locale=code)
    for slug, vi, en, hans in (("apple", "quả táo", "apple", "苹果"), ("ice-cream", "kem", "ice cream", "冰淇淋")):
        w = Word.objects.create(slug=slug)
        WordTranslation.objects.create(word=w, language_id="vi", text=vi, status=ReviewStatus.VERIFIED)
        WordTranslation.objects.create(word=w, language_id="en", text=en, status=ReviewStatus.VERIFIED)
        WordTranslation.objects.create(word=w, language_id="zh-Hans", text=hans, pinyin="x",
                                       status=ReviewStatus.VERIFIED)
    WordTranslation.objects.create(word=Word.objects.create(slug="like"), language_id="zh-Hans", text="喜欢",
                                   status=ReviewStatus.DRAFT)  # not verified: never offered
    c = APIClient()
    c.force_authenticate(User.objects.create_user("t@example.com", "Strong!Pass123"))
    return c


@pytest.fixture
def gemini(monkeypatch):
    """Answers every request with `answer["text"]`; records the requests."""
    calls, answer = [], {"text": "我喜欢苹果和冰淇淋。"}

    def post(url, headers=None, json=None, timeout=None):
        calls.append(json)
        body = {"modelVersion": "gemini-x", "candidates": [{"finishReason": "STOP", "content": {"parts": [
            {"text": _dumps({"translation": answer["text"]})}]}}]}
        return SimpleNamespace(status_code=200, json=lambda: body, text="")

    import requests
    monkeypatch.setattr(requests, "post", post)
    return calls, answer


def _dumps(obj):
    return json.dumps(obj, ensure_ascii=False)


def test_translates_with_pinyin_and_offers_only_verified_words(client, gemini):
    calls, _ = gemini
    res = client.post("/api/v1/translate/", {"text": "Tôi thích táo và kem", "source": "vi", "target": "zh-Hans"},
                      format="json")
    assert res.status_code == 200, res.data
    assert res.data["translation"] == "我喜欢苹果和冰淇淋。" and res.data["machine_translated"] is True
    assert res.data["reading"] == "wǒ xǐ huan píng guǒ hé bīng qí lín"  # computed here, not by the AI
    assert res.data["target_tts"] == "zh-CN" and res.data["source_reading"] == ""
    assert [w["text"] for w in res.data["words"]] == ["苹果", "冰淇淋"]  # 喜欢 is only a draft
    assert res.data["words"][0]["meaning_vi"] == "quả táo" and res.data["words"][0]["script"] == "hans"
    assert "Simplified" in calls[0]["contents"][0]["parts"][0]["text"]


def test_english_words_are_matched_as_phrases(client, gemini):
    gemini[1]["text"] = "I love Ice Cream and apples."
    res = client.post("/api/v1/translate/", {"text": "Tôi yêu kem", "source": "vi", "target": "en"}, format="json")
    assert res.status_code == 200, res.data
    assert [w["text"] for w in res.data["words"]] == ["ice cream"]  # "apples" ≠ "apple": no guessing
    assert res.data["reading"] == ""


@pytest.mark.parametrize("body", [
    {"text": "hi", "source": "en", "target": "en"},
    {"text": "苹果", "source": "zh-Hans", "target": "zh-Hant"},  # giản ↔ phồn is not a translation
    {"text": "hi", "source": "en", "target": "fr"},
    {"text": "   ", "source": "en", "target": "vi"},
    {"text": "a" * (translator.MAX_CHARS + 1), "source": "en", "target": "vi"},
])
def test_rejects_bad_requests_without_calling_the_ai(client, gemini, body):
    assert client.post("/api/v1/translate/", body, format="json").status_code == 400
    assert gemini[0] == []


def test_wrong_script_is_refused(client, gemini, monkeypatch):
    monkeypatch.setattr(translator, "wrong_script", lambda text, lang: lang == "zh-Hans")
    res = client.post("/api/v1/translate/", {"text": "táo", "source": "vi", "target": "zh-Hans"}, format="json")
    assert res.status_code == 503


def test_off_without_key(client, gemini, settings):
    settings.GEMINI_API_KEY = ""
    res = client.post("/api/v1/translate/", {"text": "táo", "source": "vi", "target": "en"}, format="json")
    assert res.status_code == 503 and gemini[0] == []
    assert client.get("/api/v1/ai/status/").data["translate"] is False


def test_wrong_script_uses_cedict():
    pytest.importorskip("pypinyin")
    try:
        from apps.vocab.lang.sources import cedict
        cedict()
    except FileNotFoundError:
        pytest.skip("CC-CEDICT not downloaded")
    assert translator.wrong_script("馬鈴薯", "zh-Hans") and not translator.wrong_script("马铃薯", "zh-Hans")
    assert translator.wrong_script("头发", "zh-Hant") and not translator.wrong_script("頭髮", "zh-Hant")


def test_chat_composer_can_leave_the_source_to_the_model(client, gemini):
    calls, answer = gemini
    answer["text"] = "我叫兰。"
    res = client.post("/api/v1/translate/", {"text": "Tôi tên Lan", "source": "auto", "target": "zh-Hans"},
                      format="json")
    assert res.status_code == 200, res.data
    assert res.data["translation"] == "我叫兰。" and res.data["reading"] == "wǒ jiào lán"
    assert res.data["source_tts"] == "" and res.data["source_reading"] == ""
    assert "Detect the language" in calls[0]["contents"][0]["parts"][0]["text"]
    assert client.post("/api/v1/translate/", {"text": "hi", "source": "en", "target": "auto"},
                       format="json").status_code == 400  # auto is a source only


def test_auto_does_not_turn_one_chinese_script_into_the_other(client, gemini):
    pytest.importorskip("pypinyin")
    try:
        from apps.vocab.lang.sources import cedict
        cedict()
    except FileNotFoundError:
        pytest.skip("CC-CEDICT not downloaded")
    res = client.post("/api/v1/translate/", {"text": "我的頭髮", "source": "auto", "target": "zh-Hans"},
                      format="json")
    assert res.status_code == 400 and gemini[0] == []
