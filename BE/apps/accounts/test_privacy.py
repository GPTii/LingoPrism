"""Terms acceptance, e-mail verification, kid accounts, deleting one's own account, release notes."""
from datetime import date
from pathlib import Path

import pytest
from django.conf import settings
from django.core import mail
from django.core.files.base import ContentFile
from rest_framework.test import APIClient

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def as_user(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


def code_in(message) -> str:
    import re

    return re.search(r"\b(\d{6})\b", message.body).group(1)


def signup(email="new@example.com", **extra):
    return APIClient().post("/api/v1/auth/register/", {"email": email, "password": "Strong!Pass123", **extra}, format="json")


def test_sign_up_needs_the_terms_and_records_them():
    assert signup().status_code == 400
    assert signup(accept_terms=False).status_code == 400
    res = signup(accept_terms=True)
    assert res.status_code == 201 and res.data["user"]["email_verified"] is False
    user = User.objects.get(email="new@example.com")
    assert user.terms_version == settings.LEGAL_VERSION and user.terms_accepted_at


def test_email_verification_code_and_what_it_unlocks():
    signup(accept_terms=True)
    user = User.objects.get(email="new@example.com")
    client = as_user(user)
    # before: learning works, reaching other learners does not
    assert client.get("/api/v1/me/").status_code == 200
    assert client.post("/api/v1/groups/", {"name": "x"}, format="json").status_code == 403
    sent = mail.outbox[-1]
    assert sent.to == ["new@example.com"]
    code = code_in(sent)
    wrong = "000000" if code != "000000" else "111111"
    assert client.post("/api/v1/auth/email/verify/", {"code": wrong}, format="json").status_code == 400
    assert client.post("/api/v1/auth/email/resend/").status_code == 200
    assert client.post("/api/v1/auth/email/verify/", {"code": code}, format="json").status_code == 400  # replaced
    res = client.post("/api/v1/auth/email/verify/", {"code": code_in(mail.outbox[-1])}, format="json")
    assert res.status_code == 200 and res.data["email_verified"] is True
    user.refresh_from_db()
    assert as_user(user).post("/api/v1/groups/", {"name": "x"}, format="json").status_code == 201


def test_five_wrong_codes_end_the_code():
    signup(accept_terms=True)
    user = User.objects.get(email="new@example.com")
    client = as_user(user)
    code = code_in(mail.outbox[-1])
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        client.post("/api/v1/auth/email/verify/", {"code": wrong}, format="json")
    assert client.post("/api/v1/auth/email/verify/", {"code": code}, format="json").status_code == 400


def with_jwt(user):
    """The real sign-in path (force_authenticate would skip the authentication class that holds the check)."""
    from rest_framework_simplejwt.tokens import RefreshToken

    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return c


def test_a_kid_account_learns_right_away():
    # a parent signs in (often with Google) and picks kid mode for the child: no second consent step
    kid = User.objects.create_user("kid@example.com", "Strong!Pass123", learner_type="kid",
                                   birth_date=date(date.today().year - 8, 1, 1))
    client = with_jwt(kid)
    assert "parent_consent" not in client.get("/api/v1/me/").data
    assert client.get("/api/v1/topics/").status_code == 200
    assert client.post("/api/v1/me/parent-consent/request/", {"parent_email": "mom@example.com"},
                       format="json").status_code == 404


def test_deleting_my_account_removes_it_and_its_files(tmp_path, settings):
    from apps.community.models import Post
    from apps.detection.models import Photo

    settings.MEDIA_ROOT = tmp_path
    user = User.objects.create_user("me@example.com", "Strong!Pass123", birth_date=date(1990, 1, 1))
    photo = Photo.objects.create(user=user)
    user.avatar.save("a.png", ContentFile(_png()), save=True)
    post = Post(user=user)
    post.image.save("p.png", ContentFile(_png()), save=True)
    files = [Path(user.avatar.path), Path(post.image.path)]
    assert all(f.exists() for f in files)
    client = as_user(user)
    assert client.post("/api/v1/me/delete/", {"password": "wrong"}, format="json").status_code == 400
    with pytest.MonkeyPatch.context() as m:  # files go on commit; the test transaction never commits
        m.setattr("django.db.transaction.on_commit", lambda fn, *a, **k: fn())
        assert client.post("/api/v1/me/delete/", {"password": "Strong!Pass123"}, format="json").status_code == 204
    assert not User.objects.filter(email="me@example.com").exists() and not Photo.objects.exists()
    assert not any(f.exists() for f in files)


def test_a_google_only_account_confirms_by_typing():
    user = User.objects.create_user("g@example.com", None, birth_date=date(1990, 1, 1))  # no usable password
    client = as_user(user)
    assert client.get("/api/v1/me/").data["has_password"] is False
    assert client.post("/api/v1/me/delete/", {"confirm": "ok"}, format="json").status_code == 400
    assert client.post("/api/v1/me/delete/", {"confirm": "xoá"}, format="json").status_code == 204


def test_the_last_admin_cannot_delete_itself():
    admin = User.objects.create_user("admin@example.com", "Strong!Pass123", role="admin", is_staff=True)
    assert as_user(admin).post("/api/v1/me/delete/", {"password": "Strong!Pass123"}, format="json").status_code == 400


def test_release_notes_are_public_and_the_changelog_is_up_to_date():
    from apps.core.releases import changelog_markdown

    res = APIClient().get("/api/v1/releases/")
    assert res.status_code == 200 and res.data["latest"] == res.data["results"][0]["version"]
    versions = [r["version"] for r in res.data["results"]]
    assert versions == sorted(versions, key=lambda v: tuple(map(int, v.split("."))), reverse=True)
    changelog = Path(settings.BASE_DIR).parent / "CHANGELOG.md"
    if changelog.exists():  # in the repository (not inside the backend image)
        assert changelog.read_text(encoding="utf-8") == changelog_markdown(), "run: python manage.py changelog"


def _png():
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "blue").save(buf, "PNG")
    return buf.getvalue()
