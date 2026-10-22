"""Proximity search with PostgreSQL cube + earthdistance (baseline for the self-implemented
Proximity Search of Phase 5). Uses the GiST index on ll_to_earth(lat, lng)."""
from datetime import timedelta

from django.db import connection
from django.utils import timezone

from .models import GeofenceEvent, Poi

MAX_RADIUS_M = 20000
GEOFENCE_COOLDOWN = timedelta(hours=6)


def method() -> str:
    from apps.algorithms.models import AlgorithmConfig

    return AlgorithmConfig.get().proximity


def nearby(lat: float, lng: float, radius_m: int, limit: int = 50, using: str | None = None) -> list[tuple[int, float]]:
    """[(poi_id, distance_m)] ordered by distance – self-implemented grid index (apps.algorithms.proximity)
    or the PostgreSQL earthdistance baseline, as chosen on the admin page."""
    radius_m = min(max(int(radius_m), 1), MAX_RADIUS_M)
    if (using or method()) == "grid":
        from apps.algorithms.proximity import poi_index

        return poi_index().query(lat, lng, radius_m, limit)
    sql = """
        SELECT id, earth_distance(ll_to_earth(%s, %s), ll_to_earth(lat, lng)) AS d
        FROM gis_poi
        WHERE is_active
          AND earth_box(ll_to_earth(%s, %s), %s) @> ll_to_earth(lat, lng)
          AND earth_distance(ll_to_earth(%s, %s), ll_to_earth(lat, lng)) <= %s
        ORDER BY d
        LIMIT %s
    """
    with connection.cursor() as cur:
        cur.execute(sql, [lat, lng, lat, lng, radius_m, lat, lng, radius_m, limit])
        return [(row[0], float(row[1])) for row in cur.fetchall()]


def containing(lat: float, lng: float) -> list[tuple[Poi, float]]:
    """POIs whose geofence (radius_m) contains the point."""
    candidates = nearby(lat, lng, 2000, limit=100)
    pois = {p.id: p for p in Poi.objects.filter(id__in=[c[0] for c in candidates]).prefetch_related("topics")}
    return [(pois[pid], d) for pid, d in candidates if pid in pois and d <= pois[pid].radius_m]


def check_geofence(user, lat: float, lng: float) -> list[dict]:
    from apps.notifications.models import Notification, NotificationSetting
    from apps.notifications.services import notify

    entered = []
    setting = NotificationSetting.objects.filter(user=user).first()
    allow_notify = setting.contextual_allowed if setting else True
    since = timezone.now() - GEOFENCE_COOLDOWN
    for poi, distance in containing(lat, lng):
        recent = GeofenceEvent.objects.filter(user=user, poi=poi, created_at__gte=since).exists()
        GeofenceEvent.objects.create(user=user, poi=poi, lat=lat, lng=lng, distance_m=distance)
        topics = list(poi.topics.all())
        info = {"poi": poi.id, "name": poi.name, "category": poi.category, "distance_m": round(distance, 1),
                "topics": [{"id": t.id, "name_vi": t.name_vi, "icon": t.icon} for t in topics], "new": not recent}
        entered.append(info)
        if not recent and allow_notify and topics:
            notify(user, Notification.Kind.LOCATION, f"Bạn đang ở gần {poi.name} 📍",
                   f"Học ngay chủ đề {topics[0].name_vi.lower()} phù hợp với nơi này!",
                   data={"route": f"/vocab/topics/{topics[0].id}", "poi": poi.id, "topic": topics[0].id})
    return entered
