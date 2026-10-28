from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.bulk import BulkDeleteMixin
from apps.vocab.models import Topic, Word
from apps.vocab.services import LEARN_LANGUAGES, card, resolve_target, words_for_target
from apps.vocab.views import LANG_PARAMS

from .levels import advance_if_done, current_level as level_current
from .models import PersonalWord, ReviewLog, SessionItem, StudySession
from .questions import build_questions, get_distractor_provider
from .scheduling import get_scheduler

MAX_SESSION = 30


class AddWordSerializer(serializers.Serializer):
    word = serializers.PrimaryKeyRelatedField(queryset=Word.objects.all())
    source = serializers.ChoiceField(choices=PersonalWord.Source.choices, default=PersonalWord.Source.MANUAL)
    topic = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all(), required=False, allow_null=True)
    source_ref = serializers.CharField(required=False, allow_blank=True, max_length=64)


class StartSessionSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=StudySession.Kind.choices)
    topic = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all(), required=False, allow_null=True)
    size = serializers.IntegerField(min_value=1, max_value=MAX_SESSION, required=False, allow_null=True)
    word_ids = serializers.ListField(child=serializers.IntegerField(), required=False, max_length=MAX_SESSION,
                                     help_text="Luyện lại đúng những từ này (VD từ chơi sai trong mục Trò chơi)")


class AnswerSerializer(serializers.Serializer):
    personal_word = serializers.IntegerField()
    question_type = serializers.CharField(max_length=30)
    correct = serializers.BooleanField()
    first_try = serializers.BooleanField(default=True)
    graded = serializers.BooleanField(default=False, help_text="Câu dùng để cập nhật lịch ôn (vòng kiểm tra cuối)")
    rating = serializers.IntegerField(min_value=0, max_value=5, required=False)
    response_ms = serializers.IntegerField(min_value=0, required=False)
    answer = serializers.CharField(max_length=200, required=False, allow_blank=True)


@extend_schema(tags=["learning"], parameters=LANG_PARAMS)
class MyWordViewSet(BulkDeleteMixin, mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """The learner's library (thư viện từ cá nhân): ?status=, ?source=, ?topic=, ?created_from/to (day saved)."""

    serializer_class = AddWordSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return PersonalWord.objects.none()
        target = resolve_target(self.request)
        qs = PersonalWord.objects.filter(user=self.request.user, language=target.learn)
        params = self.request.query_params
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("source"):
            qs = qs.filter(source=params["source"])
        if params.get("topic"):
            qs = qs.filter(Q(topic_id=params["topic"]) | Q(word__topics__id=params["topic"])).distinct()
        return qs.order_by("-created_at")

    def _cards(self, personal_words):
        target = resolve_target(self.request)
        words = {w.id: w for w in words_for_target(
            Word.objects.filter(id__in=[p.word_id for p in personal_words]), self.request.user, target)}
        return [card(words[p.word_id], target, p, self.request) for p in personal_words if p.word_id in words]

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        return self.get_paginated_response(self._cards(page))

    @extend_schema(request=AddWordSerializer)
    def create(self, request):
        ser = AddWordSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        target = resolve_target(request)
        word = ser.validated_data["word"]
        if not words_for_target(Word.objects.filter(id=word.id), request.user, target).exists():
            return Response({"detail": "Từ này chưa có bản dịch đã kiểm tra cho ngôn ngữ đang học", "errors": {}}, status=400)
        pw, created = PersonalWord.objects.get_or_create(
            user=request.user, word=word, language=target.learn,
            defaults={
                "source": ser.validated_data["source"], "topic": ser.validated_data.get("topic"),
                "source_ref": ser.validated_data.get("source_ref", ""),
            },
        )
        return Response(self._cards([pw])[0], status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def due(self, request):
        qs = self.get_queryset().filter(due_at__lte=timezone.now()).order_by("due_at")
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(self._cards(page))

    @action(detail=False, methods=["get"])
    def summary(self, request):
        target = resolve_target(request)
        qs = PersonalWord.objects.filter(user=request.user, language=target.learn)
        counts = dict(qs.values_list("status").annotate(n=Count("id")))
        return Response({
            "language": target.learn,
            "total": sum(counts.values()),
            "new": counts.get("new", 0),
            "learning": counts.get("learning", 0),
            "mastered": counts.get("mastered", 0),
            "due": qs.filter(due_at__lte=timezone.now()).count(),
        })


@extend_schema(tags=["learning"], parameters=LANG_PARAMS)
class StudySessionViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return StudySession.objects.none()
        return StudySession.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        return StartSessionSerializer

    def _pick(self, kind, target, topic, size, word_ids=None):
        user = self.request.user
        mine = PersonalWord.objects.filter(user=user, language=target.learn)
        if word_ids:  # only words already in the learner's library
            return list(mine.filter(word_id__in=word_ids).select_related("word")[:size])
        if kind == StudySession.Kind.REVIEW:
            due = mine.filter(due_at__lte=timezone.now()).select_related("word")
            from apps.algorithms.models import AlgorithmConfig

            cfg = AlgorithmConfig.get()
            if cfg.review_priority == AlgorithmConfig.Priority.VIP:
                from apps.algorithms.vip import rank

                return [pw for pw, _, _ in rank(list(due), cfg.vip_weights or None)[:size]]
            return list(due.order_by("due_at")[:size])
        if kind == StudySession.Kind.PRACTICE:
            if topic is None:
                return list(mine.exclude(status=PersonalWord.Status.NEW).order_by("?")[:size])
            words = words_for_target(Word.objects.filter(topics=topic), user, target)
            return [
                PersonalWord.objects.get_or_create(user=user, word=w, language=target.learn,
                                                   defaults={"source": PersonalWord.Source.TOPIC, "topic": topic})[0]
                for w in list(words.order_by("?")[:size])
            ]
        # LEARN: new words already in the library first, then fill from verified vocabulary
        picked = list(mine.filter(status=PersonalWord.Status.NEW).order_by("created_at")[:size])
        if len(picked) < size:
            base = Word.objects.filter(topics=topic) if topic else Word.objects.all()
            if user.learner_type == "kid":
                base = base.filter(audience__in=["all", "kid"])
            base = base.exclude(learners__user=user, learners__language=target.learn)
            # the learner's level first, then what is left of the easier levels; never above the current level
            cur = level_current(user, target)
            fresh = []
            for n in [cur] + list(range(cur - 1, 0, -1)):
                need = size - len(picked) - len(fresh)
                if need <= 0:
                    break
                fresh += list(words_for_target(base.filter(**{f"levels__{target.learn}": n}), user, target)
                              .order_by("difficulty", "?")[:need])
            for w in fresh:
                picked.append(PersonalWord.objects.create(
                    user=user, word=w, language=target.learn, source=PersonalWord.Source.TOPIC, topic=topic))
        return picked

    def _payload(self, session):
        target = resolve_target(self.request)
        items = list(session.items.select_related("personal_word"))
        words = {w.id: w for w in words_for_target(
            Word.objects.filter(id__in=[i.personal_word.word_id for i in items]).prefetch_related("topics"),
            self.request.user, target)}
        provider = get_distractor_provider()
        out = []
        for item in items:
            pw = item.personal_word
            w = words.get(pw.word_id)
            if w is None:
                continue
            by_lang = {t.language_id: t for t in w.visible_translations}
            out.append({
                "item_id": item.id, "personal_word": pw.id, "answered": item.answered,
                "card": card(w, target, pw, self.request),
                "questions": build_questions(w, target, by_lang, provider),
            })
        return {
            "id": session.id, "kind": session.kind, "language": session.language, "script": session.script,
            "planned_count": session.planned_count, "completed_count": session.completed_count,
            "started_at": session.started_at, "ended_at": session.ended_at, "items": out,
        }

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        return self.get_paginated_response([
            {"id": s.id, "kind": s.kind, "language": s.language, "planned_count": s.planned_count,
             "completed_count": s.completed_count, "correct_first_try": s.correct_first_try,
             "xp_earned": s.xp_earned, "started_at": s.started_at, "ended_at": s.ended_at}
            for s in page
        ])

    def retrieve(self, request, *args, **kwargs):
        return Response(self._payload(self.get_object()))

    @extend_schema(request=StartSessionSerializer)
    def create(self, request):
        ser = StartSessionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        target = resolve_target(request)
        if target.learn not in LEARN_LANGUAGES:
            return Response({"detail": "Ngôn ngữ không hỗ trợ", "errors": {}}, status=400)
        kind = ser.validated_data["kind"]
        goal = getattr(request.user, "goal", None)
        default_size = (goal.daily_review_target if kind == "review" else goal.daily_new_target) if goal else 10
        size = min(ser.validated_data.get("size") or default_size, MAX_SESSION)
        topic = ser.validated_data.get("topic")
        with transaction.atomic():
            word_ids = ser.validated_data.get("word_ids")
            if word_ids:
                kind, size = StudySession.Kind.PRACTICE, min(len(word_ids), MAX_SESSION)
            picked = self._pick(kind, target, topic, size, word_ids)
            if not picked:
                msg = "Chưa có từ nào đến hạn ôn tập" if kind == "review" else "Không có từ nào để học"
                return Response({"detail": msg, "errors": {}}, status=400)
            session = StudySession.objects.create(
                user=request.user, language=target.learn, script=target.script, kind=kind, topic=topic,
                scheduler=get_scheduler().name, planned_count=len(picked),
            )
            SessionItem.objects.bulk_create(
                [SessionItem(session=session, personal_word=pw, order=i) for i, pw in enumerate(picked)]
            )
        return Response(self._payload(session), status=status.HTTP_201_CREATED)

    @extend_schema(request=AnswerSerializer)
    @action(detail=True, methods=["post"])
    def answer(self, request, pk=None):
        session = self.get_object()
        if session.ended_at:
            return Response({"detail": "Phiên học đã kết thúc", "errors": {}}, status=400)
        ser = AnswerSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        item = get_object_or_404(SessionItem, session=session, personal_word_id=d["personal_word"])
        pw = item.personal_word
        now = timezone.now()
        before = pw.state
        elapsed = (now - pw.last_reviewed_at).total_seconds() / 86400 if pw.last_reviewed_at else None
        rating = d.get("rating", 4 if d["correct"] and d["first_try"] else (3 if d["correct"] else 1))
        after = before
        with transaction.atomic():
            if d["graded"] and not item.answered:
                scheduler = get_scheduler(session.scheduler)
                after, due = scheduler.review(before, d["correct"] and d["first_try"], rating, now, elapsed_days=elapsed)
                pw.apply_state(after, due)
                pw.save()
                item.answered = True
                item.save(update_fields=["answered"])
                session.completed_count += 1
                session.correct_first_try += int(d["correct"] and d["first_try"])
                session.save(update_fields=["completed_count", "correct_first_try", "updated_at"])
            ReviewLog.objects.create(
                user=request.user, personal_word=pw, session=session, language=session.language,
                script=session.script, question_type=d["question_type"], correct=d["correct"],
                first_try=d["first_try"], rating=rating, response_ms=d.get("response_ms"),
                answer=d.get("answer", ""), scheduler=session.scheduler,
                state_before=before.as_dict(), state_after=after.as_dict(), elapsed_days=elapsed,
            )
        return Response({
            "personal_word": pw.id, "status": pw.status, "stage": pw.stage, "due_at": pw.due_at,
            "completed_count": session.completed_count,
        })

    @action(detail=True, methods=["post"])
    def finish(self, request, pk=None):
        session = self.get_object()
        if not session.ended_at:
            session.ended_at = timezone.now()
            session.xp_earned = 5 * session.completed_count + 5 * session.correct_first_try
            session.save(update_fields=["ended_at", "xp_earned", "updated_at"])
            from apps.learning.signals import session_finished

            session_finished.send(sender=StudySession, session=session)
        level_up = advance_if_done(request.user, resolve_target(request)) if session.kind == "learn" else None
        wrong = SessionItem.objects.filter(session=session, personal_word__logs__session=session,
                                           personal_word__logs__correct=False).values_list("personal_word_id", flat=True)
        return Response({
            "id": session.id, "planned_count": session.planned_count, "completed_count": session.completed_count,
            "correct_first_try": session.correct_first_try, "xp_earned": session.xp_earned,
            "needs_more_practice": sorted(set(wrong)), "level_up": level_up,
        })
