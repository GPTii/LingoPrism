"""Genetic Algorithm (Holland / Goldberg) that tunes the parameters of the review mechanism on the pooled history.

As in the thesis outline, the GA does *not* schedule single words for single learners: it searches one parameter
set (here the 17 FSRS weights) that predicts recall best on the review history of all learners, to be used as the
reference configuration.

    chromosome  17 real genes inside BOUNDS (fsrs.py)
    fitness     − log-loss of the replayed predictions on the training cards (evaluation.py)
    selection   tournament of size 3          crossover  BLX-α (α = 0.3), rate 0.9
    mutation    Gaussian, σ = 10 % of the gene range, rate 0.15 per gene      elitism  2 best kept
The result is evaluated on held-out cards (never used during the search) against the default FSRS weights.
"""
import random
import time

from . import fsrs
from .evaluation import metrics, predict_fsrs


def fitness(w, hist) -> float:
    m = metrics([x for h in hist for x in predict_fsrs(h, w)])
    return -m.get("log_loss", 9)


def clip(w):
    return [min(hi, max(lo, x)) for x, (lo, hi) in zip(w, fsrs.BOUNDS)]


def run(train, population=30, generations=30, seed=0, log=print) -> dict:
    rng = random.Random(seed)
    span = [hi - lo for lo, hi in fsrs.BOUNDS]
    # initial population: the default weights + random individuals around and across the search space
    pop = [list(fsrs.DEFAULT_W)]
    while len(pop) < population:
        if rng.random() < 0.5:
            pop.append(clip([x + rng.gauss(0, 0.15 * s) for x, s in zip(fsrs.DEFAULT_W, span)]))
        else:
            pop.append([rng.uniform(lo, hi) for lo, hi in fsrs.BOUNDS])
    scores = [fitness(w, train) for w in pop]
    history = []
    t0 = time.time()
    for gen in range(generations):
        order = sorted(range(len(pop)), key=lambda i: -scores[i])
        history.append({"generation": gen, "best": round(-scores[order[0]], 5),
                        "mean": round(-sum(scores) / len(scores), 5)})
        elite = [pop[i] for i in order[:2]]
        children = [list(e) for e in elite]

        def tournament():
            best = max(rng.sample(range(len(pop)), 3), key=lambda i: scores[i])
            return pop[best]

        while len(children) < population:
            a, b = tournament(), tournament()
            if rng.random() < 0.9:  # BLX-α crossover
                child = []
                for x, y in zip(a, b):
                    lo, hi = min(x, y), max(x, y)
                    d = (hi - lo) * 0.3
                    child.append(rng.uniform(lo - d, hi + d))
            else:
                child = list(a)
            child = [x + rng.gauss(0, 0.1 * s) if rng.random() < 0.15 else x for x, s in zip(child, span)]
            children.append(clip(child))
        pop = children
        scores = [fitness(w, train) for w in pop]
        if gen % 5 == 0:
            log(f"  thế hệ {gen}: log-loss tốt nhất {history[-1]['best']:.4f} ({time.time() - t0:.0f}s)")
    best = max(range(len(pop)), key=lambda i: scores[i])
    history.append({"generation": generations, "best": round(-scores[best], 5), "mean": round(-sum(scores) / len(scores), 5)})
    return {"weights": [round(x, 4) for x in pop[best]], "history": history,
            "population": population, "generations": generations}
