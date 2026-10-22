from datetime import timedelta
from types import SimpleNamespace

from django.utils import timezone

from apps.vocab.services import recall_now


def pw(days_ago, stability):
    return SimpleNamespace(last_reviewed_at=timezone.now() - timedelta(days=days_ago), fsrs_stability=stability)


def test_recall_is_none_before_the_first_review():
    assert recall_now(SimpleNamespace(last_reviewed_at=None, fsrs_stability=3)) is None
    assert recall_now(pw(1, 0)) is None


def test_recall_follows_fsrs_forgetting_curve():
    assert recall_now(pw(0, 5)) == 1.0
    assert recall_now(pw(5, 5)) == 0.9  # by definition R(S, S) = 90 %
    assert recall_now(pw(30, 5)) < recall_now(pw(10, 5)) < 0.9
