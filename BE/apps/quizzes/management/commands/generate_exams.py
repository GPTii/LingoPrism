import random

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.quizzes.models import Exam, ExamQuestion, Question
from apps.vocab.models import ReviewStatus, Topic, WordTranslation

LANG_NAME = {"en": "tiếng Anh", "zh-Hans": "tiếng Trung (giản thể)", "zh-Hant": "tiếng Trung (phồn thể)"}
TOPICS = ["animals", "fruits-vegetables", "home", "transport", "places", "clothing"]


def _reading(t):
    if t.pinyin:
        return f"{t.text} ({t.pinyin})"
    if t.ipa:
        return f"{t.text} /{t.ipa}/"
    return t.text


class Command(BaseCommand):
    help = "Sinh đề kiểm tra mẫu (trắc nghiệm + điền từ + tự luận) từ từ vựng đã kiểm tra"

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=2026)

    @transaction.atomic
    def handle(self, *args, seed=2026, **opts):
        rng = random.Random(seed)
        created = 0
        for slug in TOPICS:
            topic = Topic.objects.filter(slug=slug).first()
            if topic is None:
                continue
            for code, lang_name in LANG_NAME.items():
                title = f"{topic.name_vi} – {lang_name}"
                if Exam.objects.filter(title=title).exists():
                    continue
                trs = list(WordTranslation.objects.filter(
                    word__topics=topic, language_id=code, status=ReviewStatus.VERIFIED, word__part_of_speech="noun",
                ).select_related("word"))
                vi = {t.word_id: t.text for t in WordTranslation.objects.filter(
                    word__topics=topic, language_id="vi", status=ReviewStatus.VERIFIED)}
                trs = [t for t in trs if t.word_id in vi]
                if len(trs) < 11:
                    continue
                rng.shuffle(trs)
                exam = Exam.objects.create(
                    title=title, language_id=code, topic=topic, is_published=True, time_limit_minutes=10,
                    description=f"Kiểm tra từ vựng chủ đề {topic.name_vi.lower()} bằng {lang_name}.",
                )
                order = 0
                for t in trs[:8]:
                    others = [o.text for o in trs if o.word_id != t.word_id and o.text != t.text]
                    opts = rng.sample(others, 3) + [t.text]
                    rng.shuffle(opts)
                    q = Question.objects.create(
                        kind=Question.Kind.MCQ, language_id=code, topic=topic, word=t.word,
                        prompt=f"“{vi[t.word_id]}” trong {lang_name} là gì?",
                        options=[{"text": o, "correct": o == t.text} for o in opts],
                        explanation=_reading(t),
                    )
                    ExamQuestion.objects.create(exam=exam, question=q, order=order)
                    order += 1
                for t in trs[8:10]:
                    q = Question.objects.create(
                        kind=Question.Kind.FILL, language_id=code, topic=topic, word=t.word,
                        prompt=f"Viết từ {lang_name} có nghĩa là “{vi[t.word_id]}”.",
                        accepted_answers=[t.text] + [v for v in t.accepted_variants if v],
                        explanation=_reading(t),
                    )
                    ExamQuestion.objects.create(exam=exam, question=q, order=order, points=2)
                    order += 1
                words = ", ".join(t.text for t in trs[:3])
                q = Question.objects.create(
                    kind=Question.Kind.ESSAY, language_id=code, topic=topic,
                    prompt=f"Viết 2–3 câu bằng {lang_name} có sử dụng các từ: {words}.",
                )
                ExamQuestion.objects.create(exam=exam, question=q, order=order, points=4)
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Đã tạo {created} đề kiểm tra"))
