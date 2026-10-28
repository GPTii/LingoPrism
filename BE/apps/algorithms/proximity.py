"""Proximity Search with a self-implemented spatial index (uniform lat/lng grid) + exact Haversine distance.

Index:  every POI is put in the grid cell (⌊lat / Δ⌋, ⌊lng / Δ⌋), Δ = CELL_DEG (~1.1 km of latitude).
Query (lat, lng, r):
    1. the bounding box of the circle:  Δlat = r / 111 320 m,  Δlng = r / (111 320 m · cos lat)
    2. visit only the cells overlapping that box               → candidate POIs
    3. exact great-circle distance (Haversine) on candidates, keep d ≤ r, sort by d.
Cost: O(cells + candidates) instead of O(N) for a scan of all POIs.
Geofencing then checks d ≤ the POI's own radius.  The PostgreSQL cube/earthdistance query stays as baseline.
"""
import math
import threading
import time
from collections import defaultdict

EARTH_R = 6_371_008.8  # mean Earth radius (m), IUGG
M_PER_DEG_LAT = 111_320.0
CELL_DEG = 0.01


def haversine(lat1, lng1, lat2, lng2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_R * math.asin(min(1.0, math.sqrt(a)))


class GridIndex:
    def __init__(self, points, cell_deg: float = CELL_DEG):
        """points: iterable of (id, lat, lng)."""
        self.cell = cell_deg
        self.cells = defaultdict(list)
        self.size = 0
        for pid, lat, lng in points:
            self.cells[self._key(lat, lng)].append((pid, lat, lng))
            self.size += 1

    def _key(self, lat, lng):
        return math.floor(lat / self.cell), math.floor(lng / self.cell)

    def query(self, lat: float, lng: float, radius_m: float, limit: int | None = None) -> list[tuple[int, float]]:
        dlat = radius_m / M_PER_DEG_LAT
        dlng = radius_m / (M_PER_DEG_LAT * max(math.cos(math.radians(lat)), 1e-6))
        i0, j0 = self._key(lat - dlat, lng - dlng)
        i1, j1 = self._key(lat + dlat, lng + dlng)
        hits = []
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                for pid, plat, plng in self.cells.get((i, j), ()):
                    d = haversine(lat, lng, plat, plng)
                    if d <= radius_m:
                        hits.append((pid, d))
        hits.sort(key=lambda h: h[1])
        return hits[:limit] if limit else hits


def brute_force(points, lat, lng, radius_m) -> list[tuple[int, float]]:
    hits = [(pid, haversine(lat, lng, plat, plng)) for pid, plat, plng in points]
    return sorted([h for h in hits if h[1] <= radius_m], key=lambda h: h[1])


# ------------------------------------------------------------------ index of the active POIs (rebuilt on change)
# Each server process keeps its own index; a POI saved in one process bumps a version in the shared cache (Redis)
# so the other processes rebuild theirs on their next query too.

_lock = threading.Lock()
_index: GridIndex | None = None
_index_version = None
VERSION_KEY = "proximity:poi-index-version"


def poi_index() -> GridIndex:
    global _index, _index_version
    from django.core.cache import cache

    version = cache.get(VERSION_KEY)
    with _lock:
        if _index is None or version != _index_version:
            from apps.gis.models import Poi

            _index = GridIndex(Poi.objects.filter(is_active=True).values_list("id", "lat", "lng"))
            _index_version = version
        return _index


def invalidate(**kwargs):
    global _index
    from django.core.cache import cache

    with _lock:
        _index = None
    cache.set(VERSION_KEY, time.time_ns(), timeout=None)
