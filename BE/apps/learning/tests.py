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
    # default scheduler is SM-2 (apps.algorithms): first success → 1 day, a lapse → back to 1 day
    assert (p1.stage, p1.interval_days, p1.status) == (1, 1, "learning")
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


def test_sentence_lesson_and_check(setup):
    from apps.learning.models import SentenceAttempt
    from apps.vocab.lang.sentences import tokens_latin, word_spans
    from apps.vocab.models import ExampleSentence

    user, client, topic = setup
    texts = [("cat", "The cat is sleeping.", "Con mèo đang ngủ."), ("dog", "My dog likes water.", "Con chó của tôi thích nước."),
             ("chicken", "We ate chicken today.", "Hôm nay chúng tôi ăn gà."), ("duck", "A duck is swimming.", "Một con vịt đang bơi.")]
    for i, (slug, text, vi) in enumerate(texts):
        toks = tokens_latin(text, "en")
        ExampleSentence.objects.create(word=Word.objects.get(slug=slug), language_id="en", text=text, translation_vi=vi,
                                       source="tatoeba", source_id=str(i + 1), tokens=toks, target_tokens=word_spans(toks, slug, "en"),
                                       status=ReviewStatus.VERIFIED)
    ExampleSentence.objects.create(word=Word.objects.get(slug="cat"), language_id="en", text="Hidden cat.", source="tatoeba",
                                   source_id="99", status=ReviewStatus.FLAGGED)

    res = client.get("/api/v1/sentences/lesson/", {"topic": topic.id, "size": 4})
    assert res.status_code == 200, res.data
    ex = res.data["exercises"]
    assert len(ex) == 4 and {e["type"] for e in ex} >= {"arrange", "listen"}
    assert all("Hidden" not in str(e) for e in ex)

    arrange = next(e for e in ex if e["type"] == "arrange")
    sentence = ExampleSentence.objects.get(pk=arrange["id"])
    words = [t["t"] for t in sentence.tokens if not t.get("x")]
    res = client.post("/api/v1/sentences/check/", {"sentence": sentence.id, "type": "arrange", "answer": words}, format="json")
    assert res.data["correct"] and res.data["xp"] > 0
    res = client.post("/api/v1/sentences/check/", {"sentence": sentence.id, "type": "arrange", "answer": words[::-1]}, format="json")
    assert not res.data["correct"]
    res = client.post("/api/v1/sentences/check/", {"sentence": sentence.id, "type": "fill", "answer": sentence.word.slug.upper()}, format="json")
    assert res.data["correct"] and res.data["answer"] == sentence.word.slug
    res = client.post("/api/v1/sentences/check/", {"sentence": sentence.id, "type": "meaning", "answer": sentence.translation_vi}, format="json")
    assert res.data["correct"]
    assert SentenceAttempt.objects.filter(user=user).count() == 4


def test_chinese_learner_never_gets_english(setup):
    """Learners are Vietnamese: a Chinese sentence is translated into Vietnamese or not at all."""
    from apps.vocab.models import ExampleSentence

    user, client, topic = setup
    user.active_language, user.zh_script = "zh", "hans"
    user.save()
    for i, (slug, zh) in enumerate([("cat", "猫"), ("dog", "狗"), ("chicken", "鸡"), ("duck", "鸭")]):
        w = Word.objects.get(slug=slug)
        WordTranslation.objects.create(word=w, language_id="zh-Hans", text=zh, pinyin="x", status=ReviewStatus.VERIFIED)
        text = f"我有一只{zh}。"
        toks = [{"t": ch, "p": "x"} for ch in "我有一只"] + [{"t": zh, "p": "x"}, {"t": "。", "x": 1}]
        ExampleSentence.objects.create(
            word=w, language_id="zh-Hans", text=text, source="tatoeba", source_id=str(i + 1), tokens=toks,
            target_tokens=[4], translation_en=f"I have a {slug}.", status=ReviewStatus.VERIFIED,
            translation_vi=f"Tôi có một con {slug}." if i < 2 else "")

    ex = client.get("/api/v1/sentences/lesson/", {"topic": topic.id, "size": 8}).data["exercises"]
    assert ex and "I have a" not in str(ex)
    for e in ex:
        if e["type"] in ("arrange", "meaning"):
            assert ExampleSentence.objects.get(pk=e["id"]).translation_vi
        prompt = e.get("prompt") or {}
        assert prompt.get("language", "vi") == "vi"

    cards = client.get(f"/api/v1/topics/{topic.id}/words/").data
    cards = cards.get("results", cards) if isinstance(cards, dict) else cards
    assert cards and all(c["english"] is None for c in cards)
    assert "I have a" not in str(cards)


def test_levels_path_unlock_and_test(setup):
    """Level 2 opens at 70 % of level 1 started, or by passing the skip test; new words come from the current level."""
    user, client, topic = setup
    levels = {"cat": 1, "dog": 1, "chicken": 2, "duck": 2}
    for slug, n in levels.items():
        w = Word.objects.get(slug=slug)
        w.levels = {"en": n, "zh": n, "vi": n}
        w.save()
    for i, (vi, en) in enumerate([("ngựa", "horse"), ("bò", "cow")]):
        w = Word.objects.create(slug=en, levels={"en": 2, "zh": 2, "vi": 2})
        WordTranslation.objects.create(word=w, language_id="vi", text=vi, status=ReviewStatus.VERIFIED)
        WordTranslation.objects.create(word=w, language_id="en", text=en, status=ReviewStatus.VERIFIED)

    p = client.get("/api/v1/levels/").data
    assert p["current"] == 1 and [r["total"] for r in p["levels"]] == [2, 4, 0, 0]
    assert [r["unlocked"] for r in p["levels"]][:2] == [True, False]
    assert client.post("/api/v1/levels/", {"level": 2}, format="json").status_code == 403

    # a "learn" session only offers level-1 words while the learner is at level 1
    s = client.post("/api/v1/sessions/", {"kind": "learn", "size": 10}, format="json").data
    assert {i["card"]["slug"] for i in s["items"]} == {"cat", "dog"}

    # studying both level-1 words opens level 2 and moves the learner up when the session ends
    for item in s["items"]:
        client.post(f"/api/v1/sessions/{s['id']}/answer/", {"personal_word": item["personal_word"],
                    "question_type": "type_target", "correct": True, "graded": True}, format="json")
    assert client.post(f"/api/v1/sessions/{s['id']}/finish/").data["level_up"] == 2
    assert client.get("/api/v1/levels/").data["current"] == 2

    # skip test of level 2: all answers right → level 3 opens
    test = client.get("/api/v1/levels/2/test/").data
    from django.core import signing
    answers = signing.loads(test["token"], salt="learning.level-test")["a"]
    res = client.post("/api/v1/levels/2/test/", {"token": test["token"], "answers": answers}, format="json").data
    assert res["passed"] and res["unlocked"] == 3 and res["progress"]["levels"][2]["unlocked"]
    wrong = client.post("/api/v1/levels/2/test/", {"token": test["token"], "answers": ["x"] * len(answers)},
                        format="json").data
    assert not wrong["passed"] and wrong["score"] == 0
