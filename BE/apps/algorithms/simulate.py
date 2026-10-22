"""Simulated learners – a controlled experiment for the schedulers and VIP when real long-term data is not yet there.

Ground-truth memory (deliberately *not* the FSRS model, so no scheduler is favoured by construction):
    p_recall(t) = exp(−t / S)                                  exponential forgetting, S in days
    word difficulty  δ = 0.7 + 0.25·(level − 1) + 1.2·confusion(visual class)     (interference of look-alikes)
    first exposure   S₀ = 6 · a / δ                            a = learner ability ~ U(0.8, 1.2)
    after a success  S ← S · (2.5 + 3·(1 − p)) · √a / δ^0.3      (spacing effect: harder recall, bigger gain)
    after a lapse    S ← max(0.5, 0.4 · S)
The constants give ≈ 80–90 % recall on a Leitner schedule, close to what learners report in spaced-repetition apps.
Each simulated day a learner meets `new_per_day` new words and has a review budget; the policy decides
*which* due cards get reviewed (by due date, or by VIP). Outcome: the true recall probability of every word
at the end, overall and for the most visually confusable words.
"""
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from apps.learning.scheduling import CardState, LeitnerScheduler

from .fsrs import FSRSScheduler, retrievability
from .sm2 import SM2Scheduler, recall_probability
from .vip import DEFAULT_WEIGHTS, score

T0 = datetime(2026, 1, 1)


def word_difficulty(level: int, confusion: float) -> float:
    return 0.7 + 0.25 * (max(1, min(level, 4)) - 1) + 1.2 * confusion


@dataclass
class TrueMemory:
    ability: float
    difficulty: float
    s: float = 0.0

    def first(self):
        self.s = 6.0 * self.ability / self.difficulty

    def p(self, t: float) -> float:
        return math.exp(-max(t, 0) / max(self.s, 0.05))

    def review(self, t: float, rng: random.Random) -> bool:
        p = self.p(t)
        ok = rng.random() < p
        if ok:
            self.s = min(3650, self.s * (2.5 + 3 * (1 - p)) * math.sqrt(self.ability) / self.difficulty ** 0.3)
        else:
            self.s = max(0.5, 0.4 * self.s)
        return ok


@dataclass
class Card:
    word: dict
    mem: TrueMemory
    state: CardState = field(default_factory=CardState)
    due: float = 0.0
    last: float = 0.0


def make_scheduler(name, weights=None, retention=0.9):
    return {"leitner": LeitnerScheduler, "sm2": SM2Scheduler}.get(name, lambda: FSRSScheduler(weights, retention))()


def vip_components(card: Card, now: float) -> dict:
    s, t = card.state, now - card.last
    if s.stability > 0:
        r, diff = retrievability(t, s.stability), (s.difficulty - 1) / 9
    else:
        r, diff = recall_probability(t, s.interval_days or 1), min(1.0, s.lapses / max(s.repetitions, 1))
    return {"forget": 1 - r, "difficulty": diff, "confidence": 1 - card.word["conf"], "confusion": card.word["confusion"]}


def run(words: list[dict], scheduler="sm2", priority="due", weights=None, vip_weights=None, learners=12,
        days=60, new_per_day=8, budget=25, seed=0, retention=0.9) -> dict:
    """words: [{"slug", "level", "confusion", "conf"}]; returns mean final true recall, overall and for confusable words."""
    rng = random.Random(seed)
    sched = make_scheduler(scheduler, weights, retention)
    finals, finals_conf, reviews = [], [], 0
    for _ in range(learners):
        ability = rng.uniform(0.8, 1.2)
        order = list(words)
        rng.shuffle(order)
        cards: list[Card] = []
        for day in range(days):
            for w in order[day * new_per_day:(day + 1) * new_per_day]:  # learn new words
                c = Card(w, TrueMemory(ability, word_difficulty(w["level"], w["confusion"])))
                c.mem.first()
                c.state, due = sched.review(CardState(), True, 4, T0 + timedelta(days=day), elapsed_days=0)
                c.due, c.last = day + (due - (T0 + timedelta(days=day))).days, day
                cards.append(c)
            due_cards = [c for c in cards if c.due <= day]
            vw = vip_weights or DEFAULT_WEIGHTS
            if priority == "vip" and vw.get("due_days"):  # hybrid: due date moved earlier by up to due_days · VIP
                due_cards.sort(key=lambda c: c.due - vw["due_days"] * score(vip_components(c, day), vw))
            elif priority == "vip":
                due_cards.sort(key=lambda c: -score(vip_components(c, day), vw))
            else:
                due_cards.sort(key=lambda c: c.due)
            for c in due_cards[:budget]:
                t = day - c.last
                ok = c.mem.review(t, rng)
                now = T0 + timedelta(days=day)
                c.state, due = sched.review(c.state, ok, 4 if ok else 1, now, elapsed_days=t)
                c.due, c.last = day + max(1, (due - now).days), day
                reviews += 1
        for c in cards:
            p = c.mem.p(days - c.last)
            finals.append(p)
            if c.word["confusion"] >= 0.3:
                finals_conf.append(p)
    mean = lambda xs: round(sum(xs) / len(xs), 4) if xs else None
    return {"scheduler": scheduler, "priority": priority, "recall_all": mean(finals),
            "recall_confusable": mean(finals_conf), "n_confusable": len(finals_conf) // max(learners, 1),
            "reviews_per_learner": round(reviews / learners, 1)}
