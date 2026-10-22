import json
from types import SimpleNamespace

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.detection.models import Detection, DetectionItem
from apps.vocab.models import Language, ReviewStatus, Word, WordTranslation

from . import generator
from .models import PhotoDialogue

pytestmark = pytest.mark.django_db


@pytest.fixture
def photo(db, settings):
    settings.ANTHROPIC_API_KEY = "test-key"
    settings.GEMINI_API_KEY = ""
    for code in ("vi", "en", "zh-Hans", "zh-Hant"):
        Language.objects.create(code=code, name=code, native_name=code, tts_locale=code)
    for slug, vi, hans in (("apple", "quả táo", "苹果"), ("cup", "cái cốc", "杯子")):
        w = Word.objects.create(slug=slug, yolo_label=slug)
        WordTranslation.objects.create(word=w, language_id="vi", text=vi, status=ReviewStatus.VERIFIED)
        WordTranslation.objects.create(word=w, language_id="zh-Hans", text=hans, status=ReviewStatus.VERIFIED)
    WordTranslation.objects.create(word=Word.objects.create(slug="dog", yolo_label="dog"), language_id="zh-Hans",
                                   text="狗", status=ReviewStatus.DRAFT)  # not verified: never given to the AI
    user = User.objects.create_user("t@example.com", "Strong!Pass123", active_language="zh", zh_script="hans")
    det = Detection.objects.create(user=user, model_name="test", device="server")
    DetectionItem.objects.create(detection=det, label="apple", confidence=0.9, selected=True)
    DetectionItem.objects.create(detection=det, label="dog", confidence=0.8, selected=True)
    DetectionItem.objects.create(detection=det, label="car", confidence=0.7, selected=True, feedback="wrong",
                                 corrected_label="cup")
    c = APIClient()
    c.force_authenticate(user)
    return user, c, det


@pytest.fixture
def claude(monkeypatch):
    """Stands in for the Anthropic client; records the request."""
    calls = []
    answer = {"title_vi": "Ở bếp", "lines": [
        {"speaker": "A", "text": "这个苹果很好吃。", "translation": "Quả táo này rất ngon."},
        {"speaker": "B", "text": "给我一个杯子。", "translation": "Đưa tôi một cái cốc."},
    ]}

    class Messages:
        def create(self, **kw):
            calls.append(kw)
            return SimpleNamespace(stop_reason="end_turn", model=kw["model"],
                                   content=[SimpleNamespace(type="text", text=json.dumps(answer, ensure_ascii=False))])

    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", lambda **kw: SimpleNamespace(beta=SimpleNamespace(messages=Messages())))
    return calls


def test_dialogue_uses_only_verified_words_and_is_kept(photo, claude):
    user, c, det = photo
    res = c.post(f"/api/v1/detections/{det.id}/dialogue/")
    assert res.status_code == 200, res.data
    assert res.data["ai_generated"] is True and res.data["language"] == "zh-Hans"
    assert [w["text"] for w in res.data["words"]] == ["苹果", "杯子"]  # dog: draft only; car → corrected to cup
    prompt = claude[0]["messages"][0]["content"]
    assert "苹果" in prompt and "杯子" in prompt and "狗" not in prompt
    assert claude[0]["output_config"]["format"]["type"] == "json_schema"
    assert res.data["lines"][0]["reading"] == "zhè ge píng guǒ hěn hǎo chī"  # pinyin computed here, not by the AI
    # a second request (or opening the photo again) does not call the AI again
    assert c.post(f"/api/v1/detections/{det.id}/dialogue/").data["id"] == res.data["id"]
    assert c.get(f"/api/v1/detections/{det.id}/dialogue/").status_code == 200
    assert len(claude) == 1 and PhotoDialogue.objects.count() == 1


def test_off_without_key_and_private_to_owner(photo, claude, settings):
    user, c, det = photo
    other = APIClient()
    other.force_authenticate(User.objects.create_user("o@example.com", "Strong!Pass123"))
    assert other.post(f"/api/v1/detections/{det.id}/dialogue/").status_code == 404
    settings.ANTHROPIC_API_KEY = ""
    assert c.get("/api/v1/ai/status/").data == {"dialogue": False}
    res = c.post(f"/api/v1/detections/{det.id}/dialogue/")
    assert res.status_code == 503 and claude == []
    assert c.get(f"/api/v1/detections/{det.id}/dialogue/").status_code == 404


def test_refusal_is_reported_not_saved(photo, monkeypatch):
    user, c, det = photo
    import anthropic

    class Messages:
        def create(self, **kw):
            return SimpleNamespace(stop_reason="refusal", model=kw["model"], content=[])

    monkeypatch.setattr(anthropic, "Anthropic", lambda **kw: SimpleNamespace(beta=SimpleNamespace(messages=Messages())))
    assert c.post(f"/api/v1/detections/{det.id}/dialogue/").status_code == 503
    assert not PhotoDialogue.objects.exists()
    assert generator.enabled()


def test_gemini_is_used_first_when_its_key_is_set(photo, settings, monkeypatch):
    user, c, det = photo
    settings.GEMINI_API_KEY = "g-key"
    settings.GEMINI_MODEL = "gemini-flash-latest"
    sent = []
    answer = {"title_vi": "Ở bếp", "lines": [{"speaker": "A", "text": "给我一个杯子。", "translation": "Đưa tôi một cái cốc."}]}

    def post(url, headers, json, timeout):
        sent.append((url, headers, json))
        return SimpleNamespace(status_code=200, json=lambda: {"modelVersion": "gemini-x", "candidates": [
            {"finishReason": "STOP", "content": {"parts": [{"text": __import__("json").dumps(answer, ensure_ascii=False)}]}}]})

    import requests
    monkeypatch.setattr(requests, "post", post)
    res = c.post(f"/api/v1/detections/{det.id}/dialogue/")
    assert res.status_code == 200, res.data
    url, headers, body = sent[0]
    assert "gemini-flash-latest:generateContent" in url and headers["x-goog-api-key"] == "g-key"
    assert body["generationConfig"]["responseJsonSchema"] == generator.SCHEMA
    assert "苹果" in body["contents"][0]["parts"][0]["text"]
    assert res.data["lines"][0]["reading"].startswith("gěi wǒ")  # pinyin still computed here
    assert PhotoDialogue.objects.get().model_name == "gemini-x"


def test_reading_puts_neutral_tones_back():
    from apps.vocab.lang.sources import neutral_tone_words

    if not neutral_tone_words():
        pytest.skip("CC-CEDICT not downloaded")
    assert generator._reading("杯子是妈妈的。", "zh-Hans") == "bēi zi shì mā ma de"
    assert generator._reading("是的，谢谢你！", "zh-Hans") == "shì de xiè xie nǐ"
    assert generator._reading("謝謝媽媽！", "zh-Hant") == "xiè xie mā ma"
    assert generator._reading("一个朋友不是什么人。", "zh-Hans") == "yí ge péng you bú shì shén me rén"
