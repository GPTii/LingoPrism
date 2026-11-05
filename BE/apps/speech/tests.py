import io
import wave

import numpy as np
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.vocab.models import Language, ReviewStatus, Word, WordTranslation

from . import assess as A
from . import phonology, recognizer, tones
from .align import NEAR, align, cost
from .models import PronunciationAttempt
from .phonology import Unit, base, numbered, split_tone


def _wav(seconds=1.0, hz=200.0, amp=0.3, rate=16000, glide=0.0) -> bytes:
    t = np.arange(int(seconds * rate)) / rate
    f = hz * 2 ** (glide * t / seconds / 12)  # glide: semitones over the whole sound
    a = (amp * np.sin(2 * np.pi * np.cumsum(f) / rate) * 32767).astype("<i2")
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(a.tobytes())
    return out.getvalue()


class FakeRecogniser:
    """Posteriors that spell `tokens` (3 frames each, blanks between) instead of running the 320 MB model."""

    def __init__(self, tokens):
        self.tokens = tokens
        vocab = ["<pad>"] + sorted(set(tokens) | {"s", "t", "θ", "ɪ", "ŋ", "k"})
        self.vocab = dict(enumerate(vocab))
        self.blank, self.ignore = 0, {0}

    def posteriors(self, audio):
        ids = {t: i for i, t in self.vocab.items()}
        rows = []
        for tok in self.tokens:
            rows += [ids[tok]] * 3 + [0]
        post = np.full((len(rows) + 4, len(self.vocab)), 0.01)
        for f, i in enumerate(rows):
            post[f, i] = 0.95
        post[len(rows):, 0] = 0.95
        return post / post.sum(axis=1, keepdims=True)

    decode = recognizer.Recogniser.decode


# --- pieces --------------------------------------------------------------------------------------------------------

def test_tone_marks_and_comparable_forms():
    assert split_tone("ɑ5") == ("ɑ", "5") and split_tone("aːɜ") == ("aː", "ɜ")
    assert split_tone("ɜː") == ("ɜː", "") and split_tone("ɜ") == ("ɜ", "")  # the English vowel, not a tone
    assert base("iː") == "i" and base("ɡ") == base("g") and base("ɝ") == base("ɜː")


def test_numbered_pinyin():
    assert numbered("nǚ") == ("nü", 3) and numbered("mā") == ("ma", 1) and numbered("ma") == ("ma", 5)
    assert numbered("ren2") == ("ren", 2) and numbered("lv4") == ("lü", 4)


def test_alignment_finds_the_wrong_sound():
    pairs = align(["θ", "ɪ", "ŋ", "k"], ["t", "ɪ", "ŋ", "k"])
    assert [(e, h) for e, h, _ in pairs] == [(0, 0), (1, 1), (2, 2), (3, 3)]
    assert pairs[0][2] > NEAR  # θ -> t: another place and manner, an error
    assert cost("θ", "s") <= NEAR  # θ -> s: same manner, next place – a near miss
    assert cost("θ", "s") < cost("θ", "m") < cost("θ", "a")
    missing = align(["k", "æ", "t", "s"], ["k", "æ", "t"])
    assert missing[-1][1] is None  # the final /s/ was not said


def test_pitch_tracker_and_tone_shapes():
    hz = tones.f0(A.read_wav(_wav(0.6, 220)))
    voiced = hz[hz > 0]
    assert len(voiced) > 20 and abs(np.median(voiced) - 220) < 5
    flat, rising, falling = np.zeros(30), np.linspace(-3, 3, 30), np.linspace(3, -3, 30)
    assert tones.classify_zh(flat, True) == 1 and tones.classify_zh(rising, True) == 2
    assert tones.classify_zh(falling, True) == 4
    assert tones.classify_vi(rising, True) == "sắc" and tones.classify_vi(flat, True) == "ngang"
    assert tones.judge_zh(3, 2, following=3) == "ok"  # tone sandhi
    assert tones.judge_vi("hỏi", "ngã") == "close"


def test_resampling_and_silence():
    a = A.read_wav(_wav(1.0, 200, rate=44100))
    assert abs(len(a) - 16000) < 10
    with pytest.raises(A.AudioProblem) as e:
        A.trim(A.read_wav(_wav(1.0, 200, amp=0.0)))
    assert e.value.code == "too_quiet"
    with pytest.raises(A.AudioProblem):
        A.read_wav(b"not a wav file")


@pytest.mark.skipif(not phonology.available(), reason="espeak-ng not installed")
def test_expected_phones_golden():
    """Golden pronunciations (espeak-ng, in the recogniser's symbols) – they must not drift silently."""
    assert phonology.expected_units("think", "en")[0].phones == ["θ", "ɪ", "ŋ", "k"]
    assert [u.phones for u in phonology.expected_units("ship sheep", "en")] == [["ʃ", "ɪ", "p"], ["ʃ", "iː", "p"]]
    zh = phonology.expected_units("女人", "zh-Hans", ["nǚ", "rén"])
    assert [u.text for u in zh] == ["女", "人"] and [u.tone for u in zh] == [3, 2]
    assert [base(p) for p in zh[0].phones] == ["n", "y"]
    vi = phonology.expected_units("bác sĩ", "vi")
    assert [u.tone for u in vi] == ["sắc", "ngã"]


# --- scoring with a stand-in recogniser ------------------------------------------------------------------------------

@pytest.fixture
def fake(monkeypatch):
    def use(heard, units):
        monkeypatch.setattr(recognizer, "get", lambda: FakeRecogniser(heard))
        monkeypatch.setattr(A, "expected_units", lambda text, language, pinyin=None: units)
    return use


def test_right_word_scores_high(fake):
    fake(["θ", "ɪ", "ŋ", "k"], [Unit("think", ["θ", "ɪ", "ŋ", "k"])])
    r = A.assess(_wav(), "think", "en")
    assert r["score"] >= 90 and r["verdict"] == "right" and r["errors"] == []


def test_th_said_as_t_gets_the_tip(fake):
    fake(["t", "ɪ", "ŋ", "k"], [Unit("think", ["θ", "ɪ", "ŋ", "k"])])
    r = A.assess(_wav(), "think", "en")
    assert r["verdict"] != "right"
    assert r["errors"][0]["code"] == "en.TH_T" and "giữa hai hàm răng" in r["errors"][0]["tip"]
    assert r["units"][0]["phones"][0] == {"expected": "θ", "heard": "t", "status": "wrong", "score": 0}


def test_dropped_final_sound(fake):
    fake(["k", "æ", "t"], [Unit("cats", ["k", "æ", "t", "s"])])
    r = A.assess(_wav(), "cats", "en")
    assert r["completeness"] == 75 and r["errors"][0]["code"] == "en.FINAL_DROPPED"


# --- API ------------------------------------------------------------------------------------------------------------

@pytest.fixture
def client(db, settings, monkeypatch, fake):
    for code in ("vi", "en", "zh-Hans", "zh-Hant"):
        Language.objects.create(code=code, name=code, native_name=code, tts_locale=code)
    w = Word.objects.create(slug="think")
    tr = WordTranslation.objects.create(word=w, language_id="en", text="think", ipa="θɪŋk", status=ReviewStatus.VERIFIED)
    draft = WordTranslation.objects.create(word=Word.objects.create(slug="x"), language_id="en", text="sink",
                                           status=ReviewStatus.DRAFT)
    monkeypatch.setattr(recognizer, "available", lambda: True)
    fake(["t", "ɪ", "ŋ", "k"], [Unit("think", ["θ", "ɪ", "ŋ", "k"])])
    user = User.objects.create_user("s@example.com", "Strong!Pass123", active_language="en")
    c = APIClient()
    c.force_authenticate(user)
    return c, user, tr, draft


def _post(c, **data):
    return c.post("/api/v1/speech/assess/", {"audio": io.BytesIO(_wav()), **data}, format="multipart")


def test_assess_scores_and_keeps_the_attempt(client):
    c, user, tr, _ = client
    res = _post(c, translation_id=tr.id)
    assert res.status_code == 200, res.data
    assert res.data["text"] == "think" and res.data["errors"][0]["code"] == "en.TH_T"
    a = PronunciationAttempt.objects.get(user=user)
    assert a.score == res.data["score"] and a.error_codes == ["en.TH_T"] and a.kind == "word"
    prog = c.get("/api/v1/speech/progress/?lang=en").data
    assert prog["attempts"] == 1 and prog["weak_sounds"][0]["code"] == "en.TH_T"


def test_assess_refuses_unverified_words_and_silence(client):
    c, _, tr, draft = client
    assert _post(c, translation_id=draft.id).status_code == 404
    res = c.post("/api/v1/speech/assess/", {"audio": io.BytesIO(_wav(amp=0.0)), "translation_id": tr.id},
                 format="multipart")
    assert res.status_code == 422 and res.data["code"] == "too_quiet"
    assert c.post("/api/v1/speech/assess/", {"translation_id": tr.id}, format="multipart").status_code == 400


def test_status_and_languages(client):
    c, *_ = client
    data = c.get("/api/v1/speech/status/").data
    assert data["enabled"] is True and "vi" not in data["languages"]
    vi = WordTranslation.objects.create(word=Word.objects.create(slug="me"), language_id="vi", text="mẹ",
                                        status=ReviewStatus.VERIFIED)
    res = _post(c, translation_id=vi.id)
    assert res.status_code == 400 and res.data["code"] == "language"
