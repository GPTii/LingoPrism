"""Question generation for study sessions.

Distractors come from a `DistractorProvider` so Phase 5 can swap the random baseline for
Smart Distractor Generation without changing the API. Regional variants / synonyms of the
answer are never used as wrong options (PLAN.md §3b).
"""
import random

from apps.vocab.models import ReviewStatus, Word, WordTranslation
from apps.vocab.services import Target, translation_payload


class DistractorProvider:
    name = "base"

    def pick(self, word: Word, target: Target, k: int) -> list[Word]:
        raise NotImplementedError


class RandomSameTopicDistractors(DistractorProvider):
    """Baseline: random verified words from the same topic(s), same part of speech."""

    name = "random"

    def pick(self, word, target, k):
        topic_ids = list(word.topics.values_list("id", flat=True))
        pool = (
            Word.objects.filter(topics__id__in=topic_ids, part_of_speech=word.part_of_speech)
            .exclude(id=word.id)
            .filter(translations__language_id=target.code, translations__status=ReviewStatus.VERIFIED)
            .distinct()
        )
        ids = list(pool.values_list("id", flat=True))
        if len(ids) < k:
            extra = (
                Word.objects.filter(part_of_speech=word.part_of_speech)
                .exclude(id__in=ids + [word.id])
                .filter(translations__language_id=target.code, translations__status=ReviewStatus.VERIFIED)
                .values_list("id", flat=True)
                .distinct()[:200]
            )
            ids += list(extra)
        chosen = random.sample(ids, min(k, len(ids)))
        return list(Word.objects.filter(id__in=chosen))


def get_distractor_provider() -> DistractorProvider:
    """Random baseline or Smart Distractor Generation (apps.algorithms), as chosen on the admin page."""
    from apps.algorithms.models import AlgorithmConfig

    if AlgorithmConfig.get().distractor == "smart":
        from apps.algorithms.distractor import VECTORS, SmartDistractors

        if VECTORS.exists():
            return SmartDistractors()
    return RandomSameTopicDistractors()


def _texts(words, code):
    trs = WordTranslation.objects.filter(word__in=words, language_id=code, status=ReviewStatus.VERIFIED)
    return {t.word_id: t for t in trs}


def _questions_vi(word: Word, tr, provider: DistractorProvider) -> list[dict]:
    accepted = [tr.text] + [v for v in tr.accepted_variants if v]
    payload = translation_payload(tr)
    questions = [{"type": "flashcard", "front": payload, "back": word.emoji}]
    others = [t.text for t in _texts(provider.pick(word, Target("vi", "vi", ""), 3), "vi").values() if t.text != tr.text][:3]
    if (word.emoji or word.image) and len(others) >= 2:
        opts = others + [tr.text]
        random.shuffle(opts)
        questions.append({"type": "choose_target", "prompt": word.emoji, "options": opts, "answer": tr.text})
    questions.append({"type": "listen_type", "audio": payload, "accepted": accepted, "answer": tr.text})
    return questions


def build_questions(word: Word, target: Target, by_lang: dict, provider: DistractorProvider) -> list[dict]:
    tr = by_lang.get(target.code)
    vi = by_lang.get("vi")
    if tr is None:
        return []
    if target.code == "vi":
        # Vietnamese is taught to Vietnamese children: picture + sound, never an English gloss
        return _questions_vi(word, tr, provider)
    meaning = vi.text if vi else ""
    distractors = provider.pick(word, target, 3)
    d_target = _texts(distractors, target.code)
    d_meaning = _texts(distractors, "vi" if target.code != "vi" else "en")
    # never offer an option identical to the answer (homographs / shared forms)
    target_opts = [t.text for wid, t in d_target.items() if t.text != tr.text][:3]
    meaning_opts = [t.text for wid, t in d_meaning.items() if t.text != meaning][:3]
    accepted = [tr.text] + [v for v in tr.accepted_variants if v]

    questions = [
        {"type": "flashcard", "front": translation_payload(tr), "back": meaning},
    ]
    if len(target_opts) >= 2:
        opts = target_opts + [tr.text]
        random.shuffle(opts)
        questions.append({"type": "choose_target", "prompt": meaning, "options": opts, "answer": tr.text})
    if len(meaning_opts) >= 2 and meaning:
        opts = meaning_opts + [meaning]
        random.shuffle(opts)
        questions.append({"type": "choose_meaning", "prompt": translation_payload(tr), "options": opts, "answer": meaning})
    questions.append({"type": "type_target", "prompt": meaning, "accepted": accepted, "answer": tr.text})
    questions.append({"type": "listen_type", "audio": translation_payload(tr), "accepted": accepted, "answer": tr.text})

    if target.learn == "zh" and tr.pinyin:
        wrong = [t.pinyin for t in d_target.values() if t.pinyin and t.pinyin != tr.pinyin][:3]
        if len(wrong) >= 2:
            opts = wrong + [tr.pinyin]
            random.shuffle(opts)
            questions.append({"type": "choose_pinyin", "prompt": tr.text, "options": opts, "answer": tr.pinyin})
    return questions
