"""Sentry gets the error and where it happened, nothing about the learner (apps/core/error_tracking.py)."""
import json

import pytest
import sentry_sdk
from django.urls import path
from rest_framework.test import APIClient
from sentry_sdk.transport import Transport

from apps.accounts.models import User

from . import error_tracking


def broken(request):
    # learner data only at run time, as in production (Sentry also sends the source lines around the error)
    note = json.loads(request.body)["message"]  # a local variable must not leave the server  # noqa: F841
    raise ValueError(f"Key (email)=({json.loads(request.body)['parent']}) already exists")


urlpatterns = [path("broken/", broken)]


class Capture(Transport):
    def __init__(self, options=None):
        super().__init__(options)
        self.events = []

    def capture_envelope(self, envelope):
        for item in envelope.items:
            if item.type == "event":
                self.events.append(item.payload.json)


@pytest.fixture
def sentry():
    transport = Capture()
    error_tracking.init("https://public@sentry.example/1", "test", transport=transport)
    yield transport
    sentry_sdk.init()  # no DSN: off again for the other tests


@pytest.mark.django_db
@pytest.mark.urls(__name__)
def test_a_server_error_reaches_sentry_without_personal_data(sentry):
    user = User.objects.create_user("kid@example.com", "Kid-Test!2026", display_name="Na")
    client = APIClient(raise_request_exception=False)
    client.force_authenticate(user)
    response = client.post(
        "/broken/?token=eyJsecret",
        {"password": "hunter2", "message": "Bé Na, nhà em ở ngõ 5", "parent": "parent.na@gmail.com"}, format="json",
        HTTP_COOKIE="sessionid=abc", HTTP_X_FORWARDED_FOR="1.2.3.4", HTTP_USER_AGENT="LingoPrism-test",
    )
    assert response.status_code == 500
    sentry_sdk.flush()

    assert len(sentry.events) == 1
    event = sentry.events[0]
    exc = event["exception"]["values"][-1]
    assert exc["type"] == "ValueError" and exc["value"] == "Key (email)=([email]) already exists"
    assert any(f["function"] == "broken" for f in exc["stacktrace"]["frames"])  # where it happened
    assert event["release"].startswith("lingoprism@") and event["environment"] == "test"
    assert event["transaction"] == "/broken/"  # the route, without its query string
    assert set(event.get("request", {}).get("headers", {})) <= error_tracking.KEEP_HEADERS

    sent = json.dumps(event, ensure_ascii=False)
    for private in ("eyJsecret", "hunter2", "ngõ 5", "sessionid", "1.2.3.4", "kid@example.com", "parent.na",
                    "Bé Na", '"Na"'):
        assert private not in sent, private
    assert "user" not in event
