import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.learning.models import PersonalWord
from apps.vocab.models import Language, ReviewStatus, Word, WordTranslation

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup(db):
    for code in ("vi", "en", "zh-Hans", "zh-Hant"):
        Language.objects.create(code=code, name=code, native_name=code, tts_locale=code)
    cat = Word.objects.create(slug="cat", yolo_label="cat")
    WordTranslation.objects.create(word=cat, language_id="vi", text="con mèo", status=ReviewStatus.VERIFIED)
    WordTranslation.objects.create(word=cat, language_id="en", text="cat", status=ReviewStatus.VERIFIED)
    user = User.objects.create_user("d@example.com", "Strong!Pass123", active_language="en")
    c = APIClient()
    c.force_authenticate(user)
    return user, c, cat


def test_log_on_device_and_confirm(setup):
    user, c, cat = setup
    res = c.post("/api/v1/detections/log/", {"model_name": "yolov10n-tflite", "inference_ms": 85, "items": [
        {"label": "cat", "confidence": 0.91, "bbox": [0.1, 0.1, 0.5, 0.6]},
        {"label": "dog", "confidence": 0.33, "bbox": [0.5, 0.5, 0.9, 0.9],
         "top_k": [{"label": "dog", "confidence": 0.33}, {"label": "cat", "confidence": 0.30}]},
    ]}, format="json")
    assert res.status_code == 201
    items = {i["label"]: i for i in res.data["items"]}
    assert items["cat"]["card"]["target"]["text"] == "cat" and items["dog"]["card"] is None
    res = c.post(f"/api/v1/detections/{res.data['id']}/confirm/", {"items": [
        {"id": items["cat"]["id"], "selected": True, "feedback": "correct"},
        {"id": items["dog"]["id"], "selected": False, "feedback": "wrong", "corrected_label": "cat"},
    ]}, format="json")
    assert res.data["saved"] == 1
    assert PersonalWord.objects.get(user=user, word=cat).source == "camera"
    from apps.gamification.models import UserStats
    assert UserStats.objects.get(user=user).detections == 1

    staff = User.objects.create_user("s@example.com", "Strong!Pass123", role="staff")
    s = APIClient()
    s.force_authenticate(staff)
    stats = s.get("/api/v1/admin/detections/stats/").data
    assert stats["confusion"] == [{"label": "dog", "corrected_label": "cat", "count": 1}]
