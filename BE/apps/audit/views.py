from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, serializers, viewsets

from apps.core.permissions import IsAdminRole

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ["id", "actor", "actor_email", "actor_role", "method", "path", "resource", "object_id",
                  "status_code", "fields", "ip", "created_at"]


@extend_schema(tags=["admin"], parameters=[
    OpenApiParameter("q", str, description="Tìm theo email hoặc đường dẫn"),
    OpenApiParameter("method", str), OpenApiParameter("resource", str),
])
class AuditLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Nhật ký thao tác của admin / staff – chỉ admin xem được."""

    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        qs = AuditLog.objects.all()
        p = self.request.query_params
        if p.get("q"):
            qs = qs.filter(Q(actor_email__icontains=p["q"]) | Q(path__icontains=p["q"]))
        if p.get("method"):
            qs = qs.filter(method=p["method"].upper())
        if p.get("resource"):
            qs = qs.filter(resource=p["resource"])
        return qs
