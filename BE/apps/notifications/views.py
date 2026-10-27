from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.bulk import BulkDeleteMixin
from apps.core.permissions import IsStaffRole

from .models import DeviceToken, Notification, NotificationSetting
from .services import notify


class NotificationSerializer(serializers.ModelSerializer):
    read = serializers.SerializerMethodField()
    action_state = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ["id", "kind", "title", "body", "image", "data", "read", "read_at", "action_state", "created_at"]

    def get_read(self, obj):
        return obj.read_at is not None

    def get_action_state(self, obj):
        """For a request answered right from the notification (friend / group): pending | accepted | gone, so the
        buttons show only while there is still something to answer."""
        action = (obj.data or {}).get("action")
        if action == "friend_request":
            from apps.community.models import FriendRequest

            fr = FriendRequest.objects.filter(pk=obj.data.get("request_id")).only("status").first()
            return fr.status if fr else "gone"
        if action == "group_request":
            from apps.community.models import GroupMember

            m = GroupMember.objects.filter(pk=obj.data.get("member_id")).only("status").first()
            return ("accepted" if m.status == "active" else "pending") if m else "gone"
        return None


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSetting
        fields = ["push_enabled", "morning_time", "evening_time", "contextual_allowed", "social_enabled"]


class DeviceSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)
    platform = serializers.ChoiceField(choices=["android", "ios", "web"])


class BroadcastSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=120)
    body = serializers.CharField(max_length=300, allow_blank=True, required=False)
    role = serializers.ChoiceField(choices=["all", "learner", "staff", "admin"], default="all")
    learner_type = serializers.ChoiceField(choices=["all", "kid", "adult"], default="all")


# ?group= on the list: the kinds a learner thinks of together
KIND_GROUPS = {
    "social": ["follow", "friend_request", "friend_accept", "group_request", "group", "comment", "like", "message"],
    "learning": ["reminder", "achievement", "league", "xp_milestone", "exam", "location"],
    "system": ["system", "broadcast"],
}


@extend_schema(tags=["notifications"])
class NotificationViewSet(BulkDeleteMixin, mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """The learner's notifications: ?kind=, ?group=social|learning|system, ?read=0|1, ?created_from/to; each one
    or many at once (bulk-delete) can be deleted."""

    serializer_class = NotificationSerializer
    filterset_fields = ["kind"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        qs = Notification.objects.filter(user=self.request.user)
        params = self.request.query_params
        if params.get("group") in KIND_GROUPS:
            qs = qs.filter(kind__in=KIND_GROUPS[params["group"]])
        if params.get("read") in ("0", "1"):
            qs = qs.filter(read_at__isnull=params["read"] == "0")
        return qs

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        return Response({"unread": self.get_queryset().filter(read_at__isnull=True).count()})

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        n = get_object_or_404(self.get_queryset(), pk=pk)
        n.read_at = n.read_at or timezone.now()
        n.save(update_fields=["read_at"])
        return Response(NotificationSerializer(n).data)

    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        updated = self.get_queryset().filter(read_at__isnull=True).update(read_at=timezone.now())
        return Response({"updated": updated})


@extend_schema(tags=["notifications"])
class NotificationSettingView(generics.RetrieveUpdateAPIView):
    serializer_class = SettingSerializer

    def get_object(self):
        obj, _ = NotificationSetting.objects.get_or_create(user=self.request.user)
        return obj


@extend_schema(tags=["notifications"])
class DeviceViewSet(viewsets.GenericViewSet):
    serializer_class = DeviceSerializer

    def create(self, request):
        ser = DeviceSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        DeviceToken.objects.update_or_create(
            token=ser.validated_data["token"],
            defaults={"user": request.user, "platform": ser.validated_data["platform"], "last_active_at": timezone.now()},
        )
        return Response({"registered": True}, status=201)

    @action(detail=False, methods=["post"])
    def unregister(self, request):
        DeviceToken.objects.filter(user=request.user, token=request.data.get("token", "")).delete()
        return Response({"unregistered": True})


@extend_schema(tags=["admin-notifications"])
class BroadcastView(generics.GenericAPIView):
    serializer_class = BroadcastSerializer
    permission_classes = [IsStaffRole]

    def post(self, request):
        ser = BroadcastSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        users = get_user_model().objects.filter(is_active=True)
        if d["role"] != "all":
            users = users.filter(role=d["role"])
        if d["learner_type"] != "all":
            users = users.filter(learner_type=d["learner_type"])
        count = 0
        for u in users.iterator():
            notify(u, Notification.Kind.BROADCAST, d["title"], d.get("body", ""))
            count += 1
        return Response({"sent": count})
