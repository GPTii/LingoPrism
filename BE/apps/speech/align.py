"""Align the expected phones with the heard ones (Needleman–Wunsch), with a substitution cost from articulatory
features: /θ/ heard as /s/ or /t/ is a near miss, as /a/ it is not."""
from .phonology import VOWEL_CHARS, base

# consonant -> (place, manner, voiced). Places 0 lips … 8 glottis; manners: stop, fric, affr, nasal, approx, lateral, tap
_P = {"bilabial": 0, "labiodental": 1, "dental": 2, "alveolar": 3, "postalveolar": 4, "retroflex": 5, "palatal": 6,
      "velar": 7, "uvular": 7.5, "glottal": 8}
CONS = {
    "p": ("bilabial", "stop", 0), "b": ("bilabial", "stop", 1), "ph": ("bilabial", "stop", 0), "pʰ": ("bilabial", "stop", 0),
    "m": ("bilabial", "nasal", 1), "ɓ": ("bilabial", "stop", 1), "w": ("bilabial", "approx", 1), "β": ("bilabial", "fric", 1),
    "f": ("labiodental", "fric", 0), "v": ("labiodental", "fric", 1), "ʋ": ("labiodental", "approx", 1),
    "θ": ("dental", "fric", 0), "ð": ("dental", "fric", 1), "t̪": ("dental", "stop", 0),
    "t": ("alveolar", "stop", 0), "th": ("alveolar", "stop", 0), "tʰ": ("alveolar", "stop", 0), "d": ("alveolar", "stop", 1),
    "ɗ": ("alveolar", "stop", 1), "n": ("alveolar", "nasal", 1), "s": ("alveolar", "fric", 0), "z": ("alveolar", "fric", 1),
    "ts": ("alveolar", "affr", 0), "tsh": ("alveolar", "affr", 0), "l": ("alveolar", "lateral", 1),
    "ɹ": ("alveolar", "approx", 1), "ɾ": ("alveolar", "tap", 1),
    "ʃ": ("postalveolar", "fric", 0), "ʒ": ("postalveolar", "fric", 1), "tʃ": ("postalveolar", "affr", 0),
    "dʒ": ("postalveolar", "affr", 1),
    "s.": ("retroflex", "fric", 0), "ʂ": ("retroflex", "fric", 0), "ts.": ("retroflex", "affr", 0),
    "ts.h": ("retroflex", "affr", 0), "ʐ": ("retroflex", "fric", 1), "ɻ": ("retroflex", "approx", 1),
    "ɕ": ("palatal", "fric", 0), "tɕ": ("palatal", "affr", 0), "tɕh": ("palatal", "affr", 0), "j": ("palatal", "approx", 1),
    "ɲ": ("palatal", "nasal", 1), "c": ("palatal", "stop", 0), "ç": ("palatal", "fric", 0),
    "k": ("velar", "stop", 0), "kh": ("velar", "stop", 0), "kʰ": ("velar", "stop", 0), "ɡ": ("velar", "stop", 1),
    "ŋ": ("velar", "nasal", 1), "x": ("velar", "fric", 0), "ɣ": ("velar", "fric", 1), "χ": ("uvular", "fric", 0),
    "h": ("glottal", "fric", 0), "ʔ": ("glottal", "stop", 0),
}
_MANNER_NEAR = {frozenset({"stop", "affr"}), frozenset({"fric", "affr"}), frozenset({"approx", "lateral"}),
                frozenset({"tap", "stop"}), frozenset({"approx", "tap"})}

GAP = 0.7
NEAR = 0.45  # a substitution at most this costly is "gần đúng"


def cost(a: str, b: str, equivalent=None) -> float:
    a, b = base(a), base(b)
    if a == b or (equivalent and frozenset({a, b}) in equivalent):
        return 0.0
    va, vb = bool(a) and a[0] in VOWEL_CHARS, bool(b) and b[0] in VOWEL_CHARS
    if va and vb:
        if a[0] == b[0] or a[-1] == b[-1]:  # diphthong vs its part, or a near vowel (ɪ / iː is not this: i vs ɪ)
            return 0.35
        return 0.55
    if va != vb:
        return 1.0
    ca, cb = CONS.get(a), CONS.get(b)
    if not ca or not cb:
        return 0.8
    place = min(abs(_P[ca[0]] - _P[cb[0]]) / 3, 1.0)
    manner = 0 if ca[1] == cb[1] else 0.5 if frozenset({ca[1], cb[1]}) in _MANNER_NEAR else 1
    return 0.1 + 0.35 * place + 0.35 * manner + 0.15 * (ca[2] != cb[2])


def align(expected: list[str], heard: list[str], equivalent=None) -> list[tuple[int | None, int | None, float]]:
    """-> pairs (expected index or None = extra sound, heard index or None = missing sound, cost)."""
    n, m = len(expected), len(heard)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i * GAP
    for j in range(1, m + 1):
        dp[0][j] = j * GAP
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i][j] = min(dp[i - 1][j - 1] + cost(expected[i - 1], heard[j - 1], equivalent),
                           dp[i - 1][j] + GAP, dp[i][j - 1] + GAP)
    out = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            c = cost(expected[i - 1], heard[j - 1], equivalent)
            if abs(dp[i][j] - (dp[i - 1][j - 1] + c)) < 1e-9:
                out.append((i - 1, j - 1, c))
                i, j = i - 1, j - 1
                continue
        if i > 0 and abs(dp[i][j] - (dp[i - 1][j] + GAP)) < 1e-9:
            out.append((i - 1, None, GAP))
            i -= 1
        else:
            out.append((None, j - 1, GAP))
            j -= 1
    return out[::-1]
