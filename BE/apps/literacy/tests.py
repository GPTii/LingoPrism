import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.literacy import curriculum as cur
from apps.literacy import exercises as ex
from apps.vocab.lang import vi_phonics as ph

pytestmark = pytest.mark.django_db


@pytest.fixture
def kid():
    user = User.objects.create_user("kid@example.com", "Strong!Pass123", learner_type="kid", active_language="vi")
    client = APIClient()
    client.force_authenticate(user)
    return user, client


def right_answer(item):
    data = ex.unsign(item["token"])
    if item["type"] == "build":
        s = ph.parse(data["a"])
        return {"onset": s.onset or "∅", "rhyme": s.rhyme, "tone": s.tone}
    return data["a"]


def test_every_lesson_only_uses_taught_real_syllables():
    for lesson in cur.LESSONS:
        n = lesson["n"]
        t = cur.taught_until(n)
        data = ex.build_lesson(n, seed=7)
        assert data["exercises"], f"bài {n} không có bài tập"
        for item in data["exercises"]:
            expected = ex.unsign(item["token"])["a"]
            if item["type"] in ("listen_choose", "build", "dictation", "sentence"):
                for syl in ph.syllables_of(expected):
                    s = ph.parse(syl)
                    assert s is not None and t.readable(s), (n, item["type"], syl)
            if item["type"] == "listen_choose":
                assert expected in item["options"]


def test_lesson_flow_unlocks_next(kid):
    user, client = kid
    lessons = client.get("/api/v1/literacy/lessons/").data["lessons"]
    assert lessons[0]["status"] == "open" and lessons[1]["status"] == "locked"
    assert client.get("/api/v1/literacy/lessons/2/").status_code == 403

    lesson = client.get("/api/v1/literacy/lessons/1/").data
    assert lesson["intro"][0]["unit"]["code"] == "a"
    for item in lesson["exercises"]:
        res = client.post("/api/v1/literacy/check/", {"token": item["token"], "answer": right_answer(item)}, format="json")
        assert res.status_code == 200 and res.data["correct"], (item["type"], res.data)
    res = client.post("/api/v1/literacy/lessons/1/finish/", {"session": lesson["session"], "total": len(lesson["exercises"])},
                      format="json")
    assert res.data["passed"] and res.data["stars"] == 3
    assert client.get("/api/v1/literacy/lessons/").data["lessons"][1]["status"] == "open"


def test_check_build_dictation_and_tampering(kid):
    _, client = kid
    token = ex.sign(t="build", a="bà", l=1, s="abc", i=1, u="am:b")
    res = client.post("/api/v1/literacy/check/", {"token": token, "answer": {"onset": "b", "rhyme": "a", "tone": "sac"}}, format="json")
    assert not res.data["correct"] and res.data["given"] == "bá" and res.data["spell"][-1] == "bà"

    token = ex.sign(t="dictation", a="con mèo", l=8, s="abc", i=2, u="am:m")
    res = client.post("/api/v1/literacy/check/", {"token": token, "answer": "Con Meo"}, format="json")
    assert not res.data["correct"]
    assert res.data["diff"][1] == {"expected": "mèo", "given": "meo", "ok": False, "hint": "sai dấu thanh"}
    res = client.post("/api/v1/literacy/check/", {"token": token, "answer": "con mèo."}, format="json")
    assert res.data["correct"]
    # tone mark placement variants are the same word (hoà / hòa)
    token = ex.sign(t="dictation", a="hòa", l=45, s="abc", i=3, u="van:oa")
    assert client.post("/api/v1/literacy/check/", {"token": token, "answer": "hoà"}, format="json").data["correct"]

    assert client.post("/api/v1/literacy/check/", {"token": token + "x", "answer": "hòa"}, format="json").status_code == 400
