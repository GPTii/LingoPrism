"""Review schedulers behind one interface so Phase 5 can plug in SM-2 / FSRS / SM-2+VIP
without touching the API (PLAN.md §4)."""
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta


@dataclass
class CardState:
    stage: int = 0
    ease: float = 2.5
    interval_days: int = 0
    repetitions: int = 0
    lapses: int = 0
    wrong_streak: int = 0
    difficulty: float = 0.0  # FSRS D (1–10); 0 = not used by this scheduler
    stability: float = 0.0  # FSRS S in days

    def as_dict(self):
        return asdict(self)


class Scheduler:
    name = "base"

    def review(self, state: CardState, correct: bool, rating: int, now: datetime,
               elapsed_days: float | None = None) -> tuple[CardState, datetime]:
        raise NotImplementedError


class LeitnerScheduler(Scheduler):
    """SnapLingua's original scheduler: first-try correct → next box, wrong → back to box 0."""

    name = "leitner"
    INTERVALS = [1, 3, 7, 14, 30, 60, 120]

    def review(self, state, correct, rating, now, elapsed_days=None):
        s = CardState(**state.as_dict())
        s.repetitions += 1
        if correct:
            s.stage = min(s.stage + 1, len(self.INTERVALS) - 1)
            s.wrong_streak = 0
        else:
            s.stage = 0
            s.wrong_streak += 1
            s.lapses += 1
        s.interval_days = self.INTERVALS[s.stage]
        return s, now + timedelta(days=s.interval_days)


def get_scheduler(name: str | None = None) -> Scheduler:
    """The scheduler a session uses: the one stored on the session, else the one chosen on the admin page
    (apps.algorithms: SM-2 / FSRS, self-implemented), with the GA-fitted FSRS weights when there are some."""
    from apps.algorithms.fsrs import FSRSScheduler
    from apps.algorithms.models import AlgorithmConfig
    from apps.algorithms.sm2 import SM2Scheduler

    cfg = AlgorithmConfig.get()
    name = name or cfg.scheduler
    if name == "fsrs":
        return FSRSScheduler(cfg.fsrs_weights, cfg.desired_retention)
    if name == "sm2":
        return SM2Scheduler()
    return LeitnerScheduler()
