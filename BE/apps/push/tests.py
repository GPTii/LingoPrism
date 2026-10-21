import pytest

from apps.accounts.models import User
from apps.notifications.models import DeviceToken, Notification, NotificationSetting
from apps.push import fcm

pytestmark = pytest.mark.django_db


@pytest.fixture
def sent(monkeypatch, settings):
    calls = []
    settings.FIREBASE_CREDENTIALS_FILE = "/secrets/firebase.json"
    monkeypatch.setattr(fcm, "send_to_user_async", lambda uid, title, body, data=None: calls.append((uid, title, data)))
    return calls


def test_new_notification_is_pushed(sent):
    u = User.objects.create_user("p@example.com", "Strong!Pass123")
    n = Notification.objects.create(user=u, kind="reminder", title="Đến giờ ôn tập", data={"route": "/review"})
    assert sent == [(u.id, "Đến giờ ôn tập", {"route": "/review", "notification_id": n.id, "kind": "reminder"})]


def test_respects_settings_and_is_off_without_credentials(sent, settings):
    u = User.objects.create_user("p@example.com", "Strong!Pass123")
    NotificationSetting.objects.create(user=u, push_enabled=True, social_enabled=False)
    Notification.objects.create(user=u, kind="like", title="Ai đó thích bài của bạn")  # social off
    NotificationSetting.objects.filter(user=u).update(push_enabled=False)
    Notification.objects.create(user=u, kind="reminder", title="Nhắc học")  # push off
    assert sent == []
    settings.FIREBASE_CREDENTIALS_FILE = ""
    NotificationSetting.objects.filter(user=u).update(push_enabled=True)
    Notification.objects.create(user=u, kind="reminder", title="Nhắc học")  # no Firebase configured
    assert sent == []


def test_unregistered_device_is_forgotten(monkeypatch, settings):
    settings.FIREBASE_CREDENTIALS_FILE = "/secrets/firebase.json"
    u = User.objects.create_user("p@example.com", "Strong!Pass123")
    DeviceToken.objects.create(user=u, token="old-phone", platform="android")
    monkeypatch.setattr(fcm, "send", lambda *a, **k: "gone")

    class NoThread:  # run the background job inline for the test
        def __init__(self, target, daemon):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(fcm.threading, "Thread", NoThread)
    fcm.send_to_user_async(u.id, "t", "b")
    assert not DeviceToken.objects.filter(token="old-phone").exists()
