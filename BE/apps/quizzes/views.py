import unicodedata
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.bulk import BulkDeleteMixin, Conflict
from apps.core.permissions import IsStaffRole
from apps.notifications.models import Notification
from apps.notifications.services import notify

from .models import Answer, Exam, ExamQuestion, Question, Submission


def normalize(text: str, chinese: bool) -> str:
    t = unicodedata.normalize("NFC", (text or "").strip())
    return "".join(t.split()) if chinese else " ".join(t.lower().split())


# ------------------------------------------------------------------ serializers

class QuestionPublicSerializer(serializers.ModelSerializer):
    """What a learner sees while taking an exam (no correct answers)."""

    options = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "kind", "language", "prompt", "image_url", "options"]

    def get_options(self, obj):
        return [o["text"] for o in obj.options]


class ExamListSerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(read_only=True)
    my_best = serializers.SerializerMethodField()
    topic_name = serializers.CharField(source="topic.name_vi", default=None, read_only=True)

    class Meta:
        model = Exam
        fields = ["id", "title", "description", "language", "topic", "topic_name", "audience", "time_limit_minutes",
                  "pass_percent", "question_count", "my_best", "created_at"]

    def get_my_best(self, obj):
        user = self.context["request"].user
        subs = [s for s in obj.submissions.all() if s.user_id == user.id and s.status != Submission.Status.IN_PROGRESS]
        if not subs:
            return None
        best = max(subs, key=lambda s: s.percent)
        return {"percent": best.percent, "status": best.status, "submission": best.id}


class AnswerResultSerializer(serializers.ModelSerializer):
    question = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = ["id", "question", "selected_option", "text", "is_correct", "score", "feedback"]

    def get_question(self, obj):
        q = obj.exam_question.question
        return {
            "id": q.id, "kind": q.kind, "prompt": q.prompt, "image_url": q.image_url,
            "options": [o["text"] for o in q.options],
            "correct_option": next((i for i, o in enumerate(q.options) if o.get("correct")), None),
            "accepted_answers": q.accepted_answers, "explanation": q.explanation,
            "points": obj.exam_question.points,
        }


class SubmissionSerializer(serializers.ModelSerializer):
    exam_title = serializers.CharField(source="exam.title", read_only=True)
    percent = serializers.FloatField(read_only=True)
    passed = serializers.SerializerMethodField()
    answers = serializers.SerializerMethodField()
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Submission
        fields = ["id", "exam", "exam_title", "user_email", "status", "started_at", "submitted_at", "score", "max_score",
                  "percent", "passed", "feedback", "graded_at", "answers"]

    def get_passed(self, obj):
        return obj.status == Submission.Status.GRADED and obj.percent >= obj.exam.pass_percent

    def get_answers(self, obj):
        if obj.status == Submission.Status.IN_PROGRESS:
            return []
        return AnswerResultSerializer(obj.answers.select_related("exam_question__question"), many=True).data


class SubmitSerializer(serializers.Serializer):
    class AnswerIn(serializers.Serializer):
        question = serializers.IntegerField()
        selected_option = serializers.IntegerField(required=False, allow_null=True)
        text = serializers.CharField(required=False, allow_blank=True)

    answers = AnswerIn(many=True)


class GradeSerializer(serializers.Serializer):
    class GradeIn(serializers.Serializer):
        answer = serializers.IntegerField()
        score = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal("0"))
        feedback = serializers.CharField(required=False, allow_blank=True)

    grades = GradeIn(many=True)
    feedback = serializers.CharField(required=False, allow_blank=True)


# ------------------------------------------------------------------ learner

def _recompute(sub: Submission):
    answers = list(sub.answers.select_related("exam_question"))
    sub.max_score = sum((a.exam_question.points for a in answers), Decimal("0"))
    sub.score = sum((a.score or Decimal("0") for a in answers), Decimal("0"))
    pending = any(a.is_correct is None for a in answers)
    sub.status = Submission.Status.SUBMITTED if pending else Submission.Status.GRADED


@extend_schema(tags=["exams"])
class ExamViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ExamListSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Exam.objects.none()
        user = self.request.user
        qs = Exam.objects.filter(is_published=True).annotate(question_count=Count("exam_questions")).prefetch_related("submissions")
        lang = self.request.query_params.get("language")
        if lang:
            qs = qs.filter(language_id=lang)
        if user.learner_type == "kid":
            qs = qs.filter(audience__in=["all", "kid"])
        return qs

    def retrieve(self, request, *args, **kwargs):
        exam = self.get_object()
        data = ExamListSerializer(exam, context={"request": request}).data
        data["questions_preview"] = exam.exam_questions.count()
        return Response(data)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        exam = self.get_object()
        sub = Submission.objects.filter(user=request.user, exam=exam, status=Submission.Status.IN_PROGRESS).first()
        sub = sub or Submission.objects.create(user=request.user, exam=exam)
        eqs = exam.exam_questions.select_related("question")
        return Response({
            "submission": sub.id, "started_at": sub.started_at, "time_limit_minutes": exam.time_limit_minutes,
            "title": exam.title, "language": exam.language_id,
            "questions": [{"points": eq.points, **QuestionPublicSerializer(eq.question).data} for eq in eqs],
        })


@extend_schema(tags=["exams"])
class SubmissionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = SubmissionSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Submission.objects.none()
        return Submission.objects.filter(user=self.request.user).select_related("exam")

    @extend_schema(request=SubmitSerializer)
    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        sub = self.get_object()
        if sub.status != Submission.Status.IN_PROGRESS:
            return Response({"detail": "Bài đã nộp", "errors": {}}, status=400)
        ser = SubmitSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        given = {a["question"]: a for a in ser.validated_data["answers"]}
        chinese = sub.exam.language_id.startswith("zh")
        with transaction.atomic():
            for eq in sub.exam.exam_questions.select_related("question"):
                q, a = eq.question, given.get(eq.question_id, {})
                ans = Answer(submission=sub, exam_question=eq, selected_option=a.get("selected_option"), text=a.get("text", ""))
                if q.kind == Question.Kind.MCQ:
                    correct_idx = next((i for i, o in enumerate(q.options) if o.get("correct")), None)
                    ans.is_correct = ans.selected_option is not None and ans.selected_option == correct_idx
                    ans.score = eq.points if ans.is_correct else Decimal("0")
                elif q.kind == Question.Kind.FILL:
                    accepted = {normalize(x, chinese) for x in q.accepted_answers}
                    ans.is_correct = normalize(ans.text, chinese) in accepted
                    ans.score = eq.points if ans.is_correct else Decimal("0")
                else:
                    ans.is_correct = None if ans.text.strip() else False
                    ans.score = None if ans.text.strip() else Decimal("0")
                ans.save()
            sub.submitted_at = timezone.now()
            _recompute(sub)
            sub.save()
        if sub.status == Submission.Status.GRADED:
            from apps.gamification.services import award_xp, mark_activity

            mark_activity(request.user)
            award_xp(request.user, "exam", int(sub.percent // 5), source_id=str(sub.id), note=sub.exam.title)
        return Response(SubmissionSerializer(sub).data)


# ------------------------------------------------------------------ staff

class AdminQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "kind", "language", "topic", "word", "prompt", "image_url", "options", "accepted_answers",
                  "explanation", "difficulty", "created_at"]

    def validate(self, attrs):
        kind = attrs.get("kind", getattr(self.instance, "kind", None))
        if kind == Question.Kind.MCQ:
            opts = attrs.get("options", getattr(self.instance, "options", []))
            if len(opts) < 2 or sum(1 for o in opts if o.get("correct")) != 1:
                raise serializers.ValidationError("Câu trắc nghiệm cần ít nhất 2 phương án và đúng 1 đáp án đúng")
        if kind == Question.Kind.FILL and not attrs.get("accepted_answers", getattr(self.instance, "accepted_answers", [])):
            raise serializers.ValidationError("Câu điền từ cần ít nhất 1 đáp án")
        return attrs


class AdminExamSerializer(serializers.ModelSerializer):
    question_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    questions = serializers.SerializerMethodField()
    submission_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Exam
        fields = ["id", "title", "description", "language", "topic", "audience", "time_limit_minutes", "pass_percent",
                  "is_published", "question_ids", "questions", "submission_count", "created_at"]

    def get_questions(self, obj):
        return [{"id": eq.question_id, "points": eq.points, "order": eq.order, "kind": eq.question.kind,
                 "prompt": eq.question.prompt} for eq in obj.exam_questions.select_related("question")]

    def _set_questions(self, exam, ids):
        ExamQuestion.objects.filter(exam=exam).delete()
        for i, qid in enumerate(ids):
            ExamQuestion.objects.create(exam=exam, question_id=qid, order=i)

    def create(self, validated):
        ids = validated.pop("question_ids", [])
        exam = super().create(validated)
        self._set_questions(exam, ids)
        return exam

    def update(self, instance, validated):
        ids = validated.pop("question_ids", None)
        exam = super().update(instance, validated)
        if ids is not None:
            self._set_questions(exam, ids)
        return exam


@extend_schema(tags=["admin-exams"])
class AdminQuestionViewSet(BulkDeleteMixin, viewsets.ModelViewSet):
    serializer_class = AdminQuestionSerializer
    permission_classes = [IsStaffRole]
    filterset_fields = ["kind", "language", "topic"]
    search_fields = ["prompt"]
    queryset = Question.objects.order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, question):
        exams = list(question.exams.values_list("title", flat=True)[:3])
        if exams:
            raise Conflict(f"Đang nằm trong đề: {', '.join(exams)} – bỏ khỏi đề trước khi xoá.")
        question.delete()


@extend_schema(tags=["admin-exams"])
class AdminExamViewSet(BulkDeleteMixin, viewsets.ModelViewSet):
    serializer_class = AdminExamSerializer
    permission_classes = [IsStaffRole]
    filterset_fields = ["language", "is_published", "topic"]
    search_fields = ["title"]

    def get_queryset(self):
        return Exam.objects.annotate(submission_count=Count("submissions", filter=~Q(submissions__status="in_progress")))

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, exam):
        # learners' results go with an exam: unpublish it instead
        done = exam.submissions.exclude(status="in_progress").count()
        if done:
            raise Conflict(f"Đã có {done} lượt làm bài – tắt xuất bản thay vì xoá để giữ kết quả của học viên.")
        exam.delete()


@extend_schema(tags=["admin-exams"])
class AdminSubmissionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [IsStaffRole]
    filterset_fields = ["status", "exam"]
    date_filter_field = "submitted_at"  # ?created_from/to = the day it was handed in
    queryset = Submission.objects.exclude(status=Submission.Status.IN_PROGRESS).select_related("exam", "user")

    @extend_schema(request=GradeSerializer)
    @action(detail=True, methods=["post"])
    def grade(self, request, pk=None):
        sub = self.get_object()
        ser = GradeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        with transaction.atomic():
            for g in ser.validated_data["grades"]:
                ans = get_object_or_404(Answer, pk=g["answer"], submission=sub)
                if g["score"] > ans.exam_question.points:
                    return Response({"detail": "Điểm vượt quá điểm tối đa của câu", "errors": {}}, status=400)
                ans.score = g["score"]
                ans.is_correct = g["score"] >= ans.exam_question.points / 2
                ans.feedback = g.get("feedback", "")
                ans.save()
            sub.feedback = ser.validated_data.get("feedback", sub.feedback)
            _recompute(sub)
            if sub.status == Submission.Status.GRADED:
                sub.graded_by, sub.graded_at = request.user, timezone.now()
            sub.save()
        if sub.status == Submission.Status.GRADED:
            notify(sub.user, Notification.Kind.EXAM, "Bài kiểm tra đã được chấm",
                   f"{sub.exam.title}: {sub.score}/{sub.max_score} điểm", data={"route": f"/exams/results/{sub.id}"})
        return Response(SubmissionSerializer(sub).data)
