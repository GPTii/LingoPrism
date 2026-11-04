import io
import json
import zipfile
from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.community.models import FriendRequest, Group, GroupMember
from apps.notifications.models import Notification

from .models import Assignment

pytestmark = pytest.mark.django_db


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


@pytest.fixture(autouse=True)
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def klass():
    """Lan creates a group and adds Minh and Hoa – the three-person class of the feature request."""
    lan, minh, hoa = (User.objects.create_user(f"{n}@example.com", "Strong!Pass123", display_name=n.title())
                      for n in ("lan", "minh", "hoa"))
    g = client_for(lan).post("/api/v1/groups/", {"name": "Lớp tiếng Trung", "is_private": True}, format="json").data
    group = Group.objects.get(pk=g["id"])
    for u in (minh, hoa):
        GroupMember.objects.create(group=group, user=u, status="active")
    return group, lan, minh, hoa


QUESTIONS = [
    {"kind": "mcq", "prompt": "苹果 nghĩa là?", "options": [{"text": "quả táo", "correct": True}, {"text": "quả cam"}],
     "points": 2},
    {"kind": "fill", "prompt": "Viết pinyin của 你好", "accepted_answers": ["nǐ hǎo", "ni hao"], "points": 1},
    {"kind": "essay", "prompt": "Giới thiệu bản thân bằng 3 câu", "points": 3},
]


def make(lan, group, **extra):
    data = {"group": group.id, "title": "Bài 1", "instructions": "Làm hết nhé", "questions": QUESTIONS, **extra}
    return client_for(lan).post("/api/v1/assignments/", data, format="json")


def test_leader_gives_marks_and_returns_work(klass):
    group, lan, minh, hoa = klass
    res = make(lan, group)
    assert res.status_code == 201, res.data
    aid = res.data["id"]
    assert res.data["max_score"] == 6 and res.data["status"] == "draft"
    cm = client_for(minh)
    assert cm.get(f"/api/v1/assignments/?group={group.id}").data == []  # a draft is the leaders' business
    assert client_for(lan).post(f"/api/v1/assignments/{aid}/publish/").data["status"] == "published"
    assert minh.notifications.filter(kind="assignment").count() == 1

    detail = cm.get(f"/api/v1/assignments/{aid}/").data
    assert "correct" not in detail["questions"][0]["options"][0] and "accepted_answers" not in detail["questions"][1]
    q = [x["id"] for x in detail["questions"]]
    sub = cm.post(f"/api/v1/assignments/{aid}/submit/", {"answers": [
        {"question": q[0], "selected_option": 0}, {"question": q[1], "text": "  Ni  Hao "},
        {"question": q[2], "text": "我叫明。我是越南人。我喜欢学习。"}]}, format="json").data["my_submission"]
    assert sub["status"] == "submitted" and sub["score"] is None  # the essay waits for a leader
    assert [a["is_correct"] for a in sub["answers"]] == [True, True, None]
    assert lan.notifications.filter(kind="assignment").count() == 1

    rows = client_for(lan).get(f"/api/v1/assignments/{aid}/submissions/").data
    assert {r["user"]["display_name"]: bool(r["submission"]) for r in rows} == {"Minh": True, "Hoa": False}
    essay = next(a for a in sub["answers"] if a["question"] == q[2])
    graded = client_for(lan).post(f"/api/v1/assignments/{aid}/submissions/{sub['id']}/grade/",
                                  {"answers": [{"answer": essay["id"], "score": 2.5, "feedback": "Tốt"}],
                                   "feedback": "Cố gắng thêm"}, format="json")
    assert graded.status_code == 200, graded.data
    assert graded.data["status"] == "graded" and float(graded.data["score"]) == 5.5
    assert minh.notifications.filter(title="Bài tập đã được chấm").exists()

    after = cm.get(f"/api/v1/assignments/{aid}/").data
    assert after["questions"][0]["options"][0]["correct"] is True  # answers shown once marked
    assert cm.post(f"/api/v1/assignments/{aid}/submit/", {"answers": []}, format="json").status_code == 400
    assert client_for(lan).post(f"/api/v1/assignments/{aid}/submissions/{sub['id']}/grade/",
                                {"answers": [{"answer": essay["id"], "score": 9}]}, format="json").status_code == 400
    book = client_for(lan).get(f"/api/v1/assignments/gradebook/?group={group.id}").data
    assert [r["average"] for r in book["rows"]] == [91.7, None]
    assert len(client_for(hoa).get(f"/api/v1/assignments/gradebook/?group={group.id}").data["rows"]) == 1


def test_only_leaders_give_work_and_only_members_do_it(klass):
    group, lan, minh, hoa = klass
    assert make(minh, group).status_code == 403
    aid = make(lan, group).data["id"]
    outsider = User.objects.create_user("o@example.com", "Strong!Pass123")
    assert client_for(outsider).get(f"/api/v1/assignments/{aid}/").status_code == 404
    bad = make(lan, group, questions=[{"kind": "mcq", "prompt": "?", "options": [{"text": "a"}, {"text": "b"}]}])
    assert client_for(lan).post(f"/api/v1/assignments/{bad.data['id']}/publish/").status_code == 400  # no right choice


def test_auto_marked_work_is_final_and_late_work_is_flagged_or_refused(klass):
    group, lan, minh, hoa = klass
    aid = make(lan, group, questions=QUESTIONS[:2], due_at=(timezone.now() - timedelta(hours=1)).isoformat(),
               allow_late=True).data["id"]
    client_for(lan).post(f"/api/v1/assignments/{aid}/publish/")
    q = [x["id"] for x in client_for(minh).get(f"/api/v1/assignments/{aid}/").data["questions"]]
    sub = client_for(minh).post(f"/api/v1/assignments/{aid}/submit/", {"answers": [
        {"question": q[0], "selected_option": 1}, {"question": q[1], "text": "ni hao"}]}, format="json").data["my_submission"]
    assert sub["status"] == "graded" and sub["late"] and float(sub["score"]) == 1 and sub["graded_at"]
    assert client_for(minh).post(f"/api/v1/assignments/{aid}/submit/", {"answers": []}, format="json").status_code == 400
    Assignment.objects.filter(pk=aid).update(allow_late=False)
    assert client_for(hoa).post(f"/api/v1/assignments/{aid}/submit/", {"answers": []}, format="json").status_code == 400


def test_a_worksheet_handed_in_as_a_file(klass):
    group, lan, minh, hoa = klass
    aid = client_for(lan).post("/api/v1/assignments/", {"group": group.id, "title": "Phiếu bài tập", "points": 10},
                               format="json").data["id"]
    up = client_for(lan).post(f"/api/v1/assignments/{aid}/attachment/",
                              {"file": SimpleUploadedFile("phieu.pdf", b"%PDF-1.4", "application/pdf")})
    assert up.status_code == 200 and up.data["attachment_name"] == "phieu.pdf"
    assert client_for(lan).post(f"/api/v1/assignments/{aid}/attachment/",
                                {"file": SimpleUploadedFile("x.exe", b"MZ")}).status_code == 400
    client_for(lan).post(f"/api/v1/assignments/{aid}/publish/")
    res = client_for(minh).post(f"/api/v1/assignments/{aid}/submit/",
                                {"text": "Em nộp bài ạ", "file": SimpleUploadedFile("bai.jpg", b"\xff\xd8", "image/jpeg")})
    sub = res.data["my_submission"]
    assert sub["status"] == "submitted" and sub["attachment_name"] == "bai.jpg" and sub["attachment"].startswith("http")
    assert "bai" not in sub["attachment"].rsplit("/", 1)[1]  # stored under a random name
    assert client_for(lan).post(f"/api/v1/assignments/{aid}/submissions/{sub['id']}/grade/", {"feedback": "?"},
                                format="json").status_code == 400  # needs a score
    done = client_for(lan).post(f"/api/v1/assignments/{aid}/submissions/{sub['id']}/grade/", {"score": 8},
                                format="json").data
    assert done["status"] == "graded" and done["percent"] == 80.0


def test_leader_adds_a_friend_at_once_and_invites_a_stranger(klass):
    group, lan, minh, hoa = klass
    friend = User.objects.create_user("f@example.com", "Strong!Pass123", display_name="Bạn")
    stranger = User.objects.create_user("s@example.com", "Strong!Pass123", display_name="Lạ")
    kid = User.objects.create_user("k@example.com", "Strong!Pass123", learner_type="kid")
    FriendRequest.objects.create(from_user=lan, to_user=friend, status="accepted")
    cl = client_for(lan)
    url = f"/api/v1/groups/{group.id}/members/add/"
    assert cl.post(url, {"user": friend.public_id}, format="json").data["status"] == "active"
    assert cl.post(url, {"user": stranger.public_id}, format="json").data["status"] == "invited"
    assert cl.post(url, {"user": kid.public_id}, format="json").status_code == 400
    assert cl.post(url, {"user": "00000000"}, format="json").status_code == 404
    assert client_for(minh).post(url, {"user": stranger.public_id}, format="json").status_code == 403  # leaders only
    # a private group is invisible to others, visible to the invited person, who accepts by joining
    other = User.objects.create_user("x@example.com", "Strong!Pass123")
    assert group.id not in [g["id"] for g in client_for(other).get("/api/v1/groups/").data["results"]]
    assert client_for(other).post(f"/api/v1/groups/{group.id}/join/").status_code in (403, 404)
    cs = client_for(stranger)
    assert group.id in [g["id"] for g in cs.get("/api/v1/groups/").data["results"]]
    assert stranger.notifications.filter(kind=Notification.Kind.GROUP).exists()
    assert cs.post(f"/api/v1/groups/{group.id}/join/").data["status"] == "active"


def test_a_promoted_member_can_give_work(klass):
    group, lan, minh, hoa = klass
    m = GroupMember.objects.get(group=group, user=minh)
    assert client_for(lan).post(f"/api/v1/groups/{group.id}/members/{m.id}/promote/").data["role"] == "leader"
    assert make(minh, group).status_code == 201
    creator = GroupMember.objects.get(group=group, user=lan)
    assert client_for(minh).post(f"/api/v1/groups/{group.id}/members/{creator.id}/demote/").status_code == 400


def test_exercise_file_becomes_draft_questions(klass, settings, monkeypatch):
    from apps.aitalk import generator

    group, lan, minh, hoa = klass
    settings.GEMINI_API_KEY = "g"
    sent = {}

    def fake(prompt, **kw):
        sent.update(prompt=prompt, parts=kw.get("parts"))
        return json.dumps({"title": "Unit 1", "questions": [
            {"kind": "mcq", "prompt": "Choose", "options": [{"text": "a", "correct": True}, {"text": "b", "correct": True}]},
            {"kind": "fill", "prompt": "I ___ a student", "accepted_answers": ["am"], "points": 2},
            {"kind": "weird", "prompt": "Write about your family"}]}), "gemini-test"

    monkeypatch.setattr(generator, "_gemini", fake)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", '<w:document><w:body><w:p><w:r><w:t>1. I ___ a student</w:t></w:r></w:p>'
                                        '</w:body></w:document>')
    res = client_for(lan).post("/api/v1/assignments/import/", {"group": group.id, "file": SimpleUploadedFile(
        "unit1.docx", buf.getvalue())})
    assert res.status_code == 200, res.data
    assert "I ___ a student" in sent["prompt"] and sent["parts"] is None  # Word: its text is sent
    qs = res.data["questions"]
    assert [q["kind"] for q in qs] == ["mcq", "fill", "essay"]
    assert not any(o["correct"] for o in qs[0]["options"])  # two "right" choices: the leader decides
    pdf = client_for(lan).post("/api/v1/assignments/import/", {"group": group.id, "file": SimpleUploadedFile(
        "de.pdf", b"%PDF-1.4")})
    assert pdf.status_code == 200 and sent["parts"][0]["inline_data"]["mime_type"] == "application/pdf"
    assert client_for(minh).post("/api/v1/assignments/import/", {"group": group.id, "file": SimpleUploadedFile(
        "x.txt", b"hi")}).status_code == 403
