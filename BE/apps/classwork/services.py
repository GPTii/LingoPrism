"""Who may do what with a group's assignments, automatic marking, hand-in and marking by a leader."""
import unicodedata
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.community.models import GroupMember
from apps.notifications.models import Notification
from apps.notifications.services import notify

from .models import Assignment, AssignmentAnswer, AssignmentQuestion, AssignmentSubmission

MAX_FILE_MB = 10
FILE_TYPES = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".jpg", ".jpeg", ".png", ".webp",
              ".heic", ".mp3", ".m4a", ".wav", ".zip"}


class ClassworkError(Exception):
    pass


def membership(user, group_id: int) -> GroupMember | None:
    return GroupMember.objects.filter(group_id=group_id, user=user, status=GroupMember.Status.ACTIVE).first()


def is_leader(user, group_id: int) -> bool:
    m = membership(user, group_id)
    return bool(m and m.role == GroupMember.Role.LEADER) or getattr(user, "is_staff_role", False)


def check_file(f, label="File"):
    from pathlib import Path

    if f.size > MAX_FILE_MB * 1024 * 1024:
        raise ClassworkError(f"{label} tối đa {MAX_FILE_MB} MB")
    if Path(f.name).suffix.lower() not in FILE_TYPES:
        raise ClassworkError(f"{label}: chỉ nhận PDF, Word, PowerPoint, Excel, ảnh, âm thanh, txt hoặc zip")


def normalize(text: str) -> str:
    t = unicodedata.normalize("NFC", (text or "").strip()).lower()
    return "".join(t.split()) if any("一" <= ch <= "鿿" for ch in t) else " ".join(t.split())


def auto_mark(q: AssignmentQuestion, a: AssignmentAnswer):
    """Multiple choice and fill-in are marked at once; written answers and files wait for a leader."""
    if q.kind == AssignmentQuestion.Kind.MCQ:
        correct = next((i for i, o in enumerate(q.options) if o.get("correct")), None)
        a.is_correct = a.selected_option is not None and a.selected_option == correct
        a.score = q.points if a.is_correct else Decimal("0")
    elif q.kind == AssignmentQuestion.Kind.FILL:
        a.is_correct = normalize(a.text) in {normalize(x) for x in q.accepted_answers}
        a.score = q.points if a.is_correct else Decimal("0")
    elif not a.text.strip() and not a.attachment:
        a.is_correct, a.score = False, Decimal("0")  # left empty: nothing to mark
    else:
        a.is_correct, a.score = None, None


def recompute(sub: AssignmentSubmission):
    questions = list(sub.assignment.questions.all())
    if questions:
        answers = list(sub.answers.all())
        sub.max_score = sum((q.points for q in questions), Decimal("0"))
        pending = any(a.is_correct is None for a in answers)
        sub.score = None if pending else sum((a.score or Decimal("0") for a in answers), Decimal("0"))
    else:
        sub.max_score = sub.assignment.points
        pending = sub.score is None
    sub.status = AssignmentSubmission.Status.SUBMITTED if pending else AssignmentSubmission.Status.GRADED


def submit(user, assignment: Assignment, answers: dict[int, dict], files: dict, text: str = "") -> AssignmentSubmission:
    """answers: {question_id: {"selected_option", "text"}}, files: {question_id or "main": UploadedFile}.
    A member may hand in again until a leader has marked the work."""
    if not membership(user, assignment.group_id):
        raise ClassworkError("Bạn không ở trong nhóm này")
    if assignment.status != Assignment.Status.PUBLISHED:
        raise ClassworkError("Bài tập đã đóng" if assignment.status == Assignment.Status.CLOSED else "Bài tập chưa được giao")
    now = timezone.now()
    late = bool(assignment.due_at and now > assignment.due_at)
    if late and not assignment.allow_late:
        raise ClassworkError("Đã quá hạn nộp bài")
    for f in files.values():
        check_file(f)
    with transaction.atomic():
        sub, _ = AssignmentSubmission.objects.select_for_update().get_or_create(assignment=assignment, user=user)
        if sub.graded_at:
            raise ClassworkError("Bài đã được chấm, không nộp lại được")
        sub.submitted_at, sub.late, sub.text = now, late, text.strip()
        if "main" in files:
            sub.attachment, sub.attachment_name = files["main"], files["main"].name[:200]
        for q in assignment.questions.all():
            given = answers.get(q.id, {})
            a, _ = AssignmentAnswer.objects.get_or_create(submission=sub, question=q)
            a.selected_option = given.get("selected_option")
            a.text = str(given.get("text") or "")[:5000]
            if q.id in files:
                a.attachment, a.attachment_name = files[q.id], files[q.id].name[:200]
            a.feedback = ""
            auto_mark(q, a)
            a.save()
        if not assignment.questions.exists():
            sub.score = None
        recompute(sub)
        if sub.status == AssignmentSubmission.Status.GRADED:
            sub.graded_at = now  # only auto-marked questions: final, or the answers could be found by trying again
        sub.save()
    for m in assignment.group.members.filter(role=GroupMember.Role.LEADER, status="active").exclude(user=user):
        notify(m.user, Notification.Kind.ASSIGNMENT, f"{user.display_name} đã nộp bài",
               f"{assignment.title}{' (nộp muộn)' if late else ''}",
               data={"route": route(assignment, submission=sub.id)})
    return sub


def grade(leader, sub: AssignmentSubmission, marks: list[dict], score=None, feedback: str = "") -> AssignmentSubmission:
    """marks: [{"answer": id, "score", "feedback"}]; score: the whole work when the assignment has no questions."""
    with transaction.atomic():
        for m in marks:
            a = sub.answers.select_related("question").filter(pk=m["answer"]).first()
            if a is None:
                raise ClassworkError("Câu trả lời không thuộc bài này")
            s = Decimal(str(m["score"]))
            if s < 0 or s > a.question.points:
                raise ClassworkError(f"Điểm câu phải từ 0 đến {a.question.points}")
            a.score, a.is_correct = s, s >= a.question.points / 2
            a.feedback = str(m.get("feedback") or "")[:2000]
            a.save()
        if not sub.assignment.questions.exists():
            if score is None:
                raise ClassworkError("Hãy cho điểm bài làm")
            s = Decimal(str(score))
            if s < 0 or s > sub.assignment.points:
                raise ClassworkError(f"Điểm phải từ 0 đến {sub.assignment.points}")
            sub.score = s
        sub.feedback = (feedback or "")[:4000]
        recompute(sub)
        if sub.status != AssignmentSubmission.Status.GRADED:
            raise ClassworkError("Còn câu chưa chấm")
        sub.graded_by, sub.graded_at = leader, timezone.now()
        sub.save()
    notify(sub.user, Notification.Kind.ASSIGNMENT, "Bài tập đã được chấm",
           f"{sub.assignment.title}: {sub.score:g}/{sub.max_score:g} điểm",
           data={"route": route(sub.assignment)})
    return sub


def publish(assignment: Assignment):
    if not assignment.title.strip():
        raise ClassworkError("Bài tập cần có tên")
    if not assignment.questions.exists() and not assignment.instructions.strip() and not assignment.attachment:
        raise ClassworkError("Thêm câu hỏi, đề bài hoặc file trước khi giao")
    for q in assignment.questions.all():
        if q.kind == AssignmentQuestion.Kind.MCQ and sum(bool(o.get("correct")) for o in q.options) != 1:
            raise ClassworkError(f"Câu {q.order + 1}: trắc nghiệm cần đúng một đáp án đúng")
        if q.kind == AssignmentQuestion.Kind.FILL and not q.accepted_answers:
            raise ClassworkError(f"Câu {q.order + 1}: điền từ cần ít nhất một đáp án")
    assignment.status, assignment.published_at = Assignment.Status.PUBLISHED, timezone.now()
    assignment.save(update_fields=["status", "published_at", "updated_at"])
    due = f" – hạn {timezone.localtime(assignment.due_at):%H:%M %d/%m}" if assignment.due_at else ""
    for m in assignment.group.members.filter(status="active").exclude(role=GroupMember.Role.LEADER).select_related("user"):
        notify(m.user, Notification.Kind.ASSIGNMENT, f"Bài tập mới trong {assignment.group.name}",
               f"{assignment.title}{due}", data={"route": route(assignment)})


def route(assignment: Assignment, submission: int | None = None) -> str:
    r = f"/community/groups/{assignment.group_id}?tab=assignments&a={assignment.id}"
    return r + (f"&s={submission}" if submission else "")
