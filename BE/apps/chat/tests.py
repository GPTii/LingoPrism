import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.community.models import UserFollow

from .models import DirectMessage

pytestmark = pytest.mark.django_db


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


@pytest.fixture
def people(db):
    a = User.objects.create_user("a@example.com", "Strong!Pass123", display_name="An")
    b = User.objects.create_user("b@example.com", "Strong!Pass123", display_name="Bình")
    kid = User.objects.create_user("k@example.com", "Strong!Pass123", learner_type="kid")
    return a, b, kid


def follow_both(x, y):
    UserFollow.objects.create(follower=x, following=y)
    UserFollow.objects.create(follower=y, following=x)


def test_private_messages_need_mutual_follow(people):
    a, b, kid = people
    ca, cb = client_for(a), client_for(b)
    assert ca.post("/api/v1/messages/threads/", {"user": b.id}, format="json").status_code == 400
    UserFollow.objects.create(follower=a, following=b)  # one way only: still no
    assert ca.get(f"/api/v1/community/users/{b.id}/profile/").data["can_message"] is False
    assert ca.post("/api/v1/messages/threads/", {"user": b.id}, format="json").status_code == 400
    UserFollow.objects.create(follower=b, following=a)
    assert ca.get(f"/api/v1/community/users/{b.id}/profile/").data["can_message"] is True

    thread = ca.post("/api/v1/messages/threads/", {"user": b.id}, format="json").data
    assert thread["other"]["id"] == b.id
    # opening it again from the other side is the same conversation
    assert cb.post("/api/v1/messages/threads/", {"user": a.id}, format="json").data["id"] == thread["id"]

    url = f"/api/v1/messages/threads/{thread['id']}/messages/"
    m = ca.post(url, {"content": "Chào Bình!", "client_id": "c1"}, format="json")
    assert m.status_code == 201
    assert ca.post(url, {"content": "Chào Bình!", "client_id": "c1"}, format="json").data["id"] == m.data["id"]  # resend
    ca.post(url, {"content": "Học bài chưa?"}, format="json")
    # one notification for the burst, not one per message
    assert b.notifications.filter(kind="message").count() == 1

    rows = cb.get("/api/v1/messages/threads/").data
    assert rows[0]["unread"] == 2 and rows[0]["last_message"]["content"] == "Học bài chưa?"
    assert [x["content"] for x in cb.get(url).data["results"]] == ["Chào Bình!", "Học bài chưa?"]
    assert cb.get("/api/v1/messages/threads/").data[0]["unread"] == 0  # reading marks them read

    # unfollowing stops new messages; the history stays
    UserFollow.objects.filter(follower=b, following=a).delete()
    assert ca.post(url, {"content": "Còn đó không?"}, format="json").status_code == 400
    assert DirectMessage.objects.count() == 2


def test_strangers_and_kids_are_kept_out(people):
    a, b, kid = people
    follow_both(a, b)
    follow_both(a, kid)  # even if a child account ends up following back
    assert client_for(a).post("/api/v1/messages/threads/", {"user": kid.id}, format="json").status_code == 400
    assert client_for(kid).post("/api/v1/messages/threads/", {"user": a.id}, format="json").status_code == 400

    thread = client_for(a).post("/api/v1/messages/threads/", {"user": b.id}, format="json").data
    outsider = client_for(User.objects.create_user("c@example.com", "Strong!Pass123"))
    assert outsider.get(f"/api/v1/messages/threads/{thread['id']}/messages/").status_code == 404
    assert outsider.post(f"/api/v1/messages/threads/{thread['id']}/messages/", {"content": "hi"}, format="json").status_code == 404


def test_blocking_ends_messages_follows_and_hides_posts(people):
    from apps.community.models import Post

    a, b, kid = people
    follow_both(a, b)
    ca, cb = client_for(a), client_for(b)
    thread = ca.post("/api/v1/messages/threads/", {"user": b.id}, format="json").data
    Post.objects.create(user=b, image="posts/x.png", caption="Bài của Bình")
    assert len(ca.get("/api/v1/posts/").data["results"]) == 1

    assert cb.post(f"/api/v1/community/users/{a.id}/block/").data == {"blocked": True}
    assert not UserFollow.objects.filter(follower=a, following=b).exists()  # both directions gone
    assert not UserFollow.objects.filter(follower=b, following=a).exists()
    assert ca.post(f"/api/v1/community/users/{b.id}/follow/").status_code == 400  # cannot follow back
    url = f"/api/v1/messages/threads/{thread['id']}/messages/"
    assert ca.post(url, {"content": "Sao vậy?"}, format="json").status_code == 400
    assert ca.get("/api/v1/posts/").data["results"] == []  # the blocker's posts are gone for the blocked one…
    assert cb.get(f"/api/v1/community/users/{a.id}/profile/").data["blocked"] is True

    assert cb.delete(f"/api/v1/community/users/{a.id}/block/").data == {"blocked": False}
    assert len(ca.get("/api/v1/posts/").data["results"]) == 1  # …until unblocked
    assert ca.post(f"/api/v1/community/users/{b.id}/follow/").status_code == 200


def test_report_a_learner_with_the_conversation_as_evidence(people):
    from rest_framework_simplejwt.tokens import RefreshToken

    from apps.community.models import UserBlock, UserReport

    a, b, kid = people
    follow_both(a, b)
    ca, cb = client_for(a), client_for(b)
    thread = ca.post("/api/v1/messages/threads/", {"user": b.id}, format="json").data
    cb.post(f"/api/v1/messages/threads/{thread['id']}/messages/", {"content": "Gửi mình số tài khoản đi"}, format="json")

    # a thread that is not theirs cannot be attached
    assert ca.post(f"/api/v1/community/users/{b.id}/report/", {"reason": "spam", "thread": 999999}, format="json").status_code == 404
    assert ca.post(f"/api/v1/community/users/{b.id}/report/", {"reason": "other", "details": "?"}, format="json").status_code == 400

    r = ca.post(f"/api/v1/community/users/{b.id}/report/", {"reason": "spam", "thread": thread["id"], "block": True}, format="json")
    assert r.status_code == 201 and r.data["blocked"] is True
    assert UserBlock.objects.filter(blocker=a, blocked=b).exists()
    report = UserReport.objects.get()
    assert [m["content"] for m in report.evidence] == ["Gửi mình số tài khoản đi"]
    # the evidence stays even if the conversation goes away
    from apps.chat.models import DirectThread
    DirectThread.objects.all().delete()
    report.refresh_from_db()
    assert report.evidence and report.thread is None
    assert ca.post(f"/api/v1/community/users/{b.id}/report/", {"reason": "spam"}, format="json").status_code == 400  # once while pending

    # learners cannot see the moderation queue
    assert ca.get("/api/v1/admin/user-reports/").status_code == 403
    staff = User.objects.create_user("mod@example.com", "Strong!Pass123", role="staff")
    cs = client_for(staff)
    row = cs.get("/api/v1/admin/user-reports/?status=pending").data["results"][0]
    assert row["reported"] == b.id and row["reports_against"] == 1 and row["evidence"][0]["sender_id"] == b.id

    refresh = str(RefreshToken.for_user(b))
    real_b = APIClient()
    real_b.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(b).access_token}")
    assert real_b.get("/api/v1/me/").status_code == 200
    assert cs.post(f"/api/v1/admin/user-reports/{row['id']}/resolve/", {"lock": True}, format="json").status_code == 200
    b.refresh_from_db()
    assert b.status == "locked"
    assert UserReport.objects.get().status == "resolved"
    assert a.notifications.filter(title="Báo cáo của bạn đã được xem xét").exists()
    # a locked account is cut off at once: its access token and refresh token stop working
    assert real_b.get("/api/v1/me/").status_code == 401
    assert APIClient().post("/api/v1/auth/refresh/", {"refresh": refresh}, format="json").status_code == 401


def test_staff_cannot_be_locked_from_a_report(people):
    from apps.community.models import UserReport

    a, b, kid = people
    staff = User.objects.create_user("mod@example.com", "Strong!Pass123", role="staff")
    report = UserReport.objects.create(reporter=a, reported=staff, reason="other", details="giả làm admin")
    r = client_for(staff).post(f"/api/v1/admin/user-reports/{report.id}/resolve/", {"lock": True}, format="json")
    assert r.status_code == 400
    assert client_for(staff).post(f"/api/v1/admin/user-reports/{report.id}/resolve/", {}, format="json").status_code == 200
    report.refresh_from_db()
    assert report.status == "dismissed"
