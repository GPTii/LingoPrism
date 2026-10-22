"""Smart Distractor Generation: wrong options that are *plausible* (close in meaning) but never correct.

1. Candidates  – every verified word of the target language, scored by cosine similarity of the Word2Vec
                 concept vectors (word2vec.py, trained on Tatoeba).
2. Filtering   – drop anything that could also be a right answer or gives the answer away:
                 the same concept; near-synonyms (cosine ≥ SYNONYM_COS); the same Vietnamese meaning;
                 the same / contained target text (homographs, 土豆 vs 馬鈴薯-type regional variants);
                 an English alias shared with the answer; a different part of speech when enough remain.
3. Ranking     – 0.6·cos + 0.15·same topic + 0.15·same part of speech + 0.1·level closeness,
                 then picked greedily with a diversity rule (no two distractors closer than DIVERSE_COS),
                 so the options are hard but not all the same thing.
Words without a vector fall back to the random same-topic baseline.
"""
from functools import lru_cache

import numpy as np
from django.conf import settings

from apps.learning.questions import DistractorProvider, RandomSameTopicDistractors
from apps.vocab.models import ReviewStatus, Word, WordTranslation

VECTORS = settings.BASE_DIR / "seed" / "cache" / "concept_vectors.npz"
SYNONYM_COS = 0.88
DIVERSE_COS = 0.8


@lru_cache(maxsize=1)
def load_vectors(mtime: float = 0) -> dict:
    if not VECTORS.exists():
        return {}
    data = np.load(VECTORS, allow_pickle=False)
    return dict(zip(data["slugs"].tolist(), data["vectors"]))


def vectors() -> dict:
    return load_vectors(VECTORS.stat().st_mtime if VECTORS.exists() else 0)


def _texts(code):
    out = {}
    for t in WordTranslation.objects.filter(language_id=code, status=ReviewStatus.VERIFIED).values("word_id", "text"):
        out[t["word_id"]] = t["text"]
    return out


def rank_candidates(word: Word, code: str, k: int = 3, pool: list[Word] | None = None) -> list[tuple[Word, float]]:
    vec = vectors()
    v = vec.get(word.slug)
    if v is None:
        return []
    pool = pool if pool is not None else list(
        Word.objects.filter(translations__language_id=code, translations__status=ReviewStatus.VERIFIED)
        .exclude(id=word.id).prefetch_related("topics").distinct())
    target, vi = _texts(code), _texts("vi")
    en = {t.word_id: t for t in WordTranslation.objects.filter(language_id="en", word_id__in=[word.id] + [w.id for w in pool])}
    answer_text, answer_vi = target.get(word.id, ""), vi.get(word.id, "")
    answer_aliases = set((en[word.id].accepted_variants or []) + [en[word.id].text]) if word.id in en else set()
    topics = set(word.topics.values_list("id", flat=True))
    lvl = (word.levels or {})
    scored = []
    for c in pool:
        cv = vec.get(c.slug)
        if cv is None or c.id not in target:
            continue
        cos = float(np.dot(v, cv))
        text = target[c.id]
        if (cos >= SYNONYM_COS or text == answer_text or (answer_text and (answer_text in text or text in answer_text))
                or (answer_vi and vi.get(c.id) == answer_vi)
                or (c.id in en and en[c.id].text in answer_aliases)):
            continue
        same_topic = bool(topics & {t.id for t in c.topics.all()})
        same_pos = c.part_of_speech == word.part_of_speech
        level_gap = abs((c.levels or {}).get("en", 2) - lvl.get("en", 2))
        scored.append((c, 0.6 * cos + 0.15 * same_topic + 0.15 * same_pos + 0.1 * (1 - level_gap / 3), cos, same_pos))
    scored.sort(key=lambda x: -x[1])
    if sum(1 for s in scored if s[3]) >= k:  # keep the answer's part of speech when possible
        scored = [s for s in scored if s[3]]
    chosen = []
    for c, s, cos, _ in scored:
        if all(float(np.dot(vec[c.slug], vec[o.slug])) < DIVERSE_COS for o, _ in chosen):
            chosen.append((c, round(s, 4)))
        if len(chosen) == k:
            break
    return chosen


class SmartDistractors(DistractorProvider):
    name = "smart"

    def pick(self, word, target, k):
        chosen = rank_candidates(word, target.code, k)
        if len(chosen) < k:
            extra = RandomSameTopicDistractors().pick(word, target, k)
            return [c for c, _ in chosen] + [w for w in extra if w.id not in {c.id for c, _ in chosen}][: k - len(chosen)]
        return [c for c, _ in chosen]
