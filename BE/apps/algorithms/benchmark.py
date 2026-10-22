"""Benchmark: test every candidate algorithm / setting of each decision the system makes, pick the best by a stated
rule and (optionally) apply it to AlgorithmConfig.

    review schedule   Leitner · SM-2 · FSRS-4.5 · FSRS + GA weights, desired retention 0.80 / 0.85 / 0.90
    review priority   by due date · pure VIP with several weightings (incl. "forgetting risk only") ·
                      hybrid VIP (due date moved earlier by up to 1 / 3 / 7 days · VIP)
        → every combination simulated on 3 groups of learners (seeds 0–2, averaged); the chosen one, the baseline and
          the best plain one re-checked on a new, larger group (seed 10) never used for the choice
        rule: among the combinations whose overall recall is within `tolerance` of the best overall recall,
              take the one that keeps the visually confusable words best (VIP's purpose, thesis outline);
              so a VIP setting is only chosen if it does not cost overall learning.
    recall prediction Leitner / SM-2 / FSRS / FSRS + GA on held-out review history (log-loss, AUC, accuracy) – reported
    distractors       random same topic vs Smart: Smart if more similar and never more often a second right answer
    proximity         PostgreSQL earthdistance vs grid index: grid if it equals brute force and is faster
    YOLO              trained / COCO / combined top-1 on the word photos – reported (the detector is set in settings)
"""
import time

from . import evaluation, experiments, simulate
from .models import AlgorithmConfig, ExperimentRun

VIP_VARIANTS = {
    "vip": {"forget": 0.4, "difficulty": 0.25, "confidence": 0.15, "confusion": 0.2},  # thesis default
    "vip_history": {"forget": 0.6, "difficulty": 0.25, "confidence": 0.05, "confusion": 0.1},
    "vip_vision": {"forget": 0.3, "difficulty": 0.2, "confidence": 0.2, "confusion": 0.3},
    "risk_only": {"forget": 1.0, "difficulty": 0.0, "confidence": 0.0, "confusion": 0.0},
    "vip_due1": {"forget": 0.4, "difficulty": 0.25, "confidence": 0.15, "confusion": 0.2, "due_days": 1},
    "vip_due3": {"forget": 0.4, "difficulty": 0.25, "confidence": 0.15, "confusion": 0.2, "due_days": 3},
    "vip_due7": {"forget": 0.4, "difficulty": 0.25, "confidence": 0.15, "confusion": 0.2, "due_days": 7},
}
SEEDS = (0, 1, 2)
PRIORITY_LABEL = {"due": "theo hạn", "vip": "VIP", "vip_history": "VIP thiên lịch sử", "vip_vision": "VIP thiên thị giác",
                  "risk_only": "nguy cơ quên", "vip_due1": "VIP lai 1 ngày", "vip_due3": "VIP lai 3 ngày",
                  "vip_due7": "VIP lai 7 ngày"}
SCHEDULERS = [("leitner", None, 0.9), ("sm2", None, 0.9)] + \
             [(f"fsrs{tag}", None, r) for tag in ("", "_ga") for r in (0.8, 0.85, 0.9)]


def _ga_weights():
    run = ExperimentRun.objects.filter(kind="ga").first()
    return (run.results.get("weights") if run else None) or AlgorithmConfig.get().fsrs_weights or None


def schedule_search(learners=12, days=60, tolerance=0.02, log=print) -> dict:
    words = experiments._sim_words()
    w_ga = _ga_weights()
    rows = []
    for name, _, retention in SCHEDULERS:
        sched = "fsrs" if name.startswith("fsrs") else name
        weights = w_ga if name == "fsrs_ga" else None
        for prio, vw in [("due", None)] + list(VIP_VARIANTS.items()):
            runs = [simulate.run(words, sched, "due" if prio == "due" else "vip", weights=weights, vip_weights=vw,
                                 learners=learners, days=days, retention=retention, seed=seed) for seed in SEEDS]
            avg = lambda k: round(sum(r[k] for r in runs) / len(runs), 4)
            rows.append({"scheduler": name, "retention": retention if sched == "fsrs" else None, "priority": prio,
                         "recall_all": avg("recall_all"), "recall_confusable": avg("recall_confusable"),
                         "reviews": avg("reviews_per_learner")})
        log(f"  {name} r={retention}: xong")
    best_all = max(r["recall_all"] for r in rows)
    eligible = [r for r in rows if r["recall_all"] >= best_all - tolerance]
    chosen = max(eligible, key=lambda r: (r["recall_confusable"] or 0, r["recall_all"]))
    # Pareto front: no other row better on both measures
    for r in rows:
        r["pareto"] = not any(o["recall_all"] >= r["recall_all"] and (o["recall_confusable"] or 0) >= (r["recall_confusable"] or 0)
                              and o is not r and (o["recall_all"], o["recall_confusable"]) != (r["recall_all"], r["recall_confusable"])
                              for o in rows)
        r["eligible"] = r in eligible
    # re-check on other learners: chosen vs the thesis baseline (SM-2, by due date) and the best plain overall
    baseline = next(r for r in rows if r["scheduler"] == "sm2" and r["priority"] == "due")
    best_overall = max(rows, key=lambda r: r["recall_all"])

    def recheck(r):
        sched = "fsrs" if r["scheduler"].startswith("fsrs") else r["scheduler"]
        out = simulate.run(words, sched, "due" if r["priority"] == "due" else "vip",
                           weights=w_ga if r["scheduler"] == "fsrs_ga" else None, vip_weights=VIP_VARIANTS.get(r["priority"]),
                           learners=learners * 2, days=days, retention=r["retention"] or 0.9, seed=10)
        return {"label": label(r), "recall_all": out["recall_all"], "recall_confusable": out["recall_confusable"]}

    validation = [recheck(r) for r in {id(x): x for x in (baseline, best_overall, chosen)}.values()]
    return {"rows": rows, "chosen": chosen, "best_overall": best_overall, "baseline": baseline, "validation": validation,
            "tolerance": tolerance, "setup": {"learners": learners, "days": days, "words": len(words),
                                              "confusable_words": sum(1 for w in words if w["confusion"] >= 0.3)}}


def label(r) -> str:
    name = {"leitner": "Leitner", "sm2": "SM-2", "fsrs": "FSRS", "fsrs_ga": "FSRS+GA"}[r["scheduler"]]
    if r.get("retention") and r["scheduler"].startswith("fsrs"):
        name += f" r={r['retention']}"
    return name + ("" if r["priority"] == "due" else f" + {PRIORITY_LABEL[r['priority']]}")


def prediction() -> dict:
    hist = evaluation.histories()
    _, test = evaluation.split(hist)
    w_ga = _ga_weights()
    preds = {"leitner": evaluation.predict_leitner, "sm2": evaluation.predict_sm2, "fsrs": evaluation.predict_fsrs}
    out = {k: evaluation.metrics([x for h in test for x in f(h)]) for k, f in preds.items()}
    if w_ga:
        out["fsrs_ga"] = evaluation.metrics([x for h in test for x in evaluation.predict_fsrs(h, w_ga)])
    best = min(out, key=lambda k: out[k].get("log_loss", 9))
    return {"test_cards": len(test), "models": out, "best": best}


def run(apply=False, tolerance=0.02, learners=12, days=60, rerun=True, log=print) -> ExperimentRun:
    t0 = time.time()
    log("▶ Dự đoán nhớ / quên (tập test)")
    pred = prediction()
    log("▶ Lịch ôn × thứ tự ôn (mô phỏng)")
    sched = schedule_search(learners, days, tolerance, log)
    if rerun:
        log("▶ Smart Distractor / Proximity")
        experiments.distractor()
        experiments.proximity()
    latest = experiments.latest()
    dist = latest.get("distractor", {}).get("results", {}).get("stats", {})
    prox = latest.get("proximity", {}).get("results", {})
    yolo = latest.get("yolo", {}).get("results", {}).get("comparison", {})

    decisions = []
    c = sched["chosen"]
    decisions.append({"decision": "Lịch ôn", "options": "Leitner · SM-2 · FSRS · FSRS+GA × retention 0,8/0,85/0,9",
                      "chosen": label({**c, "priority": "due"}), "evidence": f"nhớ chung {c['recall_all']:.1%}, từ dễ nhầm {c['recall_confusable']:.1%} (mô phỏng)"})
    decisions.append({"decision": "Thứ tự ôn", "options": " · ".join(PRIORITY_LABEL.values()),
                      "chosen": PRIORITY_LABEL[c["priority"]], "evidence": f"trong ngưỡng −{tolerance:.0%} nhớ chung, giữ từ dễ nhầm tốt nhất"})
    smart_ok = bool(dist) and dist["smart"]["mean_similarity"] > dist["random"]["mean_similarity"] \
        and dist["smart"]["invalid_rate"] <= dist["random"]["invalid_rate"]
    if dist:
        decisions.append({"decision": "Đáp án nhiễu", "options": "ngẫu nhiên cùng chủ đề · Smart",
                          "chosen": "smart" if smart_ok else "random",
                          "evidence": f"độ gần nghĩa {dist['random']['mean_similarity']} → {dist['smart']['mean_similarity']}, "
                                      f"đáp án nhiễu cũng đúng {dist['smart']['invalid_rate']:.0%}"})
    grid_ok = bool(prox) and prox.get("grid_equals_brute", "").split("/")[0] == str(prox.get("queries")) \
        and (prox.get("postgres_ms") is None or prox["grid_ms"] < prox["postgres_ms"])
    if prox:
        decisions.append({"decision": "Tìm điểm gần", "options": "PostgreSQL earthdistance · lưới + Haversine",
                          "chosen": "grid" if grid_ok else "postgres",
                          "evidence": f"đúng {prox['grid_equals_brute']} so với brute force, {prox['grid_ms']} ms vs {prox.get('postgres_ms')} ms"})
    for m in yolo.get("models", []):
        res = {k: v for k, v in m["results"].items() if v.get("top1") is not None}
        if res:
            best = max(res, key=lambda k: res[k]["top1"] if k != "coco" else -1)  # coco alone misses the new classes
            decisions.append({"decision": f"Nhận diện ảnh ({m['model']})", "options": "model tự train · COCO · kết hợp",
                              "chosen": best, "evidence": ", ".join(f"{k} top-1 {v['top1']:.0%}" for k, v in res.items()),
                              "note": "đặt trong settings (YOLO_BASE_MODEL_PATH), không đổi tự động"})

    applied = {}
    if apply:
        cfg = AlgorithmConfig.get()
        cfg.scheduler = "fsrs" if c["scheduler"].startswith("fsrs") else c["scheduler"]
        if cfg.scheduler == "fsrs":
            cfg.desired_retention = c["retention"]
            cfg.fsrs_weights = _ga_weights() if c["scheduler"] == "fsrs_ga" else []
        cfg.review_priority = "due" if c["priority"] == "due" else "vip"
        if c["priority"] in VIP_VARIANTS:
            cfg.vip_weights = VIP_VARIANTS[c["priority"]]
        if dist:
            cfg.distractor = "smart" if smart_ok else "random"
        if prox:
            cfg.proximity = "grid" if grid_ok else "postgres"
        cfg.save()
        applied = {k: getattr(cfg, k) for k in ("scheduler", "desired_retention", "review_priority", "vip_weights",
                                                  "distractor", "proximity")}
    res = {"prediction": pred, "schedule": sched, "decisions": decisions, "applied": applied,
           "rule": f"Chọn tổ hợp giữ từ dễ nhầm tốt nhất trong số các tổ hợp có tỉ lệ nhớ chung không thấp hơn tổ hợp tốt nhất quá {tolerance:.0%}.",
           "note": "Lịch sử ôn và người học là mô phỏng (chưa có người dùng thật) – chạy lại khi có dữ liệu thật."}
    return ExperimentRun.objects.create(kind="benchmark", results=res, duration_s=round(time.time() - t0, 2))
