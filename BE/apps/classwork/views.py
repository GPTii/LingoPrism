"""Group assignments API (/assignments/). Leaders of a group (its creator, members it promoted) create, give and mark
assignments; members do them. Children's accounts are not in study groups at all (community.views.NotKid)."""

import json
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.aitalk.generator import AiUnavailable
from apps.community.models import Group, GroupMember
from apps.community.views import NotKid, author
from apps.core.throttles import ActionThrottleMixin

from . import services
from .models import Assignment, AssignmentQuestion, AssignmentSubmission


def _url(request, f):
    return request.build_absolute_uri(f.url) if f else None


class QuestionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = AssignmentQuestion
        fields = ["id", "order", "kind", "prompt", "options", "accepted_answers", "points", "explanation"]

    def validate(self, d):
        if d["kind"] == "mcq":
            opts = [o for o in d.get("options") or [] if str(o.get("text", "")).strip()]
            if len(opts) < 2:
                raise ValidationError({"options": "Trắc nghiệm cần ít nhất 2 phương án"})
            d["options"] = [{"text": str(o["text"]).strip()[:500], "correct": bool(o.get("correct"))} for o in opts]
        else:
            d["options"] = []
        d["accepted_answers"] = (
            [str(x).strip()[:200] for x in d.get("accepted_answers") or [] if str(x).strip()]
            if d["kind"] == "fill"
            else []
        )
        return d


class AssignmentWriteSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.filter(status="active"))

    class Meta:
        model = Assignment
        fields = [
            "group",
            "title",
            "instructions",
            "due_at",
            "points",
            "allow_late",
            "show_answers",
            "ai_generated",
            "questions",
        ]

    def validate_points(self, v):
        if v <= 0:
            raise ValidationError("Điểm phải lớn hơn 0")
        return v


def _replace_questions(assignment, questions):
    assignment.questions.all().delete()
    AssignmentQuestion.objects.bulk_create(
        [
            AssignmentQuestion(
                assignment=assignment,
                order=i,
                kind=q["kind"],
                prompt=q["prompt"].strip()[:5000],
                options=q.get("options", []),
                accepted_answers=q.get("accepted_answers", []),
                points=q.get("points") or Decimal("1"),
                explanation=q.get("explanation", "")[:2000],
            )
            for i, q in enumerate(questions)
        ]
    )


@extend_schema(tags=["classwork"])
class AssignmentViewSet(ActionThrottleMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, NotKid]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    serializer_class = AssignmentWriteSerializer
    throttle_scopes = {"import_file": "ai_import", "attachment": "upload", "submit": "upload"}

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Assignment.objects.none()
        u = self.request.user
        qs = Assignment.objects.select_related("group").prefetch_related("questions")
        if not u.is_staff_role:
            groups = GroupMember.objects.filter(user=u, status="active").values("group_id")
            led = GroupMember.objects.filter(user=u, status="active", role="leader").values("group_id")
            qs = qs.filter(group_id__in=groups).filter(~Q(status=Assignment.Status.DRAFT) | Q(group_id__in=led))
        if group := self.request.query_params.get("group"):
            qs = qs.filter(group_id=group)
        return qs.order_by("-published_at", "-created_at")

    def _assignment(self, pk, leader=False) -> Assignment:
        a = get_object_or_404(self.get_queryset(), pk=pk)
        if leader and not services.is_leader(self.request.user, a.group_id):
            raise PermissionDenied("Chỉ trưởng nhóm mới làm được việc này.")
        return a

    # ---------------------------------------------------------------- payloads

    def _summary(self, a: Assignment, leader: bool, mine: AssignmentSubmission | None, counts: dict | None) -> dict:
        d = {
            "id": a.id,
            "group": a.group_id,
            "group_name": a.group.name,
            "title": a.title,
            "status": a.status,
            "due_at": a.due_at,
            "published_at": a.published_at,
            "created_at": a.created_at,
            "question_count": len(a.questions.all()),
            "max_score": a.max_score,
            "has_attachment": bool(a.attachment),
            "ai_generated": a.ai_generated,
            "is_leader": leader,
        }
        if leader and counts is not None:
            d["counts"] = counts
        d["my_submission"] = self._sub_brief(mine) if mine else None
        return d

    @staticmethod
    def _sub_brief(s: AssignmentSubmission) -> dict:
        return {
            "id": s.id,
            "status": s.status,
            "score": s.score,
            "max_score": s.max_score,
            "percent": s.percent,
            "late": s.late,
            "submitted_at": s.submitted_at,
            "graded_at": s.graded_at,
        }

    def _detail(self, a: Assignment) -> dict:
        request, u = self.request, self.request.user
        leader = services.is_leader(u, a.group_id)
        mine = AssignmentSubmission.objects.filter(assignment=a, user=u).prefetch_related("answers").first()
        reveal = leader or (mine is not None and mine.graded_at is not None and a.show_answers)
        d = self._summary(a, leader, mine, None)
        d.update(
            instructions=a.instructions,
            points=a.points,
            allow_late=a.allow_late,
            show_answers=a.show_answers,
            attachment=_url(request, a.attachment),
            attachment_name=a.attachment_name,
            created_by=author(request, a.created_by) if a.created_by else None,
        )
        d["questions"] = [
            {
                "id": q.id,
                "order": q.order,
                "kind": q.kind,
                "prompt": q.prompt,
                "points": q.points,
                "options": q.options if reveal else [{"text": o["text"]} for o in q.options],
                **({"accepted_answers": q.accepted_answers, "explanation": q.explanation} if reveal else {}),
            }
            for q in a.questions.all()
        ]
        if mine:
            d["my_submission"] = self._submission(mine, with_user=False)
        return d

    def _submission(self, s: AssignmentSubmission, with_user=True) -> dict:
        request = self.request
        d = {
            **self._sub_brief(s),
            "text": s.text,
            "attachment": _url(request, s.attachment),
            "attachment_name": s.attachment_name,
            "feedback": s.feedback,
            "answers": [
                {
                    "id": x.id,
                    "question": x.question_id,
                    "selected_option": x.selected_option,
                    "text": x.text,
                    "attachment": _url(request, x.attachment),
                    "attachment_name": x.attachment_name,
                    "is_correct": x.is_correct,
                    "score": x.score,
                    "feedback": x.feedback,
                }
                for x in s.answers.all()
            ],
        }
        if with_user:
            d["user"] = author(request, s.user)
        return d

    # ---------------------------------------------------------------- CRUD

    def list(self, request):
        items = list(self.get_queryset())
        u = request.user
        mine = {s.assignment_id: s for s in AssignmentSubmission.objects.filter(user=u, assignment__in=items)}
        led = set(GroupMember.objects.filter(user=u, role="leader", status="active").values_list("group_id", flat=True))
        counts = {}
        led_items = [a.id for a in items if a.group_id in led or u.is_staff_role]
        for row in (
            AssignmentSubmission.objects.filter(assignment_id__in=led_items)
            .values("assignment_id")
            .annotate(submitted=Count("id"), graded=Count("id", filter=Q(graded_at__isnull=False)))
        ):
            counts[row["assignment_id"]] = {"submitted": row["submitted"], "graded": row["graded"]}
        members = dict(
            GroupMember.objects.filter(group_id__in={a.group_id for a in items}, status="active", role="member")
            .values("group_id")
            .annotate(n=Count("id"))
            .values_list("group_id", "n")
        )
        return Response(
            [
                self._summary(
                    a,
                    a.id in led_items,
                    mine.get(a.id),
                    {**counts.get(a.id, {"submitted": 0, "graded": 0}), "members": members.get(a.group_id, 0)},
                )
                for a in items
            ]
        )

    def retrieve(self, request, pk=None):
        return Response(self._detail(self._assignment(pk)))

    def create(self, request):
        ser = AssignmentWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        if not services.is_leader(request.user, d["group"].id):
            raise PermissionDenied("Chỉ trưởng nhóm mới tạo được bài tập.")
        questions = d.pop("questions", [])
        with transaction.atomic():
            a = Assignment.objects.create(created_by=request.user, **d)
            _replace_questions(a, questions)
        return Response(self._detail(a), status=201)

    def partial_update(self, request, pk=None):
        a = self._assignment(pk, leader=True)
        ser = AssignmentWriteSerializer(a, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        d.pop("group", None)  # an assignment never moves to another group
        questions = d.pop("questions", None)
        if questions is not None and a.submissions.exists():
            return Response({"detail": "Đã có người nộp bài: không sửa câu hỏi được nữa", "errors": {}}, status=400)
        with transaction.atomic():
            for k, v in d.items():
                setattr(a, k, v)
            a.save()
            if questions is not None:
                _replace_questions(a, questions)
        return Response(self._detail(a))

    def destroy(self, request, pk=None):
        self._assignment(pk, leader=True).delete()
        return Response(status=204)

    @extend_schema(
        request={
            "multipart/form-data": {"type": "object", "properties": {"file": {"type": "string", "format": "binary"}}}
        }
    )
    @action(detail=True, methods=["post", "delete"])
    def attachment(self, request, pk=None):
        a = self._assignment(pk, leader=True)
        if request.method == "DELETE":
            a.attachment.delete(save=False)
            a.attachment_name = ""
            a.save(update_fields=["attachment", "attachment_name", "updated_at"])
            return Response(self._detail(a))
        f = request.FILES.get("file")
        if not f:
            return Response({"detail": "Chưa chọn file", "errors": {}}, status=400)
        try:
            services.check_file(f)
        except services.ClassworkError as e:
            return Response({"detail": str(e), "errors": {}}, status=400)
        a.attachment, a.attachment_name = f, f.name[:200]
        a.save(update_fields=["attachment", "attachment_name", "updated_at"])
        return Response(self._detail(a))

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        a = self._assignment(pk, leader=True)
        if a.status == Assignment.Status.PUBLISHED:
            return Response(self._detail(a))
        try:
            services.publish(a)
        except services.ClassworkError as e:
            return Response({"detail": str(e), "errors": {}}, status=400)
        return Response(self._detail(a))

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        a = self._assignment(pk, leader=True)
        a.status = Assignment.Status.CLOSED if a.status == Assignment.Status.PUBLISHED else a.status
        a.save(update_fields=["status", "updated_at"])
        return Response(self._detail(a))

    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        a = self._assignment(pk, leader=True)
        if a.status == Assignment.Status.CLOSED:
            a.status = Assignment.Status.PUBLISHED
            a.save(update_fields=["status", "updated_at"])
        return Response(self._detail(a))

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {"file": {"type": "string", "format": "binary"}, "group": {"type": "integer"}},
            }
        }
    )
    @action(detail=False, methods=["post"], url_path="import")
    def import_file(self, request):
        """An exercise file → draft questions (not saved) for the leader to check in the editor."""
        group = request.data.get("group")
        if not group or not services.is_leader(request.user, int(group)):
            raise PermissionDenied("Chỉ trưởng nhóm mới tạo được bài tập.")
        f = request.FILES.get("file")
        if not f:
            return Response({"detail": "Chưa chọn file", "errors": {}}, status=400)
        try:
            services.check_file(f)
            from .ai_import import read_questions

            return Response(read_questions(f))
        except services.ClassworkError as e:
            return Response({"detail": str(e), "errors": {}}, status=400)
        except AiUnavailable as e:
            return Response({"detail": str(e), "errors": {}}, status=503)

    # ---------------------------------------------------------------- doing and marking

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """JSON or multipart: answers = [{question, selected_option?, text?}] (a JSON string in multipart),
        text (no-question work), files: file (the whole work) and file_<question id> (a file question)."""
        a = self._assignment(pk)
        raw = request.data.get("answers") or []
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except ValueError:
                return Response({"detail": "Câu trả lời không hợp lệ", "errors": {}}, status=400)
        answers = {}
        for x in raw if isinstance(raw, list) else []:
            try:
                answers[int(x["question"])] = {
                    "selected_option": None if x.get("selected_option") in (None, "") else int(x["selected_option"]),
                    "text": x.get("text", ""),
                }
            except (KeyError, TypeError, ValueError):
                return Response({"detail": "Câu trả lời không hợp lệ", "errors": {}}, status=400)
        files = {}
        for key, f in request.FILES.items():
            if key == "file":
                files["main"] = f
            elif key.startswith("file_") and key[5:].isdigit():
                files[int(key[5:])] = f
        try:
            services.submit(request.user, a, answers, files, str(request.data.get("text", ""))[:20000])
        except services.ClassworkError as e:
            return Response({"detail": str(e), "errors": {}}, status=400)
        return Response(self._detail(a))

    @action(detail=True, methods=["get"])
    def submissions(self, request, pk=None):
        """Every member of the group with their work (or none yet), for the leader."""
        a = self._assignment(pk, leader=True)
        subs = {s.user_id: s for s in a.submissions.select_related("user__mascot")}
        rows = []
        for m in a.group.members.filter(status="active").exclude(role="leader").select_related("user__mascot"):
            s = subs.pop(m.user_id, None)
            rows.append({"user": author(request, m.user), "submission": self._sub_brief(s) if s else None})
        rows += [{"user": author(request, s.user), "submission": self._sub_brief(s)} for s in subs.values()]
        return Response(rows)

    @action(detail=True, methods=["get"], url_path=r"submissions/(?P<sid>\d+)")
    def submission(self, request, pk=None, sid=None):
        a = self._assignment(pk)
        s = get_object_or_404(a.submissions.prefetch_related("answers"), pk=sid)
        if s.user_id != request.user.id and not services.is_leader(request.user, a.group_id):
            raise PermissionDenied("Bạn không xem được bài này.")
        return Response(self._submission(s))

    @action(detail=True, methods=["post"], url_path=r"submissions/(?P<sid>\d+)/grade")
    def grade(self, request, pk=None, sid=None):
        """{answers: [{answer, score, feedback}], score (a work without questions), feedback}"""
        a = self._assignment(pk, leader=True)
        s = get_object_or_404(a.submissions, pk=sid)
        try:
            services.grade(
                request.user,
                s,
                request.data.get("answers") or [],
                request.data.get("score"),
                str(request.data.get("feedback") or ""),
            )
        except (services.ClassworkError, ValueError, ArithmeticError) as e:
            return Response({"detail": str(e) or "Điểm không hợp lệ", "errors": {}}, status=400)
        s.refresh_from_db()
        return Response(self._submission(s))

    @action(detail=False, methods=["get"])
    def gradebook(self, request):
        """?group=: the leader sees every member × every given assignment, a member only their own row."""
        group = request.query_params.get("group")
        if not group or not services.membership(request.user, int(group)) and not request.user.is_staff_role:
            raise PermissionDenied("Bạn không ở trong nhóm này.")
        leader = services.is_leader(request.user, int(group))
        items = list(
            Assignment.objects.filter(group_id=group)
            .exclude(status=Assignment.Status.DRAFT)
            .prefetch_related("questions")
            .order_by("published_at")
        )
        members = GroupMember.objects.filter(group_id=group, status="active").select_related("user__mascot")
        if not leader:
            members = members.filter(user=request.user)
        subs = {(s.assignment_id, s.user_id): s for s in AssignmentSubmission.objects.filter(assignment__in=items)}
        rows = []
        for m in members.exclude(role="leader") if leader else members:
            cells = [self._sub_brief(subs[(a.id, m.user_id)]) if (a.id, m.user_id) in subs else None for a in items]
            done = [c for c in cells if c and c["percent"] is not None]
            rows.append(
                {
                    "user": author(request, m.user),
                    "cells": cells,
                    "average": round(sum(c["percent"] for c in done) / len(done), 1) if done else None,
                }
            )
        return Response(
            {
                "assignments": [
                    {"id": a.id, "title": a.title, "due_at": a.due_at, "max_score": a.max_score} for a in items
                ],
                "rows": rows,
                "is_leader": leader,
            }
        )
