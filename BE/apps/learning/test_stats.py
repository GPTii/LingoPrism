from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.learning.models import PersonalWord, ReviewLog
from apps.vocab.models import Language, ReviewStatus, Topic, TopicWord, Word, WordTranslation


@pytest.fixture
def learner(db):
    for code in ("vi", "en", "zh-Hans", "zh-Hant"):
        Language.objects.create(code=code, name=code, native_name=code, tts_locale=code)
    topic = Topic.objects.create(slug="animals", name_vi="Động vật", icon="🐾")
    user = User.objects.create_user("s@example.com", "Strong!Pass123", active_language="en")
    pws = []
    for i, (vi, en) in enumerate([("mèo", "cat"), ("chó", "dog"), ("gà", "chicken")]):
        w = Word.objects.create(slug=en)
        TopicWord.objects.create(topic=topic, word=w, order=i)
        WordTranslation.objects.create(word=w, language_id="vi", text=vi, status=ReviewStatus.VERIFIED)
        WordTranslation.objects.create(word=w, language_id="en", text=en, status=ReviewStatus.VERIFIED)
        pws.append(PersonalWord.objects.create(user=user, word=w, language="en", topic=topic,
                                               status="mastered" if i == 0 else "learning"))
    client = APIClient()
    client.force_authenticate(user)
    return user, client, pws


def log(user, pw, correct, qtype="choose_target", days_ago=0, first_try=True):
    ReviewLog.objects.create(user=user, personal_word=pw, language="en", question_type=qtype, correct=correct,
                             first_try=first_try, scheduler="sm2", created_at=timezone.now() - timedelta(days=days_ago))


def test_stats_counts_words_accuracy_and_days(learner):
    user, client, (cat, dog, chicken) = learner
    log(user, cat, True)
    log(user, cat, True, days_ago=2)
    log(user, dog, False)
    log(user, dog, False, qtype="type_target", first_try=False)
    log(user, dog, True, days_ago=40)  # outside the 30-day window

    d = client.get("/api/v1/stats/learning/").data
    assert d["words"] == {"total": 3, "new": 0, "learning": 2, "mastered": 1}
    assert d["answers"] == 4 and d["accuracy"] == 0.5
    assert d["first_try_accuracy"] == round(2 / 3, 4)
    assert len(d["daily"]) == 30 and d["active_days"] == 2
    assert d["daily"][-1]["answers"] == 3
    assert {r["type"] for r in d["by_question_type"]} == {"choose_target", "type_target"}
    assert d["by_topic"][0]["name"] == "Động vật" and d["by_topic"][0]["mastered"] == 1
    # the word missed twice comes first, with its card in the learner's language
    assert d["hardest"][0]["card"]["target"]["text"] == "dog" and d["hardest"][0]["wrong"] == 2


def test_stats_window_and_privacy(learner):
    user, client, (cat, *_ ) = learner
    log(user, cat, True, days_ago=40)
    assert client.get("/api/v1/stats/learning/?days=90").data["answers"] == 1
    assert len(client.get("/api/v1/stats/learning/?days=3").data["daily"]) == 7  # at least a week

    other = User.objects.create_user("o@example.com", "Strong!Pass123", active_language="en")
    c2 = APIClient()
    c2.force_authenticate(other)
    assert c2.get("/api/v1/stats/learning/").data["answers"] == 0
    assert APIClient().get("/api/v1/stats/learning/").status_code == 401
