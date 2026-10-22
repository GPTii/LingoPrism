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
