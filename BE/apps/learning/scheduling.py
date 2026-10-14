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

    def as_dict(self):
        return asdict(self)


class Scheduler:
    name = "base"

    def review(self, state: CardState, correct: bool, rating: int, now: datetime) -> tuple[CardState, datetime]:
        raise NotImplementedError


class LeitnerScheduler(Scheduler):
    """SnapLingua's original scheduler: first-try correct → next box, wrong → back to box 0."""

    name = "leitner"
    INTERVALS = [1, 3, 7, 14, 30, 60, 120]

    def review(self, state, correct, rating, now):
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


SCHEDULERS = {cls.name: cls for cls in (LeitnerScheduler,)}
DEFAULT_SCHEDULER = "leitner"


def get_scheduler(name: str | None = None) -> Scheduler:
    return SCHEDULERS.get(name or DEFAULT_SCHEDULER, LeitnerScheduler)()
