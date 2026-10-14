from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.learning.models import PersonalWord, ReviewLog
from apps.learning.scheduling import CardState, LeitnerScheduler
from apps.vocab.models import Language, ReviewStatus, Topic, TopicWord, Word, WordTranslation


def test_leitner_scheduler():
    now = timezone.now()
    s = LeitnerScheduler()
    state, due = s.review(CardState(), True, 4, now)
    assert (state.stage, state.interval_days) == (1, 3) and due == now + timedelta(days=3)
    state, due = s.review(state, False, 1, now)
    assert (state.stage, state.interval_days, state.lapses, state.wrong_streak) == (0, 1, 1, 1)


@pytest.fixture
def setup(db):
    for code in ("vi", "en", "zh-Hans", "zh-Hant"):
        Language.objects.create(code=code, name=code, native_name=code, tts_locale=code)
    topic = Topic.objects.create(slug="animals", name_vi="Động vật")
    for i, (vi, en) in enumerate([("mèo", "cat"), ("chó", "dog"), ("gà", "chicken"), ("vịt", "duck")]):
        w = Word.objects.create(slug=en)
        TopicWord.objects.create(topic=topic, word=w, order=i)
        WordTranslation.objects.create(word=w, language_id="vi", text=vi, status=ReviewStatus.VERIFIED)
        WordTranslation.objects.create(word=w, language_id="en", text=en, status=ReviewStatus.VERIFIED)
    user = User.objects.create_user("l@example.com", "Strong!Pass123", active_language="en")
    client = APIClient()
    client.force_authenticate(user)
    return user, client, topic


def test_learn_session_flow(setup):
    user, client, topic = setup
    res = client.post("/api/v1/sessions/", {"kind": "learn", "size": 3}, format="json")
    assert res.status_code == 201, res.data
    session = res.data
    assert len(session["items"]) == 3
    types = {q["type"] for q in session["items"][0]["questions"]}
    assert {"flashcard", "choose_target", "choose_meaning", "type_target"} <= types

    first, second = session["items"][0], session["items"][1]
    client.post(f"/api/v1/sessions/{session['id']}/answer/",
                {"personal_word": first["personal_word"], "question_type": "type_target", "correct": True, "graded": True},
                format="json")
    client.post(f"/api/v1/sessions/{session['id']}/answer/",
                {"personal_word": second["personal_word"], "question_type": "choose_target", "correct": False, "graded": True},
                format="json")
    p1, p2 = PersonalWord.objects.get(id=first["personal_word"]), PersonalWord.objects.get(id=second["personal_word"])
    assert (p1.stage, p1.interval_days, p1.status) == (1, 3, "learning")
    assert (p2.stage, p2.interval_days, p2.lapses) == (0, 1, 1)
    assert ReviewLog.objects.filter(user=user).count() == 2

    summary = client.post(f"/api/v1/sessions/{session['id']}/finish/").data
    assert summary["completed_count"] == 2 and summary["correct_first_try"] == 1
    assert summary["needs_more_practice"] == [p2.id]


def test_review_only_due(setup):
    user, client, topic = setup
    assert client.post("/api/v1/sessions/", {"kind": "review"}, format="json").status_code == 400
    w = Word.objects.get(slug="cat")
    PersonalWord.objects.create(user=user, word=w, language="en", status="learning", due_at=timezone.now() - timedelta(hours=1))
    res = client.post("/api/v1/sessions/", {"kind": "review"}, format="json")
    assert res.status_code == 201 and len(res.data["items"]) == 1
    assert client.get("/api/v1/my-words/summary/").data["due"] == 1
