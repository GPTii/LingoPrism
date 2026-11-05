"""Score one recording against a verified text: phones, tones, completeness (docs/thiet-ke-luyen-noi.md §4)."""
import io
import time
import wave

import numpy as np

from . import recognizer, tips
from .align import NEAR, align
from .phonology import base, expected_units, is_vowel, split_tone
from .tones import judge_vi, judge_zh, syllable_tones

SR = 16000
MAX_SECONDS = 12
RIGHT, CLOSE = 90, 60
# posterior of the expected sound that still counts it as said (ok) / nearly said (close); tuned on speechocean762
GOP_OK, GOP_CLOSE = 0.3, 0.1


class AudioProblem(Exception):
    """The recording cannot be scored (too short, silent, unreadable): ask the learner to try again."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


def read_wav(data: bytes) -> np.ndarray:
    """WAV (PCM 16/32-bit or 8-bit, any rate, mono or stereo) -> float32 mono 16 kHz."""
    try:
        with wave.open(io.BytesIO(data)) as w:
            ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
            raw = w.readframes(min(n, rate * (MAX_SECONDS + 2)))
    except (wave.Error, EOFError) as e:
        raise AudioProblem("bad_audio", "Không đọc được file ghi âm (cần WAV).") from e
    if width == 2:
        a = np.frombuffer(raw, "<i2").astype(np.float32) / 32768
    elif width == 4:
        a = np.frombuffer(raw, "<i4").astype(np.float32) / 2 ** 31
    elif width == 1:
        a = (np.frombuffer(raw, np.uint8).astype(np.float32) - 128) / 128
    else:
        raise AudioProblem("bad_audio", "Định dạng ghi âm không hỗ trợ.")
    if ch > 1:
        a = a[: len(a) // ch * ch].reshape(-1, ch).mean(axis=1)
    if rate != SR and len(a):
        t = np.arange(0, len(a) / rate, 1 / SR)
        a = np.interp(t, np.arange(len(a)) / rate, a).astype(np.float32)
    return a


def trim(a: np.ndarray) -> np.ndarray:
    """Cut the silence before and after the speech (keeping 0.2 s), refuse empty or too quiet recordings."""
    if len(a) < SR * 0.25:
        raise AudioProblem("too_short", "Ghi âm quá ngắn. Bấm mic rồi đọc cả từ nhé.")
    frame = SR // 50
    n = len(a) // frame
    energy = np.sqrt((a[: n * frame].reshape(n, frame) ** 2).mean(axis=1))
    loud = np.where(energy > max(0.008, 0.08 * energy.max()))[0]
    if energy.max() < 0.01 or len(loud) < 3:
        raise AudioProblem("too_quiet", "Chưa nghe thấy tiếng. Đọc to hơn hoặc đưa micro lại gần.")
    start, end = max(0, (loud[0] - 10) * frame), min(len(a), (loud[-1] + 11) * frame)
    return a[start:end][: SR * MAX_SECONDS]


def _ids_by_base(rec) -> dict[str, list[int]]:
    if not hasattr(rec, "_by_base"):
        groups: dict[str, list[int]] = {}
        for i, t in rec.vocab.items():
            if i not in rec.ignore:
                groups.setdefault(base(t), []).append(i)
        rec._by_base = groups
    return rec._by_base


def assess(audio_bytes: bytes, text: str, language: str, pinyin: list[str] | None = None) -> dict:
    t0 = time.perf_counter()
    audio = trim(read_wav(audio_bytes))
    units = expected_units(text, language, pinyin)
    exp = [(u, p) for u, unit in enumerate(units) for p in unit.phones]
    if not exp:
        raise AudioProblem("no_text", "Từ này chưa có cách đọc để chấm.")
    rec = recognizer.get()
    post = rec.posteriors(audio)
    heard = rec.decode(post)
    if not heard:
        raise AudioProblem("not_heard", "Máy chưa nghe rõ âm nào. Đọc chậm, rõ hơn rồi thử lại.")

    lk = tips.lang_key(language)
    pairs = align([p for _, p in exp], [h.token for h in heard], tips.EQUIVALENT.get(lk))
    by_base = _ids_by_base(rec)
    phones = [[] for _ in units]
    unit_frames: list[list[int]] = [[] for _ in units]
    vowel_frames: list[list[int]] = [[] for _ in units]  # where each syllable's vowel was heard (tones)
    extras, errors, gops = 0, [], []
    last_index = {u: i for i, (u, _) in enumerate(exp)}
    # frames around each expected sound: from the last heard sound before it to the next heard one after it
    frames_before, last = [], 0
    for ei, hi, _ in pairs:
        if hi is not None:
            last = heard[hi].end
        frames_before.append(last)
    frames_after, nxt = [], len(post) - 1
    for ei, hi, _ in reversed(pairs):
        if hi is not None:
            nxt = heard[hi].frame
        frames_after.append(nxt)
    frames_after.reverse()
    for k, (ei, hi, c) in enumerate(pairs):
        if ei is None:
            extras += 1
            continue
        u, e = exp[ei]
        h = heard[hi] if hi is not None else None
        if h is None:
            # not decoded: said only weakly (connected speech often swallows a final n / l / r)? look at the gap
            ids = by_base.get(base(e), [])
            a, b = frames_before[k], max(frames_before[k] + 1, frames_after[k] + 1)
            p = float(post[a:b][:, ids].sum(axis=1).max()) if ids and b > a else 0.0
            gops.append(p)
            if p >= GOP_OK:
                status, score = "ok", 70 + 30 * min(1.0, p / 0.6)
            elif p >= GOP_CLOSE:
                status, score = "close", 40.0
            else:
                status, score = "missing", 0.0
        else:
            # GOP-like: how much the recogniser believed in the EXPECTED sound where it heard this one
            ids = by_base.get(base(e), [])
            a, b = max(0, h.frame - 1), min(len(post), h.end + 2)
            p = float(post[a:b][:, ids].sum(axis=1).max()) if ids else (h.prob if c == 0 else 0.0)
            gops.append(p)
            if c == 0 or p >= GOP_OK:  # heard as expected, or a close second choice of the recogniser
                status, score = "ok", 70 + 30 * min(1.0, p / 0.6)
            elif c <= NEAR or p >= GOP_CLOSE:
                status, score = "close", 40.0
            else:
                status, score = "wrong", 0.0
        if h is not None:
            unit_frames[u] += [h.frame, h.end]
            if is_vowel(e):
                vowel_frames[u].append(h.frame)
        if status in ("missing", "wrong", "close"):
            code, tip = tips.phone_error(language, e, h.token if h else None, ei == last_index[u])
            errors.append({"code": code, "unit": u, "expected": base(e), "heard": base(h.token) if h else None,
                           "tip": tip, "severity": "minor" if status == "close" else "major"})
        phones[u].append({"expected": split_tone(e)[0], "heard": split_tone(h.token)[0] if h else None,
                          "status": status, "score": round(score), "heard_tone": split_tone(h.token)[1] if h else ""})

    # tones (the pitch curve of each syllable: the recogniser's own tone marks are not reliable)
    tone_results: list[dict | None] = [None] * len(units)
    if lk in ("zh", "vi"):
        starts = [min(f) if f else None for f in unit_frames]
        spans = []
        for u, f in enumerate(unit_frames):
            if not f:
                spans.append(None)
                continue
            nxt = next((s for s in starts[u + 1:] if s is not None), None)
            end = (nxt - 2) if nxt is not None else max(f) + 12
            start = min(vowel_frames[u]) - 1 if vowel_frames[u] else min(f)
            spans.append((start * recognizer.FRAME_S, max(end, start + 3) * recognizer.FRAME_S))
        got = syllable_tones(audio, spans, lk)
        for u, unit in enumerate(units):
            if got[u] is None:
                continue
            if lk == "zh" and unit.tone in (1, 2, 3, 4):
                following = units[u + 1].tone if u + 1 < len(units) else None
                status = judge_zh(unit.tone, got[u], following)
            elif lk == "vi" and unit.tone:
                status = judge_vi(unit.tone, got[u])
            else:
                continue
            tone_results[u] = {"expected": unit.tone, "heard": got[u], "status": status}
    for u, t in enumerate(tone_results):
        if t and t["status"] != "ok":
            code, tip = tips.tone_error(language, t["expected"], t["heard"])
            errors.append({"code": code, "unit": u, "expected": str(t["expected"]), "heard": str(t["heard"]), "tip": tip,
                           "severity": "minor" if t["status"] == "close" else "major"})

    # scores
    out_units = []
    for u, unit in enumerate(units):
        ps = [p["score"] for p in phones[u]]
        s = sum(ps) / len(ps) if ps else 0
        t = tone_results[u]
        if t:
            s = 0.75 * s + 25 * {"ok": 1, "close": 0.5, "wrong": 0}[t["status"]]
        s = round(s)
        out_units.append({"text": unit.text, "reading": unit.reading, "score": s,
                          "status": "right" if s >= RIGHT else "close" if s >= CLOSE else "wrong",
                          "tone": t, "phones": [{k: v for k, v in p.items() if k != "heard_tone"} for p in phones[u]]})
    all_phones = [p for ps in phones for p in ps]
    phone_score = sum(p["score"] for p in all_phones) / len(all_phones)
    completeness = 100 * sum(p["status"] in ("ok", "close") for p in all_phones) / len(all_phones)
    judged = [t for t in tone_results if t]
    tone_score = (100 * sum({"ok": 1, "close": 0.5, "wrong": 0}[t["status"]] for t in judged) / len(judged)) if judged else None
    total = (0.65 * phone_score + 0.15 * completeness + 0.2 * tone_score) if tone_score is not None \
        else (0.8 * phone_score + 0.2 * completeness)
    total *= 1 - min(0.2, 0.04 * extras)
    seen, unique_errors = set(), []
    for e in sorted(errors, key=lambda e: e["severity"] != "major"):
        key = (e["code"], e["expected"], e["heard"])
        if key not in seen:
            seen.add(key)
            unique_errors.append(e)
    score = round(total)
    return {
        "score": score, "verdict": "right" if score >= RIGHT else "close" if score >= CLOSE else "wrong",
        "phone_score": round(phone_score), "tone_score": round(tone_score) if tone_score is not None else None,
        "completeness": round(completeness), "extra_sounds": extras, "units": out_units,
        "gop": round(sum(gops) / len(gops), 3) if gops else 0.0,
        "heard_ipa": " ".join(split_tone(h.token)[0] for h in heard), "errors": unique_errors[:6],
        "duration_s": round(len(audio) / SR, 2), "ms": int((time.perf_counter() - t0) * 1000),
    }
