"""CMUdict ARPAbet -> IPA (General American), with stress marks placed by the maximal-onset rule."""

VOWELS = {
    "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ", "AW": "aʊ", "AY": "aɪ", "EH": "ɛ", "ER": "ɝ",
    "EY": "eɪ", "IH": "ɪ", "IY": "i", "OW": "oʊ", "OY": "ɔɪ", "UH": "ʊ", "UW": "u",
}
CONSONANTS = {
    "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "F": "f", "G": "ɡ", "HH": "h", "JH": "dʒ", "K": "k",
    "L": "l", "M": "m", "N": "n", "NG": "ŋ", "P": "p", "R": "r", "S": "s", "SH": "ʃ", "T": "t",
    "TH": "θ", "V": "v", "W": "w", "Y": "j", "Z": "z", "ZH": "ʒ",
}
# Legal English syllable onsets (ARPAbet), used to split consonant clusters between vowels.
ONSETS = {
    (), *[(c,) for c in CONSONANTS if c != "NG"],
    ("P", "L"), ("P", "R"), ("B", "L"), ("B", "R"), ("T", "R"), ("D", "R"), ("K", "L"), ("K", "R"),
    ("G", "L"), ("G", "R"), ("F", "L"), ("F", "R"), ("TH", "R"), ("SH", "R"), ("S", "L"), ("S", "M"),
    ("S", "N"), ("S", "P"), ("S", "T"), ("S", "K"), ("S", "W"), ("K", "W"), ("T", "W"), ("D", "W"),
    ("G", "W"), ("P", "Y"), ("B", "Y"), ("K", "Y"), ("F", "Y"), ("M", "Y"), ("HH", "Y"), ("V", "Y"),
    ("S", "P", "L"), ("S", "P", "R"), ("S", "T", "R"), ("S", "K", "R"), ("S", "K", "W"), ("S", "K", "Y"),
}


def arpabet_to_ipa(phones: list[str]) -> str:
    """['P','AH0','T','EY1','T','OW2'] -> 'pəˈteɪtoʊ'. A "|" separates words of a phrase."""
    if "|" in phones:
        words, current = [], []
        for p in phones:
            if p == "|":
                words.append(current)
                current = []
            else:
                current.append(p)
        words.append(current)
        return " ".join(_word_to_ipa(w) for w in words)
    return _word_to_ipa(phones)


def _word_to_ipa(phones: list[str]) -> str:
    units = []  # (ipa, is_vowel, stress)
    for p in phones:
        base, stress = (p[:-1], int(p[-1])) if p[-1].isdigit() else (p, None)
        if base in VOWELS:
            if base == "AH" and stress == 0:
                ipa = "ə"
            elif base == "ER" and stress == 0:
                ipa = "ɚ"
            else:
                ipa = VOWELS[base]
            units.append((ipa, True, stress, base))
        else:
            units.append((CONSONANTS[base], False, None, base))

    vowel_idx = [i for i, u in enumerate(units) if u[1]]
    # syllable start index for every vowel (maximal onset)
    starts = []
    prev_vowel = -1
    for v in vowel_idx:
        cluster = list(range(prev_vowel + 1, v))
        start = v
        for k in range(len(cluster) + 1):
            candidate = tuple(units[i][3] for i in cluster[k:])
            if candidate in ONSETS or prev_vowel == -1:
                start = cluster[k] if k < len(cluster) else v
                break
        starts.append(0 if prev_vowel == -1 else start)
        prev_vowel = v

    primary_seen = False
    marks = {}
    for v, start in zip(vowel_idx, starts):
        stress = units[v][2]
        if stress == 1:
            marks[start] = "ˈ"
            primary_seen = True
        elif stress == 2 and not primary_seen:
            marks[start] = "ˌ"
    if len(vowel_idx) == 1:
        marks = {}  # monosyllables are written without a stress mark

    return "".join(marks.get(i, "") + u[0] for i, u in enumerate(units))
