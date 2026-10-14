import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.quizzes.models import Exam, ExamQuestion, Question
from apps.vocab.models import Language

pytestmark = pytest.mark.django_db


@pytest.fixture
def exam(db):
    Language.objects.create(code="zh-Hant", name="zh", native_name="zh", tts_locale="zh-TW")
    exam = Exam.objects.create(title="Động vật", language_id="zh-Hant", is_published=True)
    q1 = Question.objects.create(kind="mcq", language_id="zh-Hant", prompt="con mèo?",
                                 options=[{"text": "狗", "correct": False}, {"text": "貓", "correct": True}])
    q2 = Question.objects.create(kind="fill", language_id="zh-Hant", prompt="con chó", accepted_answers=["狗"])
    q3 = Question.objects.create(kind="essay", language_id="zh-Hant", prompt="Viết câu")
    ExamQuestion.objects.create(exam=exam, question=q1, order=0)
    ExamQuestion.objects.create(exam=exam, question=q2, order=1, points=2)
    ExamQuestion.objects.create(exam=exam, question=q3, order=2, points=4)
    return exam


def test_exam_flow_with_manual_grading(exam):
    learner = User.objects.create_user("l@example.com", "Strong!Pass123")
    staff = User.objects.create_user("s@example.com", "Strong!Pass123", role="staff")
    c = APIClient()
    c.force_authenticate(learner)
    started = c.post(f"/api/v1/exams/{exam.id}/start/").data
    assert "correct" not in str(started["questions"])  # answers are not leaked
    qids = [q["id"] for q in started["questions"]]
    res = c.post(f"/api/v1/submissions/{started['submission']}/submit/", {"answers": [
        {"question": qids[0], "selected_option": 1},
        {"question": qids[1], "text": " 狗 "},
        {"question": qids[2], "text": "我有一隻貓。"},
    ]}, format="json")
    assert res.data["status"] == "submitted" and float(res.data["score"]) == 3.0

    s = APIClient()
    s.force_authenticate(staff)
    pending = s.get("/api/v1/admin/submissions/?status=submitted").data["results"]
    essay = next(a for a in pending[0]["answers"] if a["question"]["kind"] == "essay")
    res = s.post(f"/api/v1/admin/submissions/{pending[0]['id']}/grade/",
                 {"grades": [{"answer": essay["id"], "score": "3.5", "feedback": "Tốt"}]}, format="json")
    assert res.data["status"] == "graded" and float(res.data["score"]) == 6.5
    assert learner.notifications.filter(kind="exam").exists()


def test_simplified_answer_rejected_when_learning_traditional(exam):
    learner = User.objects.create_user("l@example.com", "Strong!Pass123")
    q = Question.objects.get(kind="fill")
    q.accepted_answers = ["貓"]
    q.save()
    c = APIClient()
    c.force_authenticate(learner)
    started = c.post(f"/api/v1/exams/{exam.id}/start/").data
    res = c.post(f"/api/v1/submissions/{started['submission']}/submit/",
                 {"answers": [{"question": q.id, "text": "猫"}]}, format="json")
    fill = next(a for a in res.data["answers"] if a["question"]["kind"] == "fill")
    assert fill["is_correct"] is False


def test_mcq_requires_one_correct(db):
    Language.objects.create(code="en", name="en", native_name="en", tts_locale="en-US")
    staff = User.objects.create_user("s@example.com", "Strong!Pass123", role="staff")
    c = APIClient()
    c.force_authenticate(staff)
    res = c.post("/api/v1/admin/questions/", {"kind": "mcq", "language": "en", "prompt": "?",
                                              "options": [{"text": "a", "correct": True}, {"text": "b", "correct": True}]},
                 format="json")
    assert res.status_code == 400
