"""Bulk delete (ticked rows) and the date filters shared by every list."""
from datetime import timedelta

import pytest
from django.core.files.base import ContentFile
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def as_user(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


@pytest.fixture
def admin():
    return User.objects.create_user(email="admin@example.com", password="Strong!Pass123", role="admin", is_staff=True)


def learner(n):
    return User.objects.create_user(email=f"l{n}@example.com", password="Strong!Pass123", birth_date="1990-01-01")


def test_admin_bulk_deletes_users_but_never_itself(admin):
    a, b = learner(1), learner(2)
    res = as_user(admin).post("/api/v1/admin/users/bulk-delete/", {"ids": [a.id, b.id, admin.id, 999999]}, format="json")
    assert res.status_code == 200
    assert res.data["deleted"] == 2 and res.data["not_found"] == 1
    assert res.data["skipped"] == [{"id": admin.id, "reason": "Không thể xóa tài khoản đang đăng nhập"}]
    assert list(User.objects.values_list("id", flat=True)) == [admin.id]

    from apps.audit.models import AuditLog
    log = AuditLog.objects.get(path="/api/v1/admin/users/bulk-delete/")
    assert log.object_id.startswith("4 mục:")


def test_single_delete_keeps_the_same_guards(admin):
    res = as_user(admin).delete(f"/api/v1/admin/users/{admin.id}/")
    assert res.status_code == 400 and User.objects.filter(pk=admin.pk).exists()


def test_a_learner_cannot_bulk_delete_admin_data():
    a, b = learner(1), learner(2)
    res = as_user(a).post("/api/v1/admin/users/bulk-delete/", {"ids": [b.id]}, format="json")
    assert res.status_code == 403 and User.objects.filter(pk=b.pk).exists()


def test_bad_bulk_requests_are_400(admin):
    client = as_user(admin)
    for body in ({}, {"ids": []}, {"ids": "1,2"}, {"ids": [0]}, {"ids": list(range(1, 502))}):
        assert client.post("/api/v1/admin/users/bulk-delete/", body, format="json").status_code == 400


def test_learner_bulk_deletes_only_own_notifications():
    from apps.notifications.models import Notification

    a, b = learner(1), learner(2)
    mine = [Notification.objects.create(user=a, kind="system", title=str(i)) for i in range(3)]
    theirs = Notification.objects.create(user=b, kind="system", title="x")
    res = as_user(a).post("/api/v1/notifications/bulk-delete/", {"ids": [mine[0].id, mine[1].id, theirs.id]}, format="json")
    assert res.data == {"deleted": 2, "skipped": [], "not_found": 1}
    assert Notification.objects.filter(pk=theirs.pk).exists() and Notification.objects.filter(user=a).count() == 1
    assert as_user(a).delete(f"/api/v1/notifications/{mine[2].id}/").status_code == 204


def test_notification_filters():
    from apps.notifications.models import Notification

    a = learner(1)
    Notification.objects.create(user=a, kind="like", title="social")
    Notification.objects.create(user=a, kind="reminder", title="learning", read_at=timezone.now())
    client = as_user(a)
    titles = lambda q: sorted(n["title"] for n in client.get(f"/api/v1/notifications/?{q}").data["results"])  # noqa: E731
    assert titles("group=social") == ["social"]
    assert titles("read=1") == ["learning"]
    assert titles("read=0") == ["social"]


def test_deleting_a_photo_removes_its_files(tmp_path, settings):
    from apps.detection.models import CorrectionMemory, Detection, DetectionItem, Photo

    settings.MEDIA_ROOT = tmp_path
    a, b = learner(1), learner(2)
    photo = Photo.objects.create(user=a)
    photo.image.save("p.jpg", ContentFile(b"jpeg"))
    det = Detection.objects.create(user=a, photo=photo, model_name="m", device="server")
    item = DetectionItem.objects.create(detection=det, label="cat", confidence=0.9, bbox=[0, 0, 1, 1])
    report = CorrectionMemory.objects.create(user=a, item=item, wrong_label="cat", correct_label="dog")
    report.crop.save("c.jpg", ContentFile(b"jpeg"))
    files = [tmp_path / photo.image.name, tmp_path / report.crop.name]
    assert all(f.exists() for f in files)

    assert as_user(b).post("/api/v1/detections/bulk-delete/", {"ids": [det.id]}, format="json").data["not_found"] == 1
    with pytest.MonkeyPatch.context() as m:  # files go on commit; the test transaction never commits
        m.setattr("django.db.transaction.on_commit", lambda fn, *a, **k: fn())
        res = as_user(a).post("/api/v1/detections/bulk-delete/", {"ids": [det.id]}, format="json")
    assert res.data["deleted"] == 1
    assert not Detection.objects.exists() and not Photo.objects.exists() and not CorrectionMemory.objects.exists()
    assert not any(f.exists() for f in files)


def test_exams_with_results_and_questions_in_use_are_kept(admin):
    from apps.quizzes.models import Exam, ExamQuestion, Question, Submission
    from apps.vocab.models import Language

    lang, _ = Language.objects.get_or_create(code="en", defaults={"name": "English", "native_name": "English", "tts_locale": "en-US"})
    used = Exam.objects.create(title="used", language=lang)
    empty = Exam.objects.create(title="empty", language=lang)
    Submission.objects.create(user=learner(1), exam=used, status="submitted")
    q_in_exam = Question.objects.create(kind="essay", language=lang, prompt="in exam")
    q_free = Question.objects.create(kind="essay", language=lang, prompt="free")
    ExamQuestion.objects.create(exam=used, question=q_in_exam, order=1)

    client = as_user(admin)
    res = client.post("/api/v1/admin/exams/bulk-delete/", {"ids": [used.id, empty.id]}, format="json")
    assert res.data["deleted"] == 1 and "1 lượt làm bài" in res.data["skipped"][0]["reason"]
    res = client.post("/api/v1/admin/questions/bulk-delete/", {"ids": [q_in_exam.id, q_free.id]}, format="json")
    assert res.data["deleted"] == 1 and "used" in res.data["skipped"][0]["reason"]
    assert set(Exam.objects.values_list("title", flat=True)) == {"used"}


def test_created_date_filter_and_inactive_users(admin):
    old, new = learner(1), learner(2)
    User.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=40))
    User.objects.filter(pk=new.pk).update(last_login=timezone.now())
    client = as_user(admin)
    since = (timezone.localdate() - timedelta(days=30)).isoformat()
    emails = lambda q: sorted(u["email"] for u in client.get(f"/api/v1/admin/users/?{q}").data["results"])  # noqa: E731
    assert emails(f"created_to={since}") == ["l1@example.com"]
    assert "l1@example.com" not in emails(f"created_from={since}")
    assert emails(f"created_from=not-a-date&role=learner") == ["l1@example.com", "l2@example.com"]
    assert "l2@example.com" not in emails(f"inactive_since={timezone.localdate().isoformat()}")
    assert emails("never_logged_in=1&role=learner") == ["l1@example.com"]
