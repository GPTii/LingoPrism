"""Golden tests for the self-implemented algorithms (values computed by hand from the published formulas)."""
import math
import random
from datetime import datetime

import numpy as np
import pytest

from apps.learning.scheduling import CardState

from . import evaluation, fsrs, ga, proximity, simulate, sm2, word2vec

NOW = datetime(2026, 1, 1)


def test_sm2_sequence_matches_the_original_description():
    # q = 4 three times: I = 1, 6, round(6 · EF) with EF unchanged by q = 4 (0.1 − 1·(0.08 + 0.02) = 0)
    ef, n, i = 2.5, 0, 0
    seq = []
    for _ in range(3):
        ef, n, i = sm2.sm2_step(ef, n, i, 4)
        seq.append(i)
    assert seq == [1, 6, 15] and ef == pytest.approx(2.5)
    # a lapse (q = 1) restarts the item and lowers EF by 0.54, never below 1.3
    ef2, n2, i2 = sm2.sm2_step(2.5, 3, 15, 1)
    assert (n2, i2) == (0, 1) and ef2 == pytest.approx(1.96)
    assert sm2.sm2_step(1.3, 0, 0, 0)[0] == pytest.approx(1.3)
    s, due = sm2.SM2Scheduler().review(CardState(), True, 4, NOW)
    assert s.interval_days == 1 and (due - NOW).days == 1


def test_fsrs_equations():
    w = fsrs.DEFAULT_W
    assert fsrs.retrievability(10, 10) == pytest.approx(0.9)  # by construction R(S, S) = 90 %
    assert fsrs.retrievability(0, 5) == pytest.approx(1.0)
    assert fsrs.interval(10) == 10  # desired retention 0.9 → interval = S
    assert fsrs.interval(10, 0.8) > 10
    d, s, _ = fsrs.step(w, 0, 0, 0, 3)  # first review graded Good
    assert s == w[2] and d == pytest.approx(w[4])
    d1, s_ok, r = fsrs.step(w, d, s, s, 3)  # reviewed exactly when R = 0.9
    assert r == pytest.approx(0.9) and s_ok > s
    _, s_lapse, _ = fsrs.step(w, d, s, s, 1)
    assert s_lapse < s and fsrs.step(w, d, s, s, 1)[0] > d  # forgetting raises difficulty
    state, due = fsrs.FSRSScheduler().review(CardState(), True, 4, NOW)
    assert state.stability == w[2] and (due - NOW).days == round(w[2])


def test_grid_index_equals_brute_force():
    rng = random.Random(1)
    pts = [(i, 21 + rng.uniform(-0.2, 0.2), 105.8 + rng.uniform(-0.2, 0.2)) for i in range(3000)]
    idx = proximity.GridIndex(pts)
    for _ in range(200):
        lat, lng, r = 21 + rng.uniform(-0.25, 0.25), 105.8 + rng.uniform(-0.25, 0.25), rng.choice([300, 1500, 8000])
        assert [p for p, _ in idx.query(lat, lng, r)] == [p for p, _ in proximity.brute_force(pts, lat, lng, r)]
    # Hanoi Opera House → Turtle Tower (Hoan Kiem Lake): about 700 m
    assert proximity.haversine(21.0245, 105.8576, 21.0287, 105.8523) == pytest.approx(707, abs=15)


@pytest.mark.django_db
def test_poi_index_follows_a_change_made_in_another_server_process():
    from django.core.cache import cache

    from apps.gis.models import Poi

    Poi.objects.create(name="Chợ Bến Thành", category="market", lat=10.7725, lng=106.6980, radius_m=150)
    assert len(proximity.poi_index().query(10.7725, 106.6980, 500)) == 1
    # another process adds a POI: its signal ran there, here only the shared version changes
    Poi.objects.bulk_create([Poi(name="Dinh Độc Lập", category="landmark", lat=10.7770, lng=106.6953, radius_m=200)])
    assert len(proximity.poi_index().query(10.7725, 106.6980, 1000)) == 1  # still this process's index
    cache.set(proximity.VERSION_KEY, "set by another process", timeout=None)
    assert len(proximity.poi_index().query(10.7725, 106.6980, 1000)) == 2


def test_evaluation_metrics():
    m = evaluation.metrics([(0.9, True), (0.8, True), (0.2, False), (0.1, False)])
    assert m["auc"] == 1.0 and m["log_loss"] < 0.25
    assert evaluation.metrics([(0.5, True), (0.5, False)])["auc"] == 0.5


def test_ga_beats_default_weights_on_simulated_history():
    rng = random.Random(3)
    hist = []
    for _ in range(150):  # learners who forget faster than FSRS assumes
        mem = simulate.TrueMemory(1.0, 1.6)
        mem.first()
        h, t = [(0.0, True, 4)], 0.0
        for gap in (1, 3, 7, 14):
            ok = mem.review(gap, rng)
            h.append((float(gap), ok, 4 if ok else 1))
        hist.append(h)
    base = ga.fitness(fsrs.DEFAULT_W, hist)
    out = ga.run(hist, population=12, generations=6, log=lambda *_: None)
    assert ga.fitness(out["weights"], hist) > base
    assert all(lo <= x <= hi for x, (lo, hi) in zip(out["weights"], fsrs.BOUNDS))
    assert out["history"][-1]["best"] <= out["history"][0]["best"]


def test_vip_puts_confusable_and_forgotten_words_first():
    from .vip import DEFAULT_WEIGHTS, score

    safe = {"forget": 0.1, "difficulty": 0.1, "confidence": 0.0, "confusion": 0.0}
    confusable = {"forget": 0.1, "difficulty": 0.1, "confidence": 0.6, "confusion": 0.9}
    forgotten = {"forget": 0.9, "difficulty": 0.5, "confidence": 0.0, "confusion": 0.0}
    assert score(confusable) > score(safe) and score(forgotten) > score(safe)
    assert sum(DEFAULT_WEIGHTS.values()) == pytest.approx(1)


def test_word2vec_learns_co_occurrence():
    rng = random.Random(0)
    animals, food = ["cat", "dog", "horse"], ["rice", "bread", "soup"]
    sents = [[rng.choice(animals), "runs", "in", "the", "field"] for _ in range(1500)] + \
            [[rng.choice(food), "is", "on", "the", "table"] for _ in range(1500)]
    index, vecs = word2vec.train(sents, dim=16, window=2, min_count=1, epochs=4, batch=256, log=lambda *_: None)
    unit = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
    sim = lambda a, b: float(unit[index[a]] @ unit[index[b]])
    assert sim("cat", "dog") > sim("cat", "bread")
    v = word2vec.phrase_vector("the cat", index, vecs)
    assert v is not None and math.isclose(float(np.linalg.norm(v)), 1, rel_tol=1e-5)


@pytest.mark.django_db
def test_smart_distractor_never_offers_a_second_right_answer(monkeypatch):
    from apps.vocab.models import Language, ReviewStatus, Word, WordTranslation

    from . import distractor

    for code in ("vi", "en"):
        Language.objects.create(code=code, name=code, native_name=code, tts_locale=code)
    rows = [("cat", "con mèo"), ("dog", "con chó"), ("kitten", "con mèo"), ("horse", "con ngựa"), ("car", "xe ô tô")]
    for slug, vi in rows:
        w = Word.objects.create(slug=slug)
        WordTranslation.objects.create(word=w, language_id="vi", text=vi, status=ReviewStatus.VERIFIED)
        WordTranslation.objects.create(word=w, language_id="en", text=slug, status=ReviewStatus.VERIFIED)
    vec = {"cat": [1, 0, 0], "dog": [0.8, 0.6, 0], "kitten": [0.99, 0.14, 0], "horse": [0.7, 0, 0.71], "car": [0, 0, 1]}
    vec = {k: np.array(v, dtype=np.float32) / np.linalg.norm(v) for k, v in vec.items()}
    monkeypatch.setattr(distractor, "vectors", lambda: vec)
    picks = [w.slug for w, _ in distractor.rank_candidates(Word.objects.get(slug="cat"), "en", 3)]
    assert "kitten" not in picks  # same Vietnamese meaning / near-synonym → would also be correct
    assert picks[0] == "dog" and set(picks) <= {"dog", "horse", "car"}


def test_accuracy_metric_uses_the_half_threshold():
    m = evaluation.metrics([(0.9, True), (0.6, False), (0.4, False), (0.2, True)])
    assert m["accuracy"] == 0.5


def test_hybrid_vip_keeps_due_order_but_moves_confusable_words_earlier(monkeypatch):
    from datetime import timedelta
    from types import SimpleNamespace

    from . import vip

    now = datetime(2026, 1, 10)
    word = lambda label: SimpleNamespace(yolo_label=label)
    pw = lambda days_overdue, label: SimpleNamespace(due_at=now - timedelta(days=days_overdue), last_reviewed_at=None,
                                                     fsrs_stability=0, interval_days=1, lapses=0, repetitions=1,
                                                     word=word(label))
    old, confusable, plain = pw(5, ""), pw(1.5, "spoon"), pw(2, "")
    profile = {"spoon": {"mean_conf": 0.2, "score": 1.0}}
    w = dict(vip.DEFAULT_WEIGHTS)
    monkeypatch.setattr(vip, "latest", lambda: profile)  # vision profile without the database
    order = lambda weights: [x for x, _, _ in vip.rank([old, confusable, plain], weights, now)]
    assert order(w)[0] is confusable  # pure VIP: the confusable word first, whatever its due date
    hybrid = order({**w, "due_days": 3})  # VIP 0.52 → 1.6 days earlier: before `plain` (0.6 day), still after `old`
    assert hybrid == [old, confusable, plain]
