"""Offline evaluation of schedulers on the review history (ReviewLog), the usual spaced-repetition benchmark:
replay every card's reviews in order, let the model predict the recall probability *before* each answer,
and score the predictions against what really happened.

    log-loss = −mean[y·ln p + (1 − y)·ln(1 − p)]      (lower is better)
    RMSE     = √mean[(p − y)²]
    AUC      = P(p_correct > p_wrong) for a random correct / wrong pair (0.5 = no better than chance)
    accuracy = share of answers predicted right with the threshold p ≥ 0.5 (easy to read, but a model that always
               says "remembered" already scores the recall rate – hence log-loss / AUC as the main measures)
"""
import math
import random
from collections import defaultdict

from apps.learning.models import ReviewLog

from . import fsrs
from .sm2 import quality, recall_probability, sm2_step

LEITNER = [1, 3, 7, 14, 30, 60, 120]
EPS = 1e-6


def histories(language: str | None = None) -> list[list[tuple[float, bool, int]]]:
    """One list per card: [(elapsed days since the previous review, correct, rating)], first answer per session."""
    qs = ReviewLog.objects.filter(first_try=True).order_by("personal_word_id", "created_at")
    if language:
        qs = qs.filter(language=language)
    seen, cards = set(), defaultdict(list)
    for pw, sess, created, correct, rating in qs.values_list("personal_word_id", "session_id", "created_at", "correct", "rating"):
        if (pw, sess) in seen:
            continue
        seen.add((pw, sess))
        cards[pw].append((created, correct, rating))
    out = []
    for revs in cards.values():
        h, prev = [], None
        for created, correct, rating in revs:
            h.append(((created - prev).total_seconds() / 86400 if prev else 0.0, correct, rating))
            prev = created
        if len(h) >= 2:
            out.append(h)
    return out


def predict_sm2(h):
    ef, n, interval, out = 2.5, 0, 0, []
    for i, (t, correct, rating) in enumerate(h):
        if i:
            out.append((recall_probability(t, interval), correct))
        ef, n, interval = sm2_step(ef, n, interval, quality(correct, rating))
    return out


def predict_leitner(h):
    stage, out = 0, []
    for i, (t, correct, _) in enumerate(h):
        if i:
            out.append((recall_probability(t, LEITNER[stage]), correct))
        stage = min(stage + 1, len(LEITNER) - 1) if correct else 0
    return out


def predict_fsrs(h, w=None):
    w = w or fsrs.DEFAULT_W
    d = s = 0.0
    out = []
    for i, (t, correct, rating) in enumerate(h):
        g = fsrs.grade(correct, rating)
        d, s, r = fsrs.step(w, d, s, t, g)
        if i:
            out.append((r, correct))
    return out


def metrics(pairs) -> dict:
    if not pairs:
        return {"n": 0}
    ll = -sum(math.log(min(1 - EPS, max(EPS, p))) if y else math.log(min(1 - EPS, max(EPS, 1 - p))) for p, y in pairs) / len(pairs)
    rmse = math.sqrt(sum((p - y) ** 2 for p, y in pairs) / len(pairs))
    pos = [p for p, y in pairs if y]
    neg = [p for p, y in pairs if not y]
    auc = None
    if pos and neg:  # rank-based AUC (Mann–Whitney U)
        ranked = sorted([(p, 1) for p in pos] + [(p, 0) for p in neg])
        rank_sum, i = 0.0, 0
        while i < len(ranked):
            j = i
            while j < len(ranked) and ranked[j][0] == ranked[i][0]:
                j += 1
            avg = (i + j + 1) / 2
            rank_sum += avg * sum(1 for k in range(i, j) if ranked[k][1])
            i = j
        auc = (rank_sum - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))
    acc = sum((p >= 0.5) == bool(y) for p, y in pairs) / len(pairs)
    return {"n": len(pairs), "log_loss": round(ll, 4), "rmse": round(rmse, 4), "accuracy": round(acc, 4),
            "auc": round(auc, 4) if auc is not None else None, "recall_rate": round(len(pos) / len(pairs), 4)}


def compare(hist, fsrs_weights=None) -> dict:
    out = {
        "leitner": metrics([x for h in hist for x in predict_leitner(h)]),
        "sm2": metrics([x for h in hist for x in predict_sm2(h)]),
        "fsrs": metrics([x for h in hist for x in predict_fsrs(h)]),
    }
    if fsrs_weights:
        out["fsrs_ga"] = metrics([x for h in hist for x in predict_fsrs(h, fsrs_weights)])
    return out


def split(hist, test_share=0.2, seed=0):
    rng = random.Random(seed)
    items = list(hist)
    rng.shuffle(items)
    k = int(len(items) * test_share)
    return items[k:], items[:k]
