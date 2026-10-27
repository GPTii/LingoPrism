"""Access control and robustness over EVERY API route, found by walking the URL conf (a new endpoint is covered without
being listed here):

* signed out: every route answers 401, except the few that are public on purpose;
* a learner on staff/admin routes: never a 2xx;
* learner B on learner A's own things (photos, study sessions, messages, exams, support, group chat…): never a 2xx,
  and A's data is unchanged (BOLA / IDOR, OWASP API1);
* junk in the body and the query string of every route, as a learner and as an admin: never a 500.
"""
import re

import pytest
from django.urls import get_resolver
from django.urls.resolvers import URLResolver
from rest_framework.test import APIClient

from apps.accounts.models import User

pytestmark = pytest.mark.django_db

PUBLIC = {  # reachable signed out, on purpose
    "api/v1/health/", "api/v1/auth/register/", "api/v1/auth/login/", "api/v1/auth/google/",
    "api/v1/auth/google/config/", "api/v1/auth/refresh/", "api/v1/auth/logout/", "api/v1/auth/password/forgot/",
    "api/v1/auth/password/verify/", "api/v1/auth/password/reset/", "api/v1/languages/", "api/v1/releases/",
}
STAFF_ONLY = re.compile(r"^api/v1/(admin/|pois/stats/)")
SKIP_FOR_ADMIN = re.compile(r"^api/v1/admin/(algorithms/run/|league-tiers/close-week/|broadcast/)")  # slow / fan-out
PARAMS = {"pk": "999999", "n": "1", "kind": "vip", "decision": "accept", "req_id": "999999", "member_id": "999999",
          "comment_id": "999999", "user_id": "999999", "group_id": "999999"}
JUNK_BODY = {"id": "x", "pk": [], "code": {"a": 1}, "email": 123, "password": None, "total": "abc", "answer": None,
             "message": {"a": 1}, "page": -1, "lat": "abc", "lng": "abc", "items": "x", "session": 5, "word": "x",
             "language": "xx", "decision": 1, "is_active": "maybe", "date": "not-a-date"}
JUNK_QUERY = ("?page=abc&page_size=-1&before=abc&after=abc&lat=abc&lng=abc&radius=abc&q=%00%27%22&limit=abc&offset=abc"
              "&language=xx&date=not-a-date&ordering=nonexistent_field&category=999")


def routes():
    """(path, methods) for every api/v1 route, with path parameters filled in."""
    def walk(patterns, prefix=""):
        for p in patterns:
            if isinstance(p, URLResolver):
                yield from walk(p.url_patterns, prefix + str(p.pattern))
            else:
                yield prefix + str(p.pattern), p

    out = []
    for raw, pattern in walk(get_resolver().url_patterns):
        if not raw.startswith("api/v1/") or "format" in raw:
            continue
        path = raw.replace("^", "").replace("$", "")
        # a choice like (?P<decision>accept|decline) takes its first option, any other parameter a made-up value
        path = re.sub(r"\(\?P<(\w+)>([a-z_]+)(?:\|[a-z_|]+)?\)", lambda m: m.group(2), path)
        path = re.sub(r"\(\?P<(\w+)>[^)]*\)", lambda m: PARAMS.get(m.group(1), "999999"), path)
        path = re.sub(r"<(?:\w+:)?(\w+)>", lambda m: PARAMS.get(m.group(1), "999999"), path)
        actions = getattr(pattern.callback, "actions", None)
        if actions:
            methods = sorted(m for m in actions if m in ("get", "post", "put", "patch", "delete"))
        else:
            cls = getattr(pattern.callback, "cls", None) or getattr(pattern.callback, "view_class", None)
            methods = [m for m in ("get", "post", "put", "patch", "delete") if cls and hasattr(cls, m)]
        out.append((path, methods))
    return out


def call(client, method, path, junk=False):
    url = "/" + path + (JUNK_QUERY if junk and method == "get" else "")
    if method == "get":
        return client.get(url)
    return getattr(client, method)(url, JUNK_BODY if junk else {}, format="json")


@pytest.fixture
def learners():
    a = User.objects.create_user(email="a@example.com", password="Strong!Pass123", display_name="A", birth_date="1990-01-01")
    b = User.objects.create_user(email="b@example.com", password="Strong!Pass123", display_name="B", birth_date="1990-01-01")
    return a, b


def as_user(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


def test_every_route_is_closed_when_signed_out():
    open_routes = []
    for path, methods in routes():
        if path in PUBLIC or path == "api/v1/":
            continue
        for m in methods:
            res = call(APIClient(), m, path)
            if res.status_code != 401:
                open_routes.append(f"{m.upper()} /{path} -> {res.status_code}")
    assert not open_routes, "answer without signing in:\n" + "\n".join(open_routes)


def test_learner_never_gets_through_a_staff_route(learners):
    a, _ = learners
    client = as_user(a)
    leaked = []
    for path, methods in routes():
        if not STAFF_ONLY.match(path):
            continue
        for m in methods:
            res = call(client, m, path)
            if res.status_code < 400:
                leaked.append(f"{m.upper()} /{path} -> {res.status_code}")
    # POIs are read by everyone (the map) but written only by staff
    for m in ("post", "put", "patch", "delete"):
        res = call(client, m, "api/v1/pois/" if m == "post" else "api/v1/pois/999999/")
        if res.status_code < 400 or res.status_code == 404:
            leaked.append(f"{m.upper()} pois -> {res.status_code}")
    assert not leaked, "a learner got through:\n" + "\n".join(leaked)


def make_things(a):
    """Learner A's own things, and every way to touch them: [(method, path)], plus the objects."""
    from apps.chat.models import DirectMessage, DirectThread, GroupMessage, SupportConversation
    from apps.community.models import Group, GroupMember, Post, PostComment
    from apps.detection.models import Detection, Photo
    from apps.learning.models import StudySession
    from apps.notifications.models import Notification
    from apps.quizzes.models import Exam, Submission
    from apps.vocab.models import Language

    photo = Photo.objects.create(user=a, image="photos/a.jpg")
    det = Detection.objects.create(user=a, photo=photo, model_name="m", device="server")
    sess = StudySession.objects.create(user=a, language="en", kind="learn")
    note = Notification.objects.create(user=a, kind="system", title="secret")
    lang, _ = Language.objects.get_or_create(code="en", defaults={"name": "English", "native_name": "English", "tts_locale": "en-US"})
    sub = Submission.objects.create(user=a, exam=Exam.objects.create(title="t", language=lang))
    support = SupportConversation.objects.create(learner=a)
    third = User.objects.create_user(email="c@example.com", password="Strong!Pass123", birth_date="1990-01-01")
    thread = DirectThread.objects.create(user_a=a, user_b=third)
    DirectMessage.objects.create(thread=thread, sender=a, **({"text": "secret"} if hasattr(DirectMessage, "text") else {}))
    group = Group.objects.create(name="private", created_by=a, require_approval=True)
    GroupMember.objects.create(group=group, user=a, role="leader", status="active")
    GroupMessage.objects.create(group=group, user=a, **({"text": "secret"} if hasattr(GroupMessage, "text") else {}))
    post = Post.objects.create(user=a, image="posts/a.jpg", visibility="followers")
    comment = PostComment.objects.create(post=post, user=a, **({"text": "mine"} if hasattr(PostComment, "text") else {}))

    attempts = [
        ("get", f"detections/{det.id}/"), ("post", f"detections/{det.id}/confirm/"), ("post", f"detections/{det.id}/dialogue/"),
        ("get", f"sessions/{sess.id}/"), ("post", f"sessions/{sess.id}/answer/"), ("post", f"sessions/{sess.id}/finish/"),
        ("post", f"notifications/{note.id}/read/"),
        ("get", f"submissions/{sub.id}/"), ("post", f"submissions/{sub.id}/submit/"),
        ("get", f"support/conversations/{support.id}/"), ("get", f"support/conversations/{support.id}/messages/"),
        ("post", f"support/conversations/{support.id}/messages/"), ("post", f"support/conversations/{support.id}/close/"),
        ("get", f"messages/threads/{thread.id}/"), ("get", f"messages/threads/{thread.id}/messages/"),
        ("post", f"messages/threads/{thread.id}/messages/"), ("post", f"messages/threads/{thread.id}/read/"),
        ("get", f"groups/{group.id}/messages/"), ("post", f"groups/{group.id}/messages/"),
        ("patch", f"groups/{group.id}/"), ("delete", f"groups/{group.id}/"),
        ("post", f"groups/{group.id}/members/{GroupMember.objects.get(user=a).id}/remove/"),
        ("get", f"posts/{post.id}/"), ("delete", f"posts/{post.id}/"), ("get", f"posts/{post.id}/comments/"),
        ("delete", f"posts/{post.id}/comments/{comment.id}/"),
    ]
    return attempts, dict(group=group, post=post, comment=comment, note=note)


def test_no_learner_can_reach_another_learners_things(learners):
    from apps.community.models import GroupMember, Post, PostComment
    from apps.notifications.models import Notification

    a, b = learners
    attempts, o = make_things(a)
    group, post, comment, note = o["group"], o["post"], o["comment"], o["note"]
    client = as_user(b)
    leaked = []
    for method, path in attempts:
        body = {"text": "hi", "answer": "x", "label": "cat", "name": "hacked", "content": "hi"}
        res = getattr(client, method)("/api/v1/" + path, body, format="json") if method != "get" else client.get("/api/v1/" + path)
        if res.status_code < 400:
            leaked.append(f"{method.upper()} /api/v1/{path} -> {res.status_code}")
    assert not leaked, "learner B reached learner A's data:\n" + "\n".join(leaked)
    group.refresh_from_db()
    assert group.name == "private" and Post.objects.filter(pk=post.pk).exists() and PostComment.objects.filter(pk=comment.pk).exists()
    assert GroupMember.objects.filter(group=group, user=a).exists() and Notification.objects.get(pk=note.pk).read_at is None


@pytest.mark.parametrize("who", ["learner", "admin"])
def test_junk_input_never_breaks_a_route(learners, who):
    if who == "admin":
        user = User.objects.create_user(email="admin@example.com", password="Strong!Pass123", role="admin",
                                        is_staff=True, is_superuser=True)
    else:
        user = learners[0]
    client = as_user(user)
    broken = []
    for path, methods in routes():
        if who == "admin" and SKIP_FOR_ADMIN.match(path):
            continue
        for m in methods:
            if path == "api/v1/auth/logout/" or (path == "api/v1/me/" and m == "delete"):
                continue  # would end the session / the account under test
            for junk in (False, True):
                try:
                    res = call(client, m, path, junk=junk)
                    code = res.status_code
                except Exception as e:  # an exception the test client re-raises is a 500 in production
                    code = f"{type(e).__name__}: {str(e)[:80]}"
                if not isinstance(code, int) or code >= 500:
                    broken.append(f"{m.upper()} /{path}{' (junk)' if junk else ''} -> {code}")
    assert not broken, f"500 for {who}:\n" + "\n".join(broken)


def test_junk_on_my_own_things_never_breaks(learners):
    """The owner gets past the access checks, so junk reaches the real code behind each route."""
    a, _ = learners
    attempts, _ = make_things(a)
    client = as_user(a)
    broken = []
    for method, path in attempts:
        for junk in (False, True):
            try:
                code = call(client, method, "api/v1/" + path, junk=junk).status_code
            except Exception as e:
                code = f"{type(e).__name__}: {str(e)[:80]}"
            if not isinstance(code, int) or code >= 500:
                broken.append(f"{method.upper()} /api/v1/{path}{' (junk)' if junk else ''} -> {code}")
    assert not broken, "500 on the owner's own data:\n" + "\n".join(broken)
