"""SM-2 (Wozniak, 1990) – the baseline spaced-repetition scheduler, implemented from the original description.

    quality q ∈ 0..5   (here: correct at the first try → 4, correct after a retry → 3, wrong → 1)
    q ≥ 3:  n = 0 → I = 1 ;  n = 1 → I = 6 ;  n ≥ 2 → I = round(I · EF) ;  n += 1
    q < 3:  n = 0, I = 1   (the item is relearned)
    EF' = EF + (0.1 − (5 − q) · (0.08 + (5 − q) · 0.02)),  EF ≥ 1.3

SM-2 has no forgetting curve; for log-loss comparisons the recall probability is taken as R(t) = 0.9^(t / I)
(the item is scheduled when R reaches 90 %), the usual convention in spaced-repetition benchmarks.
"""
from datetime import datetime, timedelta

from apps.learning.scheduling import CardState, Scheduler

MIN_EF = 1.3


def quality(correct: bool, rating: int) -> int:
    if not correct:
        return 1
    return 4 if rating >= 4 else 3


def sm2_step(ef: float, n: int, interval: int, q: int) -> tuple[float, int, int]:
    """One SM-2 update → (EF, repetitions, interval days)."""
    if q >= 3:
        if n == 0:
            interval = 1
        elif n == 1:
            interval = 6
        else:
            interval = max(1, round(interval * ef))
        n += 1
    else:
        n, interval = 0, 1
    ef = max(MIN_EF, ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))
    return ef, n, interval


def recall_probability(elapsed_days: float, interval_days: float) -> float:
    return 0.9 ** (max(elapsed_days, 0) / max(interval_days, 1))


class SM2Scheduler(Scheduler):
    name = "sm2"

    def review(self, state: CardState, correct: bool, rating: int, now: datetime, elapsed_days=None):
        s = CardState(**state.as_dict())
        q = quality(correct, rating)
        s.ease, n, s.interval_days = sm2_step(s.ease or 2.5, s.stage, s.interval_days, q)
        s.stage = n  # consecutive successful reviews
        s.repetitions += 1
        if q < 3:
            s.lapses += 1
            s.wrong_streak += 1
        else:
            s.wrong_streak = 0
        return s, now + timedelta(days=s.interval_days)
