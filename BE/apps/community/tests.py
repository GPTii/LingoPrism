import io

import pytest
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import User
from apps.chat.models import GroupMessage, SupportConversation
from apps.community.models import Group, GroupMember, Post

pytestmark = pytest.mark.django_db


def png():
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), (10, 200, 100)).save(buf, "PNG")
    return SimpleUploadedFile("p.png", buf.getvalue(), content_type="image/png")


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


@pytest.fixture
def users(db):
    a = User.objects.create_user("a@example.com", "Strong!Pass123", display_name="An")
    b = User.objects.create_user("b@example.com", "Strong!Pass123", display_name="Bình")
    kid = User.objects.create_user("k@example.com", "Strong!Pass123", learner_type="kid")
    return a, b, kid


def test_post_like_comment_report(users):
    a, b, kid = users
    res = client_for(a).post("/api/v1/posts/", {"image": png(), "caption": "Con mèo nhà mình"}, format="multipart")
    assert res.status_code == 201, res.data
    pid = res.data["id"]
    cb = client_for(b)
    assert cb.post(f"/api/v1/posts/{pid}/like/").data == {"liked": True}
    assert cb.post(f"/api/v1/posts/{pid}/comments/", {"content": "Dễ thương quá"}, format="json").status_code == 201
    feed = cb.get("/api/v1/posts/").data["results"]
    assert feed[0]["like_count"] == 1 and feed[0]["comment_count"] == 1 and feed[0]["liked"] is True
    assert a.notifications.filter(kind__in=["like", "comment"]).count() == 2
    assert cb.post(f"/api/v1/posts/{pid}/report/", {"reason": "other", "details": "ngắn"}, format="json").status_code == 400
    assert cb.post(f"/api/v1/posts/{pid}/report/", {"reason": "spam"}, format="json").status_code == 201
    assert cb.delete(f"/api/v1/posts/{pid}/").status_code == 403


def test_kids_cannot_post_or_comment(users):
    a, b, kid = users
    post = Post.objects.create(user=a, image=png())
    ck = client_for(kid)
    assert ck.post("/api/v1/posts/", {"image": png()}, format="multipart").status_code == 403
    assert ck.post(f"/api/v1/posts/{post.id}/comments/", {"content": "hi"}, format="json").status_code == 403


def test_group_approval_flow(users):
    a, b, _ = users
    ca, cb = client_for(a), client_for(b)
    gid = ca.post("/api/v1/groups/", {"name": "HSK 2", "require_approval": True}, format="json").data["id"]
    assert cb.post(f"/api/v1/groups/{gid}/join/").data == {"status": "pending"}
    assert cb.get(f"/api/v1/groups/{gid}/messages/").status_code == 403
    member = GroupMember.objects.get(group_id=gid, user=b)
    assert ca.post(f"/api/v1/groups/{gid}/members/{member.id}/approve/").status_code == 200
    res = cb.post(f"/api/v1/groups/{gid}/messages/", {"content": "你好", "client_id": "c1"}, format="json")
    assert res.status_code == 201
    cb.post(f"/api/v1/groups/{gid}/messages/", {"content": "你好", "client_id": "c1"}, format="json")
    assert GroupMessage.objects.filter(group_id=gid).count() == 1  # de-duplicated by client_id
    res = cb.post(f"/api/v1/groups/{gid}/messages/", {"kind": "sticker", "sticker": "sticker_ok"}, format="json")
    assert res.status_code == 400  # sticker not owned


@pytest.mark.django_db(transaction=True)
def test_group_chat_websocket(users):
    from config.asgi import application

    a, b, _ = users
    group = Group.objects.create(name="Nhóm", created_by=a)
    GroupMember.objects.create(group=group, user=a, role="leader")
    GroupMember.objects.create(group=group, user=b)

    async def run():
        ca = WebsocketCommunicator(application, f"/ws/groups/{group.id}/?token={AccessToken.for_user(a)}")
        cb = WebsocketCommunicator(application, f"/ws/groups/{group.id}/?token={AccessToken.for_user(b)}")
        assert (await ca.connect())[0] and (await cb.connect())[0]
        await ca.send_json_to({"action": "send", "content": "xin chào", "client_id": "m1"})
        got = await cb.receive_json_from(timeout=3)
        assert got["event"] == "message" and got["payload"]["content"] == "xin chào" and got["payload"]["client_id"] == "m1"
        await ca.disconnect()
        await cb.disconnect()
        outsider = await database_sync_to_async(User.objects.create_user)("x@example.com", "Strong!Pass123")
        co = WebsocketCommunicator(application, f"/ws/groups/{group.id}/?token={AccessToken.for_user(outsider)}")
        assert not (await co.connect())[0]

    async_to_sync(run)()


def test_support_chat(users):
    a, _, kid = users
    staff = User.objects.create_user("s@example.com", "Strong!Pass123", role="staff")
    ck = client_for(kid)  # kids may use support chat
    conv = ck.post("/api/v1/support/conversations/", {"content": "Em không hiểu từ 貓"}, format="json").data
    cs = client_for(staff)
    inbox = cs.get("/api/v1/support/conversations/").data["results"]
    assert inbox[0]["unread"] == 1
    cs.post(f"/api/v1/support/conversations/{conv['id']}/messages/", {"content": "貓 là con mèo nhé"}, format="json")
    msgs = ck.get(f"/api/v1/support/conversations/{conv['id']}/messages/").data
    assert [m["content"] for m in msgs] == ["Em không hiểu từ 貓", "貓 là con mèo nhé"]
    assert SupportConversation.objects.get().staff == staff
    assert client_for(a).get(f"/api/v1/support/conversations/{conv['id']}/").status_code == 404


def test_share_a_photo_only_with_your_own_detection(users):
    from apps.detection.models import Detection

    a, b, kid = users
    mine = Detection.objects.create(user=a, model_name="test", device="server")
    theirs = Detection.objects.create(user=b, model_name="test", device="server")
    ca = client_for(a)
    res = ca.post("/api/v1/posts/", {"image": png(), "caption": "Cái cốc", "detection": theirs.id}, format="multipart")
    assert res.status_code == 400 and "detection" in res.data["errors"]
    res = ca.post("/api/v1/posts/", {"image": png(), "caption": "Cái cốc", "detection": mine.id}, format="multipart")
    assert res.status_code == 201 and res.data["detection"] == mine.id


def test_follow_suggestions(users):
    from apps.community.models import UserBlock, UserFollow

    a, b, kid = users
    a.active_language = "zh"
    a.save()
    fan = User.objects.create_user("fan@example.com", "Strong!Pass123", display_name="Fan", active_language="en")
    same = User.objects.create_user("same@example.com", "Strong!Pass123", display_name="Cùng tiếng Trung", active_language="zh")
    blocked = User.objects.create_user("x@example.com", "Strong!Pass123", active_language="zh")
    staff = User.objects.create_user("t@example.com", "Strong!Pass123", role="staff", active_language="zh")
    UserFollow.objects.create(follower=a, following=b)  # already followed
    UserFollow.objects.create(follower=fan, following=a)  # follows me: suggested first
    UserBlock.objects.create(blocker=blocked, blocked=a)

    ids = [p["id"] for p in client_for(a).get("/api/v1/community/users/suggestions/").data]
    # same language first, then others; never b (followed), the child, the blocker, staff or me
    assert ids == [same.id, fan.id]
    assert staff.id not in ids and kid.id not in ids and blocked.id not in ids
    assert client_for(kid).get("/api/v1/community/users/suggestions/").data == []


# ---- user IDs, friends, saved posts, answering requests from notifications

def test_every_user_has_a_distinct_8_digit_id(users):
    a, b, kid = users
    ids = {a.public_id, b.public_id, kid.public_id}
    assert len(ids) == 3 and all(len(i) == 8 and i.isdigit() and i[0] != "0" for i in ids)
    assert client_for(a).get("/api/v1/me/").data["public_id"] == a.public_id


def test_find_by_id_or_name_never_finds_children(users):
    a, b, kid = users
    ca = client_for(a)
    found = ca.get("/api/v1/community/users/search/", {"q": b.public_id}).data
    assert [p["id"] for p in found] == [b.id] and found[0]["friend_status"] == "none"
    assert [p["id"] for p in ca.get("/api/v1/community/users/search/", {"q": "#" + b.public_id}).data] == [b.id]
    assert [p["id"] for p in ca.get("/api/v1/community/users/search/", {"q": "Bìn"}).data] == [b.id]
    assert ca.get("/api/v1/community/users/search/", {"q": kid.public_id}).data == []
    # a child cannot look for strangers either
    assert client_for(kid).get("/api/v1/community/users/search/", {"q": "An"}).status_code == 403


def test_friend_request_notify_accept_then_message(users):
    a, b, kid = users
    ca, cb = client_for(a), client_for(b)
    res = ca.post(f"/api/v1/community/users/{b.id}/friend/", {"message": "Chào bạn, mình cũng học tiếng Trung"}, format="json")
    assert res.data["friend_status"] == "outgoing"
    rid = res.data["friend_request_id"]
    # b is told, with the hello, and can answer from the notification
    n = cb.get("/api/v1/notifications/").data["results"][0]
    assert n["kind"] == "friend_request" and n["body"].startswith("Chào bạn") and n["action_state"] == "pending"
    assert n["data"]["request_id"] == rid
    incoming = cb.get("/api/v1/community/users/friend-requests/").data
    assert [r["id"] for r in incoming] == [rid] and incoming[0]["user"]["id"] == a.id
    assert [r["id"] for r in ca.get("/api/v1/community/users/friend-requests/", {"box": "outgoing"}).data] == [rid]
    assert cb.get(f"/api/v1/community/users/{a.id}/profile/").data["friend_status"] == "incoming"
    # only the person asked can answer
    assert ca.post(f"/api/v1/community/users/friend-requests/{rid}/accept/").status_code == 404
    assert cb.post(f"/api/v1/community/users/friend-requests/{rid}/accept/").data["friend_status"] == "friends"
    assert a.notifications.filter(kind="friend_accept").count() == 1
    assert cb.get("/api/v1/notifications/").data["results"][0]["action_state"] == "accepted"
    assert [f["id"] for f in ca.get("/api/v1/community/users/friends/").data] == [b.id]
    assert ca.get(f"/api/v1/community/users/{b.id}/profile/").data["can_message"] is True  # friends may message
    # unfriend
    assert ca.delete(f"/api/v1/community/users/{b.id}/friend/").data["friend_status"] == "none"
    assert cb.get("/api/v1/community/users/friends/").data == []


def test_crossed_requests_make_friends_and_decline_is_silent(users):
    a, b, kid = users
    ca, cb = client_for(a), client_for(b)
    ca.post(f"/api/v1/community/users/{b.id}/friend/")
    assert cb.post(f"/api/v1/community/users/{a.id}/friend/").data["friend_status"] == "friends"
    ca.delete(f"/api/v1/community/users/{b.id}/friend/")
    rid = ca.post(f"/api/v1/community/users/{b.id}/friend/").data["friend_request_id"]
    assert cb.post(f"/api/v1/community/users/friend-requests/{rid}/decline/").data["friend_status"] == "none"
    assert not a.notifications.filter(title__contains="từ chối").exists()
    # never with a child, never after a block
    assert ca.post(f"/api/v1/community/users/{kid.id}/friend/").status_code == 400
    cb.post(f"/api/v1/community/users/{a.id}/block/")
    assert ca.post(f"/api/v1/community/users/{b.id}/friend/").status_code == 400


def test_save_posts_and_delete_comments(users):
    a, b, kid = users
    ca, cb = client_for(a), client_for(b)
    pid = ca.post("/api/v1/posts/", {"image": png(), "caption": "Quả táo"}, format="multipart").data["id"]
    assert cb.post(f"/api/v1/posts/{pid}/bookmark/").data == {"saved": True}
    saved = cb.get("/api/v1/posts/", {"saved": "1"}).data["results"]
    assert [p["id"] for p in saved] == [pid] and saved[0]["saved"] is True
    assert ca.get("/api/v1/posts/", {"saved": "1"}).data["results"] == []  # only mine
    cb.delete(f"/api/v1/posts/{pid}/bookmark/")
    assert cb.get("/api/v1/posts/", {"saved": "1"}).data["results"] == []
    cid = cb.post(f"/api/v1/posts/{pid}/comments/", {"content": "Ngon"}, format="json").data["id"]
    other = User.objects.create_user("c@example.com", "Strong!Pass123", display_name="Chi")
    assert client_for(other).delete(f"/api/v1/posts/{pid}/comments/{cid}/").status_code == 403
    assert cb.get(f"/api/v1/posts/{pid}/comments/").data[0]["can_delete"] is True
    assert ca.delete(f"/api/v1/posts/{pid}/comments/{cid}/").status_code == 204  # the post's author may
    assert cb.get(f"/api/v1/posts/{pid}/comments/").data == []


def test_group_request_with_intro_answered_from_notification(users):
    a, b, kid = users
    ca, cb = client_for(a), client_for(b)
    gid = ca.post("/api/v1/groups/", {"name": "HSK 3", "require_approval": True}, format="json").data["id"]
    assert cb.post(f"/api/v1/groups/{gid}/join/", {"message": "Mình học HSK 2 rồi"}, format="json").data["status"] == "pending"
    n = ca.get("/api/v1/notifications/").data["results"][0]
    assert n["kind"] == "group_request" and n["body"] == "Mình học HSK 2 rồi" and n["action_state"] == "pending"
    mid = n["data"]["member_id"]
    assert cb.post(f"/api/v1/groups/{gid}/members/{mid}/approve/").status_code == 403  # not the leader
    assert ca.post(f"/api/v1/groups/{gid}/members/{mid}/approve/").data["status"] == "active"
    assert ca.get("/api/v1/notifications/").data["results"][0]["action_state"] == "accepted"
    assert b.notifications.filter(kind="group", title__contains="được duyệt").count() == 1
    # a rejected request is told so, and can be sent again
    cb.post(f"/api/v1/groups/{gid}/leave/")
    cb.post(f"/api/v1/groups/{gid}/join/", {"message": "Cho mình vào lại"}, format="json")
    mid = GroupMember.objects.get(group_id=gid, user=b).id
    ca.post(f"/api/v1/groups/{gid}/members/{mid}/reject/")
    assert b.notifications.filter(kind="group", title__contains="chưa được duyệt").count() == 1
    assert ca.get("/api/v1/notifications/").data["results"][0]["action_state"] == "gone"
