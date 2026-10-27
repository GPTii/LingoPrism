import pytest
from django.core import mail
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def register(client, email="a@example.com", password="Strong!Pass123"):
    return client.post("/api/v1/auth/register/", {"email": email, "password": password, "accept_terms": True}, format="json")


def test_register_login_me(client):
    res = register(client)
    assert res.status_code == 201
    assert res.data["user"]["email"] == "a@example.com"

    res = client.post("/api/v1/auth/login/", {"email": "A@example.com", "password": "Strong!Pass123"}, format="json")
    assert res.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")

    res = client.patch("/api/v1/me/", {"learning_languages": ["en", "zh"], "zh_script": "hant"}, format="json")
    assert res.status_code == 200
    assert res.data["zh_script"] == "hant"
    assert res.data["goal"]["daily_new_target"] == 10


def test_register_duplicate_email(client):
    register(client)
    res = register(client)
    assert res.status_code == 400
    assert res.data["detail"] == "Email đã được sử dụng"


def test_register_same_email_at_once_is_400_not_500(client, monkeypatch):
    """A double tap sends two sign-ups together: both pass the "email free?" check, the second hits the unique index."""
    from apps.accounts import serializers

    register(client)
    monkeypatch.setattr(serializers.RegisterSerializer, "validate_email", lambda self, value: value.lower())
    res = register(client)
    assert res.status_code == 400
    assert res.data["detail"] == "Email đã được sử dụng"


def test_wrong_password(client):
    register(client)
    res = client.post("/api/v1/auth/login/", {"email": "a@example.com", "password": "nope"}, format="json")
    assert res.status_code == 400


def test_forgot_password_flow(client):
    register(client)
    client.post("/api/v1/auth/password/forgot/", {"email": "a@example.com"}, format="json")
    code = mail.outbox[-1].body.split(": ")[1][:6]

    res = client.post("/api/v1/auth/password/verify/", {"email": "a@example.com", "code": "000000" if code != "000000" else "111111"}, format="json")
    assert res.status_code == 400

    res = client.post("/api/v1/auth/password/verify/", {"email": "a@example.com", "code": code}, format="json")
    assert res.status_code == 200
    token = res.data["reset_token"]

    res = client.post("/api/v1/auth/password/reset/", {"reset_token": token, "new_password": "Another!Pass456"}, format="json")
    assert res.status_code == 200
    res = client.post("/api/v1/auth/login/", {"email": "a@example.com", "password": "Another!Pass456"}, format="json")
    assert res.status_code == 200


def test_admin_users_requires_admin(client):
    res = register(client)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")
    assert client.get("/api/v1/admin/users/").status_code == 403


def test_admin_user_crud(client):
    from apps.accounts.models import User

    admin = User.objects.create_superuser("root@example.com", "Strong!Pass123")
    client.force_authenticate(admin)

    res = client.post("/api/v1/admin/users/", {
        "email": "New@Example.com", "password": "Strong!Pass123", "display_name": "Lan",
        "role": "staff", "active_language": "zh", "zh_script": "hant",
    }, format="json")
    assert res.status_code == 201, res.data
    uid = res.data["id"]
    assert res.data["email"] == "new@example.com" and "password" not in res.data
    assert res.data["learning_languages"] == ["zh"]
    assert client.post("/api/v1/admin/users/", {"email": "x@example.com"}, format="json").status_code == 400

    res = client.patch(f"/api/v1/admin/users/{uid}/", {"display_name": "Lan 2", "password": "Another!Pass456"}, format="json")
    assert res.status_code == 200 and res.data["display_name"] == "Lan 2"
    assert APIClient().post("/api/v1/auth/login/", {"email": "new@example.com", "password": "Another!Pass456"},
                            format="json").status_code == 200

    assert client.patch(f"/api/v1/admin/users/{admin.id}/", {"role": "learner"}, format="json").status_code == 400
    assert client.delete(f"/api/v1/admin/users/{admin.id}/").status_code == 400
    assert client.delete(f"/api/v1/admin/users/{uid}/").status_code == 204
    assert not User.objects.filter(pk=uid).exists()


def test_google_config_is_off_without_client_ids(client, settings):
    settings.GOOGLE_WEB_CLIENT_ID = ""
    assert client.get("/api/v1/auth/google/config/").data == {"client_id": None}


def test_google_config_returns_the_public_web_client(client, settings):
    settings.GOOGLE_WEB_CLIENT_ID = "123-web.apps.googleusercontent.com"
    assert client.get("/api/v1/auth/google/config/").data == {"client_id": "123-web.apps.googleusercontent.com"}


def test_google_login_accepts_only_our_audiences(client, settings, monkeypatch):
    from google.oauth2 import id_token as google_id_token

    settings.GOOGLE_CLIENT_IDS = ["123-web.apps.googleusercontent.com"]
    info = {"aud": "999-other.apps.googleusercontent.com", "sub": "g-1", "email": "g@example.com", "email_verified": True, "name": "G"}
    monkeypatch.setattr(google_id_token, "verify_oauth2_token", lambda token, req: info)
    assert client.post("/api/v1/auth/google/", {"id_token": "x"}, format="json").status_code == 400

    info["aud"] = "123-web.apps.googleusercontent.com"
    res = client.post("/api/v1/auth/google/", {"id_token": "x"}, format="json")
    assert res.status_code == 200
    assert res.data["user"]["email"] == "g@example.com"
    # the same Google account signs in to the same user next time
    assert client.post("/api/v1/auth/google/", {"id_token": "x"}, format="json").data["user"]["id"] == res.data["user"]["id"]


def test_secure_demo_accounts_replaces_the_public_demo_password():
    from io import StringIO

    from django.core.management import call_command

    from apps.accounts.management.commands.seed_demo_users import DEMO_PASSWORD
    from apps.accounts.models import User

    demo = User.objects.create_user(email="kid@lingoprism.local", password=DEMO_PASSWORD)
    changed = User.objects.create_user(email="adult@lingoprism.local", password="Own!Pass123")
    learner = User.objects.create_user(email="real@example.com", password=DEMO_PASSWORD)
    out = StringIO()
    call_command("secure_demo_accounts", stdout=out)

    demo.refresh_from_db(), changed.refresh_from_db(), learner.refresh_from_db()
    assert not demo.check_password(DEMO_PASSWORD)
    email, password = out.getvalue().split()
    assert email == demo.email and demo.check_password(password)
    assert changed.check_password("Own!Pass123")  # a demo account whose password was already changed is left alone
    assert learner.check_password(DEMO_PASSWORD)  # real learners are never touched
