import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit.models import AuditLog

pytestmark = pytest.mark.django_db

BROADCAST = {"title": "Bảo trì", "body": "Tối nay 22h", "role": "learner", "learner_type": "adult"}


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


def test_staff_change_is_logged_without_values():
    staff = User.objects.create_user("staff@example.com", "Strong!Pass123", role="staff")
    res = client_for(staff).post("/api/v1/admin/broadcast/", BROADCAST, format="json")
    assert res.status_code < 400, res.data
    log = AuditLog.objects.get()
    assert (log.actor, log.actor_role, log.method, log.resource) == (staff, "staff", "POST", "admin/broadcast")
    assert log.fields == ["body", "learner_type", "role", "title"]  # names only, never the text
    assert "Bảo trì" not in str(log.__dict__)


def test_learners_failures_and_sign_in_are_not_logged():
    learner = User.objects.create_user("l@example.com", "Strong!Pass123")
    client_for(learner).post("/api/v1/admin/broadcast/", BROADCAST, format="json")  # 403
    staff = User.objects.create_user("staff@example.com", "Strong!Pass123", role="staff")
    client_for(staff).post("/api/v1/admin/broadcast/", {}, format="json")  # 400
    APIClient().post("/api/v1/auth/login/", {"email": "staff@example.com", "password": "Strong!Pass123"}, format="json")
    assert AuditLog.objects.count() == 0


def test_only_admins_read_the_log():
    admin = User.objects.create_user("a@example.com", "Strong!Pass123", role="admin")
    staff = User.objects.create_user("s@example.com", "Strong!Pass123", role="staff")
    client_for(staff).post("/api/v1/admin/broadcast/", BROADCAST, format="json")
    assert client_for(staff).get("/api/v1/admin/audit-logs/").status_code == 403
    res = client_for(admin).get("/api/v1/admin/audit-logs/?q=s@example")
    assert res.status_code == 200 and res.data["count"] == 1
    assert res.data["results"][0]["actor_email"] == "s@example.com"
