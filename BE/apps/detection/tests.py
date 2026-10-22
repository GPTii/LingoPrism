from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.detection.inference import Box, EnsembleDetector, LabelVerifier
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
    # photo history: newest first, filtered by whether words were saved from the photo
    c.post("/api/v1/detections/log/", {"model_name": "m", "items": [{"label": "cat", "confidence": 0.9, "bbox": [0, 0, 1, 1]}]}, format="json")
    assert len(c.get("/api/v1/detections/").data["results"]) == 2
    saved = c.get("/api/v1/detections/?confirmed=1").data["results"]
    assert [d["confirmed"] for d in saved] == [True] and saved[0]["items"][1]["corrected_label"] == "cat"
    assert [d["confirmed"] for d in c.get("/api/v1/detections/?confirmed=0").data["results"]] == [False]
    from apps.gamification.models import UserStats
    assert UserStats.objects.get(user=user).detections == 1

    staff = User.objects.create_user("s@example.com", "Strong!Pass123", role="staff")
    s = APIClient()
    s.force_authenticate(staff)
    stats = s.get("/api/v1/admin/detections/stats/").data
    assert stats["confusion"] == [{"label": "dog", "corrected_label": "cat", "count": 1}]


def test_unsure_detection_offers_alternatives_and_saves_the_picked_word(setup):
    user, c, cat = setup
    pig = Word.objects.create(slug="pig", yolo_label="pig")
    WordTranslation.objects.create(word=pig, language_id="en", text="pig", status=ReviewStatus.VERIFIED)
    res = c.post("/api/v1/detections/log/", {"model_name": "t", "items": [
        {"label": "cat", "confidence": 0.44, "bbox": [0.1, 0.1, 0.5, 0.6],
         "top_k": [{"label": "cat", "confidence": 0.44}, {"label": "pig", "confidence": 0.31},
                   {"label": "cow", "confidence": 0.2}]},  # cow: no verified word -> not offered
    ]}, format="json")
    item = res.data["items"][0]
    assert item["uncertain"] is True
    assert [(a["label"], a["card"]["target"]["text"]) for a in item["alternatives"]] == [("pig", "pig")]
    res = c.post(f"/api/v1/detections/{res.data['id']}/confirm/", {"items": [
        {"id": item["id"], "selected": True, "feedback": "unknown", "corrected_label": "pig"},
    ]}, format="json")
    assert res.data["saved"] == 1
    assert PersonalWord.objects.filter(user=user, word=pig).exists()
    assert not PersonalWord.objects.filter(user=user, word=cat).exists()
    saved = res.data["items"][0]
    assert saved["feedback"] == "wrong" and saved["corrected_card"]["target"]["text"] == "pig"

class _FakeDetector:
    def __init__(self, classes, boxes):
        self.classes, self.boxes, self.name = classes, boxes, "fake"

    def predict(self, image):
        return [Box(b.label, b.confidence, list(b.bbox), list(b.top_k)) for b in self.boxes], 1


def _box(label, conf, bbox=(0.1, 0.1, 0.6, 0.6)):
    return Box(label, conf, list(bbox), [{"label": label, "confidence": conf}])


def test_ensemble_drops_base_guess_for_class_it_never_learned():
    # COCO has no "tiger" and calls it a zebra with high confidence – the box must not reach the learner
    base = _FakeDetector(["zebra", "cat"], [_box("zebra", 0.95), _box("cat", 0.8, (0.7, 0.7, 0.9, 0.9))])
    primary = _FakeDetector(["tiger", "zebra", "cat"], [_box("tiger", 0.9)])
    boxes, _ = EnsembleDetector(primary, base).predict(None)
    assert [b.label for b in boxes] == ["tiger", "cat"]


def test_ensemble_merges_one_object_and_keeps_other_label_as_alternative():
    base = _FakeDetector(["couch", "dining table"], [_box("couch", 0.9)])
    primary = _FakeDetector(["couch", "dining table"], [_box("dining table", 0.8), _box("couch", 0.7)])
    boxes, _ = EnsembleDetector(primary, base).predict(None)
    assert len(boxes) == 1 and boxes[0].label == "couch"
    assert [t["label"] for t in boxes[0].top_k] == ["couch", "dining table"]


class _FakeClip:
    """LabelVerifier with a fixed CLIP answer per crop instead of the ONNX model."""

    def __init__(self, labels, answers):
        self.labels, self.answers = labels, answers

    def run(self, _, feed):
        return [np.array(self.answers[: len(feed["crops"])], dtype=np.float32)]


def _verifier(labels, answers):
    v = LabelVerifier.__new__(LabelVerifier)
    v.labels, v.index, v.size = labels, {lab: i for i, lab in enumerate(labels)}, 32
    v.session = _FakeClip(labels, answers)
    return v


def test_clip_renames_an_unsure_box_and_keeps_yolo_label_as_alternative():
    v = _verifier(["orange", "lemon"], [[0.05, 0.95]])
    boxes, _ = v.check(Image.new("RGB", (100, 100)), [_box("orange", 0.4)])
    assert boxes[0].label == "lemon" and boxes[0].confidence == 0.4
    assert [t["label"] for t in boxes[0].top_k] == ["lemon", "orange"]


def test_clip_leaves_confident_small_or_doubtful_boxes_alone():
    v = _verifier(["orange", "lemon"], [[0.05, 0.95]])
    img = Image.new("RGB", (100, 100))
    assert v.check(img, [_box("orange", 0.9)])[0][0].label == "orange"  # YOLO is sure
    assert v.check(img, [_box("orange", 0.4, (0.1, 0.1, 0.2, 0.2))])[0][0].label == "orange"  # too small to judge
    v.session = _FakeClip(v.labels, [[0.3, 0.7]])  # CLIP does not rule YOLO's label out
    assert v.check(img, [_box("orange", 0.4)])[0][0].label == "orange"


# ------------------------------------------------------------------ golden: model classes <-> vocabulary

_ROOT = Path(__file__).resolve().parents[3]
_CLASSES = _ROOT / "AI" / "classes.yaml"
_WORDS = _ROOT / "BE" / "seed" / "concepts" / "words.csv"
# objects whose English name has several senses: the word must be the sense the detector means
_SENSES = {"mouse": ("chuột máy tính", "鼠标", "滑鼠"), "glasses": ("kính mắt", "眼镜", "眼鏡"),
           "watch": ("đồng hồ đeo tay", "手表", "手錶"), "keyboard": ("bàn phím", "键盘", "鍵盤"),
           "orange": ("quả cam", "橙子", "柳橙"), "cell phone": ("điện thoại di động", "手机", "手機")}


@pytest.mark.skipif(not _CLASSES.exists(), reason="AI/classes.yaml không có trong image này")
def test_every_detector_class_has_a_word_in_every_language():
    import csv

    import yaml

    data = yaml.safe_load(_CLASSES.read_text(encoding="utf-8"))
    rows = {r["yolo_label"]: r for r in csv.DictReader(_WORDS.open(encoding="utf-8")) if r["yolo_label"]}
    assert len(data["classes"]) == 78
    classes = data["classes"] + data["extra"]
    assert len({c["label"] for c in classes}) == len(classes)
    for c in classes:
        r = rows.get(c["label"])
        assert r, f"{c['label']}: không có từ nào gắn yolo_label"
        assert r["slug"] == c["slug"], c["label"]
        assert all(r[k].strip() for k in ("vi", "en", "zh_hans", "zh_hant")), c["label"]
    for label, (vi, hans, hant) in _SENSES.items():
        assert (rows[label]["vi"], rows[label]["zh_hans"], rows[label]["zh_hant"]) == (vi, hans, hant), label


# ------------------------------------------------------------------ error reports -> correction memory

def _photo(color):
    import io

    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (200, 200), color).save(buf, "JPEG")
    return SimpleUploadedFile("p.jpg", buf.getvalue(), content_type="image/jpeg")


@pytest.fixture
def memory_env(setup, settings, tmp_path, monkeypatch):
    """Detector always answers "cow"; the embedder maps a crop to its mean colour, so "looks alike" = same colour."""
    import numpy as np

    from apps.detection import memory, views

    settings.MEDIA_ROOT = str(tmp_path)
    user, c, cat = setup
    for slug in ("cow", "pig"):
        w = Word.objects.create(slug=slug, yolo_label=slug)
        WordTranslation.objects.create(word=w, language_id="en", text=slug, status=ReviewStatus.VERIFIED)
    monkeypatch.setattr(views, "get_detector", lambda: _FakeDetector(["cow"], [_box("cow", 0.9)]))

    def fake_embed(crops):
        v = np.array([np.asarray(cr.convert("RGB"), dtype=np.float32).mean(axis=(0, 1)) + 1 for cr in crops])
        return (v / np.linalg.norm(v, axis=1, keepdims=True)).astype(np.float32)

    monkeypatch.setattr(memory, "embed", fake_embed)
    monkeypatch.setattr(memory, "available", lambda: True)
    return user, c


def _learner(n):
    u = User.objects.create_user(f"l{n}@example.com", "Strong!Pass123", active_language="en")
    c = APIClient()
    c.force_authenticate(u)
    return u, c


def _detect(client, color=(200, 120, 120)):
    return client.post("/api/v1/detect/", {"image": _photo(color)}, format="multipart").data


def _report(client, det, **item):
    return client.post(f"/api/v1/detections/{det['id']}/confirm/", {"items": [
        {"id": det["items"][0]["id"], "selected": True, "feedback": "wrong", **item}]}, format="json").data


def test_error_report_fixes_the_same_mistake_for_the_reporter_at_once(memory_env):
    user, c = memory_env
    det = _detect(c)
    assert det["items"][0]["label"] == "cow"
    assert _report(c, det, corrected_label="pig")["reported"] == 1
    assert PersonalWord.objects.filter(user=user, word__slug="pig").exists()

    again = _detect(c)["items"][0]
    assert again["label"] == "pig" and again["learned"] is True
    assert _detect(c, color=(20, 200, 40))["items"][0]["label"] == "cow"  # a different-looking object is untouched
    _, other = _learner(1)
    assert _detect(other)["items"][0]["label"] == "cow"  # not approved yet -> only the reporter


def test_report_applies_to_everyone_after_consensus(memory_env):
    from apps.detection.memory import CONSENSUS_USERS
    from apps.detection.models import CorrectionMemory

    for n in range(CONSENSUS_USERS):
        _, c = _learner(n)
        _report(c, _detect(c), corrected_label="pig")
    assert set(CorrectionMemory.objects.values_list("status", flat=True)) == {"approved"}
    _, newcomer = _learner(99)
    assert _detect(newcomer)["items"][0]["label"] == "pig"


def test_not_an_object_report_hides_the_box(memory_env):
    _, c = memory_env
    _report(c, _detect(c), not_object=True)
    assert _detect(c)["items"] == []


def test_disputed_automatic_fix_is_rejected(memory_env):
    from apps.detection.memory import DISPUTE_LIMIT
    from apps.detection.models import CorrectionMemory

    _, c = memory_env
    _report(c, _detect(c), corrected_label="pig")
    CorrectionMemory.objects.update(status="approved")
    for n in range(DISPUTE_LIMIT):
        _, other = _learner(n)
        det = _detect(other)
        assert det["items"][0]["label"] == "pig"
        _report(other, det, corrected_label="cow")  # "it really is a cow"
    assert CorrectionMemory.objects.get(user__email="d@example.com").status == "rejected"
    _, newcomer = _learner(99)
    assert _detect(newcomer)["items"][0]["label"] == "cow"


def test_admin_reviews_and_exports_reports_as_training_data(memory_env):
    import io
    import zipfile

    _, c = memory_env
    _report(c, _detect(c), corrected_label="pig")
    staff = User.objects.create_user("s@example.com", "Strong!Pass123", role="staff")
    s = APIClient()
    s.force_authenticate(staff)
    rows = s.get("/api/v1/admin/detection-reports/").data["results"]
    assert [(r["wrong_label"], r["correct_label"], r["status"]) for r in rows] == [("cow", "pig", "pending")]
    assert s.get("/api/v1/admin/detection-reports/export/").status_code == 400  # nothing approved yet
    s.post(f"/api/v1/admin/detection-reports/{rows[0]['id']}/approve/")
    res = s.get("/api/v1/admin/detection-reports/export/")
    z = zipfile.ZipFile(io.BytesIO(b"".join(res.streaming_content) if res.streaming else res.content))
    names = z.read("names.txt").decode().split()
    label_file = [n for n in z.namelist() if n.startswith("labels/")][0]
    assert names == ["pig"] and z.read(label_file).decode().startswith("0 ")
    assert s.get("/api/v1/admin/detection-reports/summary/").data["approved_not_exported"] == 0


def test_labels_lists_every_detectable_object(memory_env):
    _, c = memory_env
    labels = {r["label"] for r in c.get("/api/v1/detections/labels/").data}
    assert {"cat", "cow", "pig"} <= labels
