"""Weighted Box Fusion (Solovyev et al., 2021) vs the server's merge, on cached test-set predictions (no CLIP).

    python AI/scripts/eval_wbf.py oiv7m-int8 soup6a50=AI/runs/soup/ft6-a50-int8.onnx \
        oiv7l-int8=AI/runs/oiv7l/yolov8l-oiv7-lingoprism-int8.onnx

Each argument is a primary model eval_testset.py knows, or name=path of another ONNX; it is combined with
COCO yolov10m INT8 (predictions cached in AI/testset/predictions). Results: AI/report/yolo/ensemble_upgrade.md.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eval_testset as E  # noqa: E402

import apps.detection.inference as I  # noqa: E402
from apps.detection.inference import Box, EnsembleDetector, _iou, _merge  # noqa: E402

extra = [a.split("=", 1)[0] for a in sys.argv[1:]]
for a in sys.argv[1:]:
    if "=" in a:
        E.add_model(*a.split("=", 1))
data = E.load()
images, classes = data["images"], data["classes"]
raw, cls = {}, {}
for n in ["coco-m-int8"] + extra:
    raw[n], _, cls[n] = E._predict_all(n, images)
coco = set(cls["coco-m-int8"])
coco_scope = {c for c in classes if c in set(E._predict_all("coco", images)[2])}


def veto(b_new, b_base, known):
    unknown = [b for b in b_new if b.label not in coco and b.confidence >= I.SURE_UNKNOWN]
    return [b for b in b_base if b.label in known and not any(_iou(b.bbox, n.bbox) >= 0.5 for n in unknown)]


def wbf(b_new, b_base, known, thr=0.55, w_new=1.0, w_base=1.0, mode="avg"):
    b_base = veto(b_new, b_base, known)
    tagged = [(b, w_new, 0) for b in b_new] + [(b, w_base, 1) for b in b_base]
    out = []
    by_label = {}
    for t in tagged:
        by_label.setdefault(t[0].label, []).append(t)
    for lab, items in by_label.items():
        clusters = []  # [fused_bbox, [(box, w, src)]]
        for b, w, s in sorted(items, key=lambda t: -t[0].confidence * t[1]):
            best, bi = thr, None
            for i, c in enumerate(clusters):
                v = _iou(c[0], b.bbox)
                if v > best:
                    best, bi = v, i
            if bi is None:
                clusters.append([list(b.bbox), [(b, w, s)]])
            else:
                c = clusters[bi]
                c[1].append((b, w, s))
                tot = sum(x.confidence * ww for x, ww, _ in c[1])
                c[0] = [sum(x.confidence * ww * x.bbox[k] for x, ww, _ in c[1]) / tot for k in range(4)]
        for fused, members in clusters:
            # one vote per model: its most confident box in the cluster
            votes = {}
            for x, ww, s in members:
                if s not in votes or x.confidence > votes[s][0].confidence:
                    votes[s] = (x, ww)
            # a class only one model knows: that model alone decides
            n_models = 2 if lab in coco and lab in known else 1
            wsum = sum(ww for _, ww in votes.values())
            if mode == "avg":
                conf = sum(x.confidence * ww for x, ww in votes.values()) / max(wsum, 1e-9)
                conf *= min(len(votes), n_models) / n_models
            elif mode == "max":
                conf = max(x.confidence for x, _ in votes.values())
            else:  # "box": average for the box, max for the score
                conf = max(x.confidence for x, _ in votes.values())
            top = max(members, key=lambda m: m[0].confidence)[0]
            out.append(Box(lab, conf, fused, list(top.top_k), top.memory_id))
    return _merge(out)


def run(name, primary, fn):
    known = set(cls[primary])
    preds = [fn(a, b, known) for a, b in zip(raw[primary], raw["coco-m-int8"])]
    scope = known & set(classes)
    r = E.score(images, preds, classes, scope)
    c = E.score(images, preds, classes, scope & coco_scope)
    o = E.score(images, preds, classes, scope - coco_scope)
    print(
        f"{name:42} mAP50 {r['map50']:.4f} 50-95 {r['map50_95']:.4f} P {r['precision']:.3f} R {r['recall']:.3f}"
        f" | COCO {c['map50']:.4f} | khác {o['map50']:.4f}",
        flush=True,
    )


def server(a, b, known):
    e = EnsembleDetector.__new__(EnsembleDetector)
    e.classes, e._base_classes = list(known), coco
    return e.combine(a, b)


for p in extra:
    run(f"{p} server merge", p, server)
    for mode in ("avg", "max", "box"):
        run(f"{p} WBF {mode}", p, lambda a, b, k, m=mode: wbf(a, b, k, mode=m))
    for thr in (0.5, 0.65):
        run(f"{p} WBF avg thr{thr}", p, lambda a, b, k, t=thr: wbf(a, b, k, thr=t))
    for wn, wb in ((1, 2), (2, 1)):
        run(f"{p} WBF avg w{wn}:{wb}", p, lambda a, b, k, x=wn, y=wb: wbf(a, b, k, w_new=x, w_base=y))
