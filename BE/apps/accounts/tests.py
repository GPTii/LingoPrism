import pytest
from django.core import mail
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def register(client, email="a@example.com", password="Strong!Pass123"):
    return client.post("/api/v1/auth/register/", {"email": email, "password": password}, format="json")


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
