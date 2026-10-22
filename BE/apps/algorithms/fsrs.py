"""FSRS-4.5 (Free Spaced Repetition Scheduler, Ye et al.) implemented from its published equations – no library.

Memory model DSR:
    R(t, S) = (1 + F · t / S)^C            retrievability after t days; F = 19/81, C = −0.5  (R(S, S) = 0.9)
    S₀(G)   = w[G−1]                       initial stability for the first grade G ∈ {1 Again, 2 Hard, 3 Good, 4 Easy}
    D₀(G)   = w4 − (G − 3) · w5            initial difficulty, clamped to [1, 10]
    D'      = w7 · D₀(3) + (1 − w7) · (D − w6 · (G − 3))           (mean reversion)
    S'ᵣ     = S · (1 + e^w8 · (11 − D) · S^−w9 · (e^(w10·(1−R)) − 1) · hard(w15) · easy(w16))   after a success
    S'f     = w11 · D^−w12 · ((S + 1)^w13 − 1) · e^(w14·(1−R))     after a lapse
    I(r)    = S / F · (r^(1/C) − 1)        next interval for a desired retention r (I = S when r = 0.9)

The 17 weights default to the FSRS-4.5 values; the Genetic Algorithm (ga.py) can fit them to our review history.
"""
import math
from datetime import datetime, timedelta

from apps.learning.scheduling import CardState, Scheduler

DEFAULT_W = [0.4872, 1.4003, 3.7145, 13.8206, 5.1618, 1.2298, 0.8975, 0.031, 1.6474, 0.1367, 1.0461,
             2.1072, 0.0793, 0.3246, 1.587, 0.2272, 2.8755]
# search bounds used by the GA (same order as the weights)
BOUNDS = [(0.1, 5), (0.1, 10), (0.5, 20), (1, 60), (1, 10), (0.1, 4), (0.1, 4), (0, 0.5), (0, 3), (0, 0.8),
          (0.01, 4), (0.1, 5), (0.01, 0.5), (0.01, 0.9), (0.01, 4), (0, 1), (1, 6)]
F, C = 19 / 81, -0.5


def grade(correct: bool, rating: int) -> int:
    """Our answers → FSRS grade: wrong = Again (1), right after a retry = Hard (2), right at once = Good (3)."""
    if not correct:
        return 1
    return 3 if rating >= 4 else 2


def retrievability(t: float, s: float) -> float:
    return (1 + F * max(t, 0) / max(s, 0.01)) ** C


def init_difficulty(w, g):
    return min(10.0, max(1.0, w[4] - (g - 3) * w[5]))


def next_difficulty(w, d, g):
    d2 = d - w[6] * (g - 3)
    return min(10.0, max(1.0, w[7] * init_difficulty(w, 3) + (1 - w[7]) * d2))


def stability_after_recall(w, d, s, r, g):
    hard = w[15] if g == 2 else 1.0
    easy = w[16] if g == 4 else 1.0
    return s * (1 + math.exp(w[8]) * (11 - d) * s ** -w[9] * (math.exp(w[10] * (1 - r)) - 1) * hard * easy)


def stability_after_forget(w, d, s, r):
    return w[11] * d ** -w[12] * ((s + 1) ** w[13] - 1) * math.exp(w[14] * (1 - r))


def step(w, d: float, s: float, elapsed: float, g: int) -> tuple[float, float, float]:
    """One review → (difficulty, stability, retrievability predicted *before* the answer)."""
    if s <= 0:  # first review of the card
        return init_difficulty(w, g), w[g - 1], 0.0
    r = retrievability(elapsed, s)
    s = stability_after_recall(w, d, s, r, g) if g > 1 else stability_after_forget(w, d, s, r)
    return next_difficulty(w, d, g), max(0.01, min(s, 36500)), r


def interval(s: float, retention: float = 0.9) -> int:
    return max(1, min(36500, round(s / F * (retention ** (1 / C) - 1))))


class FSRSScheduler(Scheduler):
    name = "fsrs"

    def __init__(self, weights=None, retention: float = 0.9):
        self.w = list(weights) if weights and len(weights) == 17 else list(DEFAULT_W)
        self.retention = retention

    def review(self, state: CardState, correct: bool, rating: int, now: datetime, elapsed_days: float | None = None):
        s = CardState(**state.as_dict())
        g = grade(correct, rating)
        elapsed = elapsed_days if elapsed_days is not None else s.interval_days
        s.difficulty, s.stability, _ = step(self.w, s.difficulty, s.stability, elapsed, g)
        s.interval_days = interval(s.stability, self.retention)
        s.repetitions += 1
        if g == 1:
            s.lapses += 1
            s.wrong_streak += 1
            s.stage = 0
        else:
            s.wrong_streak = 0
            s.stage += 1
        return s, now + timedelta(days=s.interval_days)
