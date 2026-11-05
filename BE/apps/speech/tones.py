"""Mandarin tones from the pitch curve (F0, YIN – de Cheveigné & Kawahara 2002) of each syllable.

Each syllable's F0 is turned into semitones around the speaker's median and classified by its shape: flat (1),
rising (2), low / falling-rising (3), falling (4). Rule based and marked experimental in the app; a neutral-tone
syllable and one with too little voiced sound are not judged.
"""
import numpy as np

SR = 16000
HOP = 160  # 10 ms
WIN = 640  # 40 ms
FMIN, FMAX = 70.0, 450.0


def f0(audio: np.ndarray, threshold: float = 0.25, fallback: float = 0.45) -> np.ndarray:
    """F0 in Hz every 10 ms (0 = unvoiced)."""
    tau_min, tau_max = int(SR / FMAX), int(SR / FMIN)
    n = 1 + max(0, (len(audio) - WIN - tau_max) // HOP)
    if n <= 0:
        return np.zeros(0)
    idx = np.arange(WIN)[None, :] + (np.arange(n) * HOP)[:, None]
    frames = audio[idx]
    energy = np.sqrt((frames ** 2).mean(axis=1))
    d = np.zeros((n, tau_max + 1))
    for tau in range(1, tau_max + 1):
        shifted = audio[idx + tau]
        d[:, tau] = ((frames - shifted) ** 2).sum(axis=1)
    cum = np.cumsum(d[:, 1:], axis=1) / np.arange(1, tau_max + 1)[None, :]
    cmnd = np.ones_like(d)
    cmnd[:, 1:] = d[:, 1:] / np.maximum(cum, 1e-12)
    out = np.zeros(n)
    loud = energy > max(0.003, 0.05 * energy.max(initial=0))
    for k in range(n):
        if not loud[k]:
            continue
        c = cmnd[k, tau_min:]
        below = np.where(c < threshold)[0]
        if len(below):
            t = below[0]
        elif c.min() < fallback:  # no dip under the threshold: the deepest one, if clear enough (pYIN-like)
            t = int(np.argmin(c))
        else:
            continue
        while t + 1 < len(c) and c[t + 1] < c[t]:
            t += 1
        tau = t + tau_min
        if 1 <= t < len(c) - 1:  # parabolic interpolation
            a, b, cc = c[t - 1], c[t], c[t + 1]
            denom = a - 2 * b + cc
            tau = tau + (0.5 * (a - cc) / denom if denom else 0)
        out[k] = SR / tau
    return out


def _shape(st: np.ndarray):
    k = max(1, len(st) // 5)
    start, end = float(st[:k].mean()), float(st[-k:].mean())
    low_at = int(np.argmin(st)) / max(1, len(st) - 1)
    return start, end, float(st.mean()), float(st.min()), low_at


def classify_zh(st: np.ndarray, single: bool, broken: bool = False) -> int | None:
    """st: semitones of one syllable (voiced frames only, around the speaker median). single: the only syllable said
    (then its height says nothing, only its shape counts)."""
    if len(st) < 5:
        return None
    start, end, mean, lowest, low_at = _shape(st)
    if end - start >= 2.5 and (lowest > start - 1.5 or low_at < 0.4):
        return 2
    if lowest < min(start, end) - 1.5 and 0.15 < low_at < 0.85:
        return 3
    if start - end >= 3.0:
        return 4
    if end - start >= 2.5:
        return 3
    if not single and mean < -2.5:
        return 3
    return 1


def classify_vi(st: np.ndarray, single: bool, broken: bool = False, voiced_s: float = 0.0) -> str | None:
    """The six Vietnamese tones from the pitch shape: ngang flat, huyền low falling, sắc rising, hỏi dipping,
    ngã rising with a break (creaky voice: the tracker loses or halves the pitch), nặng short falling."""
    if len(st) < 4:
        return None
    start, end, mean, lowest, low_at = _shape(st)
    if end - start >= 2.5:
        if broken:
            return "ngã"
        if lowest < start - 1.5 and 0.2 < low_at < 0.8:
            return "hỏi"
        return "sắc"
    if lowest < min(start, end) - 2 and 0.2 < low_at < 0.8:
        return "hỏi"
    if start - end >= 1.5:
        return "nặng" if voiced_s < 0.18 or broken else "huyền"
    if not single and mean < -2.5:
        return "huyền"
    return "ngang"


def syllable_tones(audio: np.ndarray, spans: list[tuple[float, float] | None], language: str = "zh") -> list:
    """spans: (start s, end s) of each syllable, None when it was not heard. -> tone per syllable (None = not judged)."""
    hz = f0(audio)
    voiced = hz[hz > 0]
    if len(voiced) < 5:
        return [None] * len(spans)
    ref = np.median(voiced)
    st_all = np.where(hz > 0, 12 * np.log2(np.maximum(hz, 1) / ref), np.nan)
    said = [s for s in spans if s]
    out = []
    for span in spans:
        if not span:
            out.append(None)
            continue
        a, b = int(span[0] * 100), int(span[1] * 100) + 1
        seg = st_all[a:b]
        seg = seg[~np.isnan(seg)]
        broken = False
        if len(seg) >= 3:  # octave jumps (creaky voice or tracker errors): dropped, but remembered for ngã / nặng
            keep = np.abs(seg - np.median(seg)) < 7
            broken = bool((~keep).any())
            seg = seg[keep]
        if len(seg) >= 8:  # the edges belong to the neighbouring consonants / syllables (coarticulation)
            seg = seg[len(seg) // 10: len(seg) - len(seg) // 5]
        if language == "vi":
            out.append(classify_vi(seg, len(said) == 1, broken, len(seg) / 100))
        else:
            out.append(classify_zh(seg, len(said) == 1, broken))
    return out


def judge_zh(expected: int, heard: int, following: int | None) -> str:
    """ok / close / wrong. Tone sandhi: a 3rd tone before another 3rd is said as a 2nd. A 3rd tone is often said
    low-falling without the final rise (half third tone, usual in Taiwan Mandarin): heard as a 4th it is "close"."""
    if heard == expected or (expected == 3 and following == 3 and heard == 2):
        return "ok"
    if expected == 3 and heard == 4:
        return "close"
    return "wrong"


VI_CLOSE = {frozenset({"hỏi", "ngã"}), frozenset({"sắc", "ngã"}), frozenset({"nặng", "huyền"}),
            frozenset({"ngang", "huyền"})}


def judge_vi(expected: str, heard: str) -> str:
    if heard == expected:
        return "ok"
    return "close" if frozenset({expected, heard}) in VI_CLOSE else "wrong"
