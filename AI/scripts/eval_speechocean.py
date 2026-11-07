"""Compare the pronunciation scorer (BE apps.speech) with human raters on speechocean762.

speechocean762 (Zhang et al., Interspeech 2021, CC BY 4.0): 5,000 English sentences read by 250 Mandarin speakers
(half of them children), each scored by 5 experts at sentence, word and phone level. The test split (2,500
sentences) is used; nothing of it was used to build the scorer.

    # test.json + wav/ extracted from the Hugging Face parquet (mispeech/speechocean762, split test)
    cd BE && .venv/Scripts/python ../AI/scripts/eval_speechocean.py D:/data/so762/test.json [--limit 300]

Measures:
  * Pearson correlation (PCC) of our sentence score with the experts' sentence accuracy (0-10) and total;
  * PCC of our word score with the experts' word accuracy (0-10);
  * mispronounced-word detection: a word the experts marked with a phone scored < 1 (of 2) vs a word where we found a
    wrong / missing sound – precision, recall, F1;
  * the same split by age (children <= 12 / older), and the scoring time.
Writes AI/report/speech/speechocean762.json and .md.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "BE"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
import django  # noqa: E402

django.setup()
from apps.speech.assess import AudioProblem, assess  # noqa: E402


def pcc(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(np.corrcoef(a, b)[0, 1]) if len(a) > 2 and a.std() and b.std() else float("nan")


def prf(pred, gold) -> dict:
    pred, gold = np.asarray(pred, bool), np.asarray(gold, bool)
    tp, fp, fn = int((pred & gold).sum()), int((pred & ~gold).sum()), int((~pred & gold).sum())
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {
        "precision": round(p, 3),
        "recall": round(r, 3),
        "f1": round(2 * p * r / (p + r), 3) if p + r else 0.0,
        "positives": int(gold.sum()),
        "words": len(gold),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("meta")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    meta_path = Path(args.meta)
    items = json.loads(meta_path.read_text(encoding="utf-8"))
    if args.limit:
        items = items[: args.limit]
    rows, words, skipped, ms = [], [], 0, []
    t0 = time.time()
    for k, it in enumerate(items):
        try:
            r = assess((meta_path.parent / it["file"]).read_bytes(), it["text"].lower(), "en")
        except AudioProblem:
            skipped += 1
            continue
        ms.append(r["ms"])
        child = it["age"] <= 12
        rows.append(
            {
                "ours": r["score"],
                "phone": r["phone_score"],
                "gop": r["gop"],
                "acc": it["accuracy"],
                "total": it["total"],
                "child": child,
            }
        )
        if len(r["units"]) == len(it["words"]):
            for u, w in zip(r["units"], it["words"]):
                words.append(
                    {
                        "ours": u["score"],
                        "acc": w["accuracy"],
                        "child": child,
                        "ours_bad": any(p["status"] in ("wrong", "missing") for p in u["phones"]),
                        "gold_bad": min(w["phones_accuracy"]) < 1.0,
                    }
                )
        if (k + 1) % 250 == 0:
            print(f"   {k + 1}/{len(items)} ({time.time() - t0:.0f}s)", flush=True)

    def block(rs, ws):
        return {
            "sentences": len(rs),
            "pcc_sentence_accuracy": round(pcc([x["ours"] for x in rs], [x["acc"] for x in rs]), 3),
            "pcc_sentence_total": round(pcc([x["ours"] for x in rs], [x["total"] for x in rs]), 3),
            "pcc_phone_score_accuracy": round(pcc([x["phone"] for x in rs], [x["acc"] for x in rs]), 3),
            "pcc_gop_accuracy": round(pcc([x["gop"] for x in rs], [x["acc"] for x in rs]), 3),
            "pcc_word_accuracy": round(pcc([x["ours"] for x in ws], [x["acc"] for x in ws]), 3),
            "mispronounced_words": prf([x["ours_bad"] for x in ws], [x["gold_bad"] for x in ws]),
        }

    out = {
        "dataset": "speechocean762 test",
        "skipped_unscorable": skipped,
        "all": block(rows, words),
        "children_le_12": block([x for x in rows if x["child"]], [x for x in words if x["child"]]),
        "older": block([x for x in rows if not x["child"]], [x for x in words if not x["child"]]),
        "ms_per_sentence": round(float(np.mean(ms)), 1) if ms else None,
    }
    rep = ROOT / "AI" / "report" / "speech"
    rep.mkdir(parents=True, exist_ok=True)
    (rep / "speechocean762.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Chấm phát âm so với giám khảo – speechocean762 (tập test)",
        "",
        f"{out['all']['sentences']} câu chấm được, {skipped} câu bỏ qua (máy không nghe được); "
        f"{out['ms_per_sentence']} ms / câu trên CPU (máy phát triển).",
        "",
        "| Nhóm | Số câu | PCC câu (accuracy) | PCC câu (total) | PCC từ (accuracy) | Phát hiện từ đọc sai P / R / F1 |",
        "|---|---|---|---|---|---|",
    ]
    for name, key in (("Tất cả", "all"), ("Trẻ em ≤ 12 tuổi", "children_le_12"), ("Trên 12 tuổi", "older")):
        b = out[key]
        m = b["mispronounced_words"]
        lines.append(
            f"| {name} | {b['sentences']} | {b['pcc_sentence_accuracy']} | {b['pcc_sentence_total']} | "
            f"{b['pcc_word_accuracy']} | {m['precision']} / {m['recall']} / {m['f1']} |"
        )
    (rep / "speechocean762.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
