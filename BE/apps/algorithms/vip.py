"""VIP – Visual Confusion-based Review Prioritization (the thesis' own algorithm).

Which due words should a learner review first when time is limited? The baseline takes them by due date.
VIP ranks them by a priority that adds, to the learning history, what the vision model tells us:

    VIP(u, w) = a · (1 − R(u, w))        forgetting risk now      (FSRS R, or 0.9^(t/I) for SM-2/Leitner)
              + b · Diff(u, w)          difficulty for this learner (FSRS D, else lapse rate)
              + c · (1 − Conf(w))       how unsure the detector is about the word's object class
              + d · Confusion(w)        how often the class is mistaken for another class (vision.py)

Words without a visual class get Conf = 1 and Confusion = 0, i.e. VIP falls back to history only.
Default weights a, b, c, d = 0.4, 0.25, 0.15, 0.2 (sum 1).

Two ways to use the score (benchmark.py tests both and picks one):
    pure VIP     due words sorted by VIP, highest first;
    hybrid       sorted by  due_at − due_days · VIP  (the weights carry "due_days"): the due date stays the main
                 order and VIP moves a word at most `due_days` days earlier – review on time first, confusable
                 words a little earlier.
"""
from datetime import timedelta

from django.utils import timezone

from .fsrs import retrievability
from .sm2 import recall_probability
from .vision import latest

DEFAULT_WEIGHTS = {"forget": 0.4, "difficulty": 0.25, "confidence": 0.15, "confusion": 0.2}


def components(pw, profile: dict, now=None) -> dict:
    now = now or timezone.now()
    elapsed = (now - pw.last_reviewed_at).total_seconds() / 86400 if pw.last_reviewed_at else 0
    if pw.fsrs_stability > 0:
        r = retrievability(elapsed, pw.fsrs_stability)
        diff = (pw.fsrs_difficulty - 1) / 9
    else:
        r = recall_probability(elapsed, pw.interval_days or 1) if pw.last_reviewed_at else 0.5
        diff = min(1.0, pw.lapses / max(pw.repetitions, 1))
    vis = profile.get(pw.word.yolo_label) if pw.word.yolo_label else None
    conf = vis["mean_conf"] if vis and vis.get("mean_conf") is not None else 1.0
    return {"forget": 1 - r, "difficulty": diff, "confidence": 1 - conf, "confusion": vis["score"] if vis else 0.0}


def score(comp: dict, weights: dict | None = None) -> float:
    w = weights or DEFAULT_WEIGHTS
    return sum(w[k] * comp[k] for k in DEFAULT_WEIGHTS)


def rank(personal_words, weights=None, now=None) -> list[tuple]:
    """[(pw, score, components)] sorted by VIP priority, highest first."""
    profile = latest()
    rows = [(pw, comp) for pw in personal_words for comp in [components(pw, profile, now)]]
    scored = [(pw, round(score(c, weights), 4), c) for pw, c in rows]
    k = (weights or {}).get("due_days")
    if k:
        return sorted(scored, key=lambda x: x[0].due_at - timedelta(days=k * x[1]))
    return sorted(scored, key=lambda x: -x[1])
