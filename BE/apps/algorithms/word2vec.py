"""Word2Vec skip-gram with negative sampling (Mikolov et al., 2013), implemented with NumPy – no gensim.

Trained on English sentences of Tatoeba; each vocabulary *concept* gets the vector of its English text
(mean of the token vectors), so the same semantic space serves the English, Chinese and Vietnamese courses.

    for every (centre c, context o) pair inside a window, and k negatives n ~ U(w)^0.75:
        L = −log σ(u_o · v_c) − Σ log σ(−u_n · v_c)
    vectors are updated by mini-batch SGD with a linearly decaying learning rate;
    frequent words are sub-sampled with p_keep = (√(f/t) + 1) · t / f.
"""
import re
import time
from collections import Counter

import numpy as np

TOKEN = re.compile(r"[a-z]+(?:'[a-z]+)?")
STOP = {"a", "an", "the", "to", "of", "and", "or", "in", "on", "for", "with", "at", "by", "is", "be"}


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def train(sentences, dim=64, window=4, negative=5, min_count=5, max_vocab=30000, epochs=3, batch=4096,
          lr0=0.025, sample=1e-3, seed=0, log=print) -> tuple[dict, np.ndarray]:
    rng = np.random.default_rng(seed)
    counts = Counter(t for s in sentences for t in s)
    vocab = [w for w, c in counts.most_common(max_vocab) if c >= min_count]
    index = {w: i for i, w in enumerate(vocab)}
    freq = np.array([counts[w] for w in vocab], dtype=np.float64)
    total = freq.sum()
    keep = np.minimum(1.0, (np.sqrt(freq / total / sample) + 1) * sample * total / freq)
    noise = freq ** 0.75
    noise /= noise.sum()
    # the whole corpus as one flat array of word ids + the sentence each token belongs to (low memory)
    ids, sid = [], []
    for n, s in enumerate(sentences):
        row = [index[t] for t in s if t in index]
        if len(row) > 1:
            ids.extend(row)
            sid.extend([n] * len(row))
    ids, sid = np.array(ids, dtype=np.int32), np.array(sid, dtype=np.int32)
    table = np.repeat(np.arange(len(vocab), dtype=np.int32), np.maximum(1, (noise * 2_000_000).astype(np.int64)))

    w_in = (rng.random((len(vocab), dim), dtype=np.float32) - 0.5) / dim
    w_out = np.zeros((len(vocab), dim), dtype=np.float32)

    def chunk_pairs(tok, sen):
        """All (centre, context) pairs of a token chunk, vectorised; dynamic window b ∈ [1, window] per centre."""
        b = rng.integers(1, window + 1, size=len(tok))
        cs, os_ = [], []
        for d in range(1, window + 1):
            same = sen[:-d] == sen[d:]
            fwd = same & (b[:-d] >= d)  # centre i, context i+d
            bwd = same & (b[d:] >= d)  # centre i+d, context i
            cs += [tok[:-d][fwd], tok[d:][bwd]]
            os_ += [tok[d:][fwd], tok[:-d][bwd]]
        c, o = np.concatenate(cs), np.concatenate(os_)
        order = rng.permutation(len(c))
        return c[order], o[order]

    t0 = time.time()
    chunk = 1_000_000
    est_total = epochs * max(1, len(ids) * window // batch)  # rough step count for the learning-rate decay
    step = 0
    for epoch in range(epochs):
        kept = rng.random(len(ids)) < keep[ids]  # sub-sampling of frequent words, new draw each epoch
        tok_all, sen_all = ids[kept], sid[kept]
        loss_sum, steps, n_pairs = 0.0, 0, 0
        for start in range(0, len(tok_all), chunk):
            c_all, o_all = chunk_pairs(tok_all[start:start + chunk], sen_all[start:start + chunk])
            n_pairs += len(c_all)
            for k in range(0, len(c_all), batch):
                lr = lr0 * max(1e-4, 1 - step / est_total)
                c, o = c_all[k:k + batch], o_all[k:k + batch]
                neg = table[rng.integers(0, len(table), size=(len(c), negative))]
                targets = np.concatenate([o[:, None], neg], axis=1)  # (B, 1+k)
                labels = np.zeros(targets.shape, dtype=np.float32)
                labels[:, 0] = 1
                v = w_in[c]  # (B, d)
                u = w_out[targets]  # (B, 1+k, d)
                score = np.einsum("bd,bkd->bk", v, u)
                sig = 1 / (1 + np.exp(-np.clip(score, -10, 10)))
                g = (labels - sig) * lr  # gradient of the log-likelihood
                loss_sum += float(-np.log(sig[:, 0] + 1e-7).mean() - np.log(1 - sig[:, 1:] + 1e-7).sum(1).mean())
                np.add.at(w_in, c, np.einsum("bk,bkd->bd", g, u))
                np.add.at(w_out, targets.ravel(), (g[..., None] * v[:, None, :]).reshape(-1, v.shape[1]))
                steps += 1
                step += 1
        log(f"  epoch {epoch + 1}/{epochs}: {n_pairs:,} cặp, loss {loss_sum / max(steps, 1):.3f}, {time.time() - t0:.0f}s")
    return index, w_in


def phrase_vector(text: str, index: dict, vectors: np.ndarray) -> np.ndarray | None:
    ids = [index[t] for t in tokenize(text) if t in index and t not in STOP] or \
          [index[t] for t in tokenize(text) if t in index]
    if not ids:
        return None
    v = vectors[ids].mean(0)
    n = np.linalg.norm(v)
    return v / n if n else None
