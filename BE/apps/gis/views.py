import time

from django.db.models import Count
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsStaffRole

from . import services
from .models import Poi


class PoiSerializer(serializers.ModelSerializer):
    topics_detail = serializers.SerializerMethodField()
    distance_m = serializers.FloatField(read_only=True, required=False)
    category_label = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Poi
        fields = ["id", "name", "category", "category_label", "lat", "lng", "radius_m", "address", "description",
                  "topics", "topics_detail", "is_active", "distance_m"]

    def get_topics_detail(self, obj):
        return [{"id": t.id, "slug": t.slug, "name_vi": t.name_vi, "icon": t.icon} for t in obj.topics.all()]

    def validate(self, attrs):
        lat, lng = attrs.get("lat"), attrs.get("lng")
        if lat is not None and not -90 <= lat <= 90 or lng is not None and not -180 <= lng <= 180:
            raise serializers.ValidationError("Toạ độ không hợp lệ")
        return attrs


class PointSerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lng = serializers.FloatField(min_value=-180, max_value=180)


class NearbyView(APIView):
    @extend_schema(tags=["gis"], parameters=[
        OpenApiParameter("lat", float, required=True), OpenApiParameter("lng", float, required=True),
        OpenApiParameter("radius", int, description="mét (mặc định 1000, tối đa 20000)")], responses={200: dict})
    def get(self, request):
        ser = PointSerializer(data=request.query_params)
        ser.is_valid(raise_exception=True)
        radius = int(request.query_params.get("radius", 1000))
        start = time.perf_counter()
        hits = services.nearby(ser.validated_data["lat"], ser.validated_data["lng"], radius)
        query_ms = round((time.perf_counter() - start) * 1000, 2)
        pois = {p.id: p for p in Poi.objects.filter(id__in=[h[0] for h in hits]).prefetch_related("topics")}
        results = []
        for pid, d in hits:
            p = pois[pid]
            p.distance_m = round(d, 1)
            results.append(PoiSerializer(p).data)
        return Response({"radius_m": radius, "query_ms": query_ms, "method": services.method(), "results": results})


class GeofenceCheckView(APIView):
    @extend_schema(tags=["gis"], request=PointSerializer, responses={200: dict})
    def post(self, request):
        ser = PointSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        return Response({"entered": services.check_geofence(request.user, ser.validated_data["lat"], ser.validated_data["lng"])})


@extend_schema(tags=["gis"])
class PoiViewSet(viewsets.ModelViewSet):
    """Everyone can read POIs (map); only staff can edit them (WebGIS admin)."""

    serializer_class = PoiSerializer
    filterset_fields = ["category", "is_active"]
    search_fields = ["name", "address"]
    pagination_class = None

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return super().get_permissions()
        return [IsStaffRole()]

    def get_queryset(self):
        qs = Poi.objects.prefetch_related("topics")
        if not getattr(self.request.user, "is_staff_role", False):
            qs = qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[IsStaffRole])
    def stats(self, request):
        rows = Poi.objects.annotate(visits=Count("events")).order_by("-visits").values("id", "name", "category", "visits")[:20]
        return Response(list(rows))
