"""Experiments of the thesis outline (§ "So sánh – đối chiếu"), each stored as an ExperimentRun for the admin page:

  srs         SM-2 vs FSRS (and the old Leitner) predicting recall on the review history
  ga          Genetic Algorithm tuning the FSRS weights (train cards) → compared on held-out cards
  vip         SM-2 / FSRS with and without VIP on simulated learners (overall + confusable words)
  distractor  random same-topic baseline vs Smart Distractor on every word
  proximity   self-implemented grid index vs brute force vs PostgreSQL earthdistance (correctness + speed)
"""
import random
import statistics
import time

from django.db import connection

from apps.vocab.models import ReviewStatus, Word, WordTranslation
from apps.vocab.services import Target

from . import evaluation, ga, simulate, vision
from .vip import DEFAULT_WEIGHTS
from .models import AlgorithmConfig, ExperimentRun


def _save(kind, results, t0):
    return ExperimentRun.objects.create(kind=kind, results=results, duration_s=round(time.time() - t0, 2))


def srs():
    t0 = time.time()
    hist = evaluation.histories()
    cfg = AlgorithmConfig.get()
    res = {"cards": len(hist), "reviews": sum(len(h) for h in hist), "models": evaluation.compare(hist, cfg.fsrs_weights or None),
           "note": "Dữ liệu ôn tập hiện là của người học mẫu (seed_demo_activity) – kết quả cần chạy lại khi có người dùng thật."}
    return _save("srs", res, t0)


def run_ga(population=24, generations=25, apply=True, log=print):
    t0 = time.time()
    hist = evaluation.histories()
    train, test = evaluation.split(hist)
    out = ga.run(train, population, generations, log=log)
    res = {**out, "train_cards": len(train), "test_cards": len(test),
           "test": {"fsrs_default": evaluation.metrics([x for h in test for x in evaluation.predict_fsrs(h)]),
                    "fsrs_ga": evaluation.metrics([x for h in test for x in evaluation.predict_fsrs(h, out["weights"])]),
                    "sm2": evaluation.metrics([x for h in test for x in evaluation.predict_sm2(h)])}}
    improved = res["test"]["fsrs_ga"].get("log_loss", 9) < res["test"]["fsrs_default"].get("log_loss", 9)
    res["applied"] = bool(apply and improved)
    if res["applied"]:  # only a parameter set that is better on unseen cards becomes the reference configuration
        cfg = AlgorithmConfig.get()
        cfg.fsrs_weights = out["weights"]
        cfg.save(update_fields=["fsrs_weights", "updated_at"])
    return _save("ga", res, t0)


def _sim_words():
    profile = vision.latest()
    words = []
    for w in Word.objects.filter(translations__language_id="en", translations__status=ReviewStatus.VERIFIED).distinct():
        vis = profile.get(w.yolo_label) if w.yolo_label else None
        words.append({"slug": w.slug, "level": (w.levels or {}).get("en", 2),
                      "confusion": vis["score"] if vis else 0.0,
                      "conf": vis["mean_conf"] if vis and vis.get("mean_conf") is not None else 1.0})
    return words


def vip(learners=12, days=60):
    t0 = time.time()
    words = _sim_words()
    cfg = AlgorithmConfig.get()
    pure = {k: v for k, v in (cfg.vip_weights or DEFAULT_WEIGHTS).items() if k != "due_days"}
    hybrid = {**pure, "due_days": (cfg.vip_weights or {}).get("due_days") or 3}
    rows = []
    for sched in ("sm2", "fsrs"):
        for prio, vw in (("due", None), ("vip", pure), ("vip_hybrid", hybrid)):  # pure VIP order / hybrid (benchmark.py)
            r = simulate.run(words, sched, "due" if prio == "due" else "vip", weights=cfg.fsrs_weights or None,
                             vip_weights=vw, learners=learners, days=days, retention=cfg.desired_retention)
            rows.append({**r, "priority": prio})
    rows.append(simulate.run(words, "leitner", "due", learners=learners, days=days))
    res = {"rows": rows, "words": len(words), "confusable_words": sum(1 for w in words if w["confusion"] >= 0.3),
           "setup": {"learners": learners, "days": days, "new_per_day": 8, "review_budget": 25,
                     "hybrid_due_days": hybrid["due_days"]},
           "note": "Mô phỏng: trí nhớ thật theo mô hình quên hàm mũ + hiệu ứng giãn cách, từ dễ nhầm thị giác khó nhớ hơn."}
    return _save("vip", res, t0)


def distractor(sample=250, seed=0):
    from apps.learning.questions import RandomSameTopicDistractors

    from .distractor import SmartDistractors, vectors

    t0 = time.time()
    vec = vectors()
    if not vec:
        return _save("distractor", {"error": "Chưa có vector – chạy python manage.py train_word2vec"}, t0)
    rng = random.Random(seed)
    words = list(Word.objects.filter(slug__in=list(vec)).prefetch_related("topics"))
    words = rng.sample(words, min(sample, len(words)))
    vi = dict(WordTranslation.objects.filter(language_id="vi").values_list("word_id", "text"))
    target = Target("en", "en", "")
    stats, examples = {}, []
    for name, provider in (("random", RandomSameTopicDistractors()), ("smart", SmartDistractors())):
        cos, same_pos, invalid, total = [], 0, 0, 0
        for w in words:
            picks = provider.pick(w, target, 3)
            for p in picks:
                total += 1
                if p.slug in vec:
                    cos.append(float(vec[w.slug] @ vec[p.slug]))
                same_pos += p.part_of_speech == w.part_of_speech
                invalid += vi.get(p.id) == vi.get(w.id)  # would also be a right answer
        stats[name] = {"distractors": total, "mean_similarity": round(statistics.mean(cos), 4) if cos else None,
                       "same_pos_rate": round(same_pos / max(total, 1), 4), "invalid_rate": round(invalid / max(total, 1), 4)}
    vi_word = {w.id: vi.get(w.id, w.slug) for w in Word.objects.all()}
    for w in words[:12]:
        examples.append({"word": vi_word.get(w.id), "en": w.slug,
                         "random": [vi_word.get(p.id) for p in RandomSameTopicDistractors().pick(w, target, 3)],
                         "smart": [vi_word.get(p.id) for p in SmartDistractors().pick(w, target, 3)]})
    return _save("distractor", {"words": len(words), "stats": stats, "examples": examples}, t0)


def proximity(queries=500, seed=0):
    from apps.gis.models import Poi
    from apps.gis.services import nearby

    from .proximity import GridIndex, brute_force

    t0 = time.time()
    rng = random.Random(seed)
    pois = list(Poi.objects.filter(is_active=True).values_list("id", "lat", "lng"))
    res = {"pois": len(pois)}
    if not pois:
        return _save("proximity", {"error": "Chưa có POI"}, t0)
    lats, lngs = [p[1] for p in pois], [p[2] for p in pois]
    box = (min(lats) - 0.05, max(lats) + 0.05, min(lngs) - 0.05, max(lngs) + 0.05)
    qs = [(rng.uniform(box[0], box[1]), rng.uniform(box[2], box[3]), rng.choice([500, 1000, 3000, 10000])) for _ in range(queries)]
    index = GridIndex(pois)

    def timed(fn):
        s = time.perf_counter()
        out = [fn(lat, lng, r) for lat, lng, r in qs]
        return out, (time.perf_counter() - s) / len(qs) * 1000

    grid, t_grid = timed(lambda a, b, r: index.query(a, b, r))
    brute, t_brute = timed(lambda a, b, r: brute_force(pois, a, b, r))
    pg, t_pg = timed(lambda a, b, r: nearby(a, b, r, limit=1000, using="postgres")) if connection.vendor == "postgresql" else ([], None)
    same_ids = sum(1 for g, b in zip(grid, brute) if [x[0] for x in g] == [x[0] for x in b])
    max_diff_pg = max((abs(d1 - d2) for g, p in zip(grid, pg) for (i1, d1), (i2, d2) in zip(g, p) if i1 == i2), default=0)
    res.update(queries=queries, grid_ms=round(t_grid, 4), brute_ms=round(t_brute, 4), postgres_ms=round(t_pg, 4) if t_pg else None,
               grid_equals_brute=f"{same_ids}/{queries}", grid_vs_postgres_ids=f"{sum(1 for g, p in zip(grid, pg) if [x[0] for x in g] == [x[0] for x in p])}/{len(pg)}",
               max_distance_diff_m=round(max_diff_pg, 3),
               note="earthdistance dùng bán kính Trái Đất 6 378 168 m, Haversine ở đây dùng bán kính trung bình 6 371 009 m "
                    "→ lệch ~0,1 % khoảng cách; khác biệt chỉ xảy ra với POI nằm sát mép bán kính.")
    # scaling: synthetic POIs around Ha Noi, same queries
    scale = []
    for n in (1_000, 10_000, 50_000):
        pts = [(i, 21.0 + rng.uniform(-0.3, 0.3), 105.8 + rng.uniform(-0.3, 0.3)) for i in range(n)]
        idx = GridIndex(pts)
        q2 = [(21.0 + rng.uniform(-0.3, 0.3), 105.8 + rng.uniform(-0.3, 0.3), 1000) for _ in range(100)]
        s = time.perf_counter()
        for a, b, r in q2:
            idx.query(a, b, r)
        tg = (time.perf_counter() - s) / len(q2) * 1000
        s = time.perf_counter()
        for a, b, r in q2[:20]:
            brute_force(pts, a, b, r)
        tb = (time.perf_counter() - s) / 20 * 1000
        scale.append({"pois": n, "grid_ms": round(tg, 3), "brute_ms": round(tb, 3), "speedup": round(tb / tg, 1) if tg else None})
    res["scaling"] = scale
    return _save("proximity", res, t0)


def latest() -> dict:
    out = {}
    for kind in ("benchmark", "yolo", "vision", "word2vec", "srs", "ga", "vip", "distractor", "proximity"):
        run = ExperimentRun.objects.filter(kind=kind).first()
        if run:
            out[kind] = {"created_at": run.created_at, "duration_s": run.duration_s, "results": run.results}
    return out
