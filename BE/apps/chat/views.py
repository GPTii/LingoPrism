from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.throttles import ActionThrottleMixin
from apps.gamification.mascot import look

from . import services
from .models import DirectThread, GroupMessage, SupportConversation


class SendGroupMessageSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=GroupMessage.Kind.choices, default="text")
    content = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    sticker = serializers.CharField(required=False, allow_blank=True, max_length=40)
    badge = serializers.CharField(required=False, allow_blank=True, max_length=50)
    client_id = serializers.CharField(required=False, allow_blank=True, max_length=40)


class GroupMessagesView(APIView):
    """History (paginated by ?before=<id>) and REST fallback for sending when the socket is down."""

    @extend_schema(tags=["chat"], parameters=[OpenApiParameter("before", int)], responses={200: dict})
    def get(self, request, group_id):
        if not services.is_active_member(request.user, group_id):
            return Response({"detail": "Bạn chưa tham gia nhóm này", "errors": {}}, status=403)
        qs = GroupMessage.objects.filter(group_id=group_id).select_related("user", "badge").order_by("-id")
        if request.query_params.get("before"):
            qs = qs.filter(id__lt=int(request.query_params["before"]))
        msgs = list(qs[:50])[::-1]
        return Response({"results": [services.group_message_payload(m) for m in msgs], "has_more": len(msgs) == 50})

    @extend_schema(tags=["chat"], request=SendGroupMessageSerializer, responses={201: dict})
    def post(self, request, group_id):
        ser = SendGroupMessageSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        try:
            m = services.send_group_message(request.user, group_id, d["kind"], d.get("content", ""), d.get("sticker", ""),
                                            d.get("badge", ""), d.get("client_id", ""))
        except services.ChatError as e:
            return Response({"detail": str(e), "errors": {}}, status=400)
        return Response(services.group_message_payload(m), status=201)


class ConversationSerializer(serializers.ModelSerializer):
    learner = serializers.SerializerMethodField()
    staff_name = serializers.CharField(source="staff.display_name", default=None, read_only=True)
    unread = serializers.IntegerField(read_only=True, default=0)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = SupportConversation
        fields = ["id", "subject", "status", "learner", "staff", "staff_name", "unread", "last_message",
                  "created_at", "last_message_at"]
        read_only_fields = ["id", "status", "learner", "staff", "staff_name", "created_at", "last_message_at"]

    def get_learner(self, obj):
        return {"id": obj.learner_id, "display_name": obj.learner.display_name, "email": obj.learner.email}

    def get_last_message(self, obj):
        m = obj.messages.order_by("-id").first()
        return services.support_message_payload(m) if m else None


class SendSupportSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=2000)
    client_id = serializers.CharField(required=False, allow_blank=True, max_length=40)


@extend_schema(tags=["chat"])
class SupportConversationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                                 viewsets.GenericViewSet):
    """Learners see their own conversations; staff see all (support inbox)."""

    serializer_class = ConversationSerializer
    filterset_fields = ["status"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return SupportConversation.objects.none()
        user = self.request.user
        qs = SupportConversation.objects.select_related("learner", "staff").annotate(
            unread=Count("messages", filter=Q(messages__read_at__isnull=True) & ~Q(messages__sender=user)))
        qs = qs.order_by("-last_message_at")
        return qs if user.is_staff_role else qs.filter(learner=user)

    def create(self, request, *args, **kwargs):
        conv = SupportConversation.objects.filter(learner=request.user, status="open").first()
        if conv is None:
            conv = SupportConversation.objects.create(learner=request.user, subject=request.data.get("subject") or "Hỗ trợ học tập")
        if request.data.get("content"):
            services.send_support_message(request.user, conv, request.data["content"])
        return Response(ConversationSerializer(self.get_queryset().get(pk=conv.pk)).data, status=201)

    @extend_schema(request=SendSupportSerializer, responses={200: dict})
    @action(detail=True, methods=["get", "post"])
    def messages(self, request, pk=None):
        conv = self.get_object()
        if request.method == "GET":
            msgs = conv.messages.select_related("sender").order_by("id")
            services.mark_support_read(request.user, conv)
            return Response([services.support_message_payload(m) for m in msgs])
        ser = SendSupportSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            m = services.send_support_message(request.user, conv, ser.validated_data["content"], ser.validated_data.get("client_id", ""))
        except services.ChatError as e:
            return Response({"detail": str(e), "errors": {}}, status=400)
        return Response(services.support_message_payload(m), status=201)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        conv = get_object_or_404(self.get_queryset(), pk=pk)
        conv.status = SupportConversation.Status.CLOSED
        conv.save(update_fields=["status"])
        return Response({"status": conv.status})


# ------------------------------------------------------------------ private messages

def _person(request, user):
    return {"id": user.id, "display_name": user.display_name, "avatar": user.avatar_url(request), "mascot": look(user)}


class SendDirectSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    sticker = serializers.CharField(required=False, allow_blank=True, max_length=40)
    client_id = serializers.CharField(required=False, allow_blank=True, max_length=40)


class OpenThreadSerializer(serializers.Serializer):
    user = serializers.IntegerField()


@extend_schema(tags=["chat"])
class DirectThreadViewSet(ActionThrottleMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Private messages between two learners who follow each other (see services.can_message)."""

    serializer_class = serializers.Serializer
    pagination_class = None
    throttle_scopes = {"messages": "message"}

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return DirectThread.objects.none()
        user = self.request.user
        return (DirectThread.objects.filter(Q(user_a=user) | Q(user_b=user)).select_related("user_a", "user_b")
                .annotate(unread=Count("messages", filter=Q(messages__read_at__isnull=True) & ~Q(messages__sender=user)))
                .order_by("-last_message_at"))

    def _row(self, t):
        other = t.other(self.request.user)
        last = t.messages.order_by("-id").first()
        return {"id": t.id, "other": _person(self.request, other), "unread": getattr(t, "unread", 0),
                "can_message": services.can_message(self.request.user, other),
                "last_message": services.direct_message_payload(last) if last else None,
                "last_message_at": t.last_message_at.isoformat()}

    def list(self, request):
        return Response([self._row(t) for t in self.get_queryset() if t.messages.exists()])

    def retrieve(self, request, pk=None):
        return Response(self._row(self.get_object()))

    @extend_schema(request=OpenThreadSerializer, responses={201: dict})
    def create(self, request):
        from apps.accounts.models import User

        ser = OpenThreadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        other = User.objects.filter(pk=ser.validated_data["user"]).first()
        if not services.can_message(request.user, other):
            return Response({"detail": "Hai bạn cần theo dõi nhau mới nhắn tin được.", "errors": {}}, status=400)
        thread = services.thread_with(request.user, other)
        return Response(self._row(self.get_queryset().get(pk=thread.pk)), status=201)

    @extend_schema(request=SendDirectSerializer, responses={200: dict},
                   parameters=[OpenApiParameter("before", int, description="older than this message id")])
    @action(detail=True, methods=["get", "post"])
    def messages(self, request, pk=None):
        thread = self.get_object()
        if request.method == "GET":
            qs = thread.messages.order_by("-id")
            if request.query_params.get("before"):
                qs = qs.filter(id__lt=int(request.query_params["before"]))
            msgs = list(qs[:50])[::-1]
            services.mark_direct_read(request.user, thread)
            return Response({"results": [services.direct_message_payload(m) for m in msgs], "has_more": len(msgs) == 50})
        ser = SendDirectSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            d = ser.validated_data
            m = services.send_direct_message(request.user, thread, d.get("content", ""), d.get("client_id", ""),
                                             d.get("sticker", ""))
        except services.ChatError as e:
            return Response({"detail": str(e), "errors": {}}, status=400)
        return Response(services.direct_message_payload(m), status=201)

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        return Response({"read": services.mark_direct_read(request.user, self.get_object())})
