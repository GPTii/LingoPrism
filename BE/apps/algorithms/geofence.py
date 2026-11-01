"""Geofence trigger delay (thesis outline §4.5: "độ trễ kích hoạt geofence"), measured by simulation on the real POIs.

A learner passes a POI in a straight line (walking, cycling or on a motorbike), the phone gets a GPS fix every second
with noise, and the app applies its check policy exactly as location_service.dart does:
    the position stream only emits after moving `distance_filter` metres (Geolocator distanceFilter),
    and an emitted position is sent to /geofence/check/ only if the last check is older than `min_interval` seconds.
The server side is the same test as services.containing(): grid index (proximity.py) + Haversine, d ≤ the POI radius.

    delay      = time of the first check that finds the POI − time the learner really entered its circle
    detected   = share of passes in which the POI is found at all before the learner leaves the circle + 30 s
    false      = passes that stay 10–50 % outside the circle but are "found" because of GPS noise
    checks/h   = requests per hour of moving (server load, battery)

The app's old policy (the baseline) is compared with denser ones; the server's own share (one containing() call) is timed separately.
Network time of a real phone is not included.
"""
import math
import random
import statistics
import time

from .proximity import GridIndex, haversine

M_PER_DEG = 111_320.0
GPS_SIGMA_M = 8.0  # LocationAccuracy.high outdoors
SPEEDS = {"đi bộ": 1.4, "xe đạp": 4.5, "xe máy": 8.0}  # m/s
POLICIES = {  # name: (distance_filter m, min_interval s)
    "cũ: 100 m / 2 phút": (100, 120),
    "25 m / 30 giây": (25, 30),
    "đang dùng: 25 m / 15 giây": (25, 15),
    "10 m / 10 giây": (10, 10),
}
BASELINE = "cũ: 100 m / 2 phút"  # what the app did before this experiment
CURRENT = "đang dùng: 25 m / 15 giây"  # location_service.dart since 1.8.0: every pass detected at every speed
GRACE_S = 30  # a POI found up to 30 s after leaving its circle still counts (the learner is just past it)


def _offset(lat, lng, east_m, north_m):
    return lat + north_m / M_PER_DEG, lng + east_m / (M_PER_DEG * math.cos(math.radians(lat)))


def _pass(rng, poi, speed, inside: bool):
    """One straight pass: (true points per second, noisy fixes, entry time or None, exit time)."""
    _, lat, lng, radius = poi
    heading = rng.uniform(0, 2 * math.pi)
    # distance of the path from the centre: inside → crosses the circle, outside → 10–50 % beyond it
    b = rng.uniform(0, 0.9) * radius if inside else rng.uniform(1.1, 1.5) * radius
    lead = 600 + radius
    ux, uy = math.cos(heading), math.sin(heading)
    px, py = -uy * b, ux * b  # perpendicular offset
    n = int(2 * lead / speed)
    true_pts, fixes, entry, exit_ = [], [], None, None
    for t in range(n + 1):
        along = -lead + t * speed
        e, nth = px + ux * along, py + uy * along
        d = math.hypot(e, nth)
        if d <= radius and entry is None:
            entry = t
        if entry is not None and exit_ is None and d > radius:
            exit_ = t
        true_pts.append(_offset(lat, lng, e, nth))
        fixes.append(_offset(lat, lng, e + rng.gauss(0, GPS_SIGMA_M), nth + rng.gauss(0, GPS_SIGMA_M)))
    return fixes, entry, exit_ if exit_ is not None else n


def _run_policy(fixes, poi_id, radius_of, index, distance_filter, min_interval, rng):
    """Seconds at which the app checks, and the first second a check finds `poi_id`."""
    last_emit = fixes[0]
    last_check = -rng.uniform(0, min_interval)  # the app has been running for a while
    checks, found = [], None
    for t, (lat, lng) in enumerate(fixes):
        if t and haversine(last_emit[0], last_emit[1], lat, lng) < distance_filter:
            continue
        last_emit = (lat, lng)
        if t - last_check <= min_interval:
            continue
        last_check = t
        checks.append(t)
        if found is None and any(pid == poi_id and d <= radius_of[pid] for pid, d in index.query(lat, lng, 2000)):
            found = t
    return checks, found


def simulate(pois, passes=120, seed=0) -> dict:
    """pois: [(id, lat, lng, radius_m)]."""
    rng = random.Random(seed)
    index = GridIndex([(p[0], p[1], p[2]) for p in pois])
    radius_of = {p[0]: p[3] for p in pois}
    rows = []
    for policy, (dist_f, interval) in POLICIES.items():
        for mode, speed in SPEEDS.items():
            delays, detected, false_hits, checks, seconds = [], 0, 0, 0, 0
            for k in range(passes):
                poi = rng.choice(pois)
                inside = k % 4 != 3  # one pass in four goes by just outside the circle
                fixes, entry, exit_ = _pass(rng, poi, speed, inside)
                times, found = _run_policy(fixes, poi[0], radius_of, index, dist_f, interval, rng)
                checks += len(times)
                seconds += len(fixes)
                if not inside:
                    false_hits += found is not None
                elif found is not None and found <= exit_ + GRACE_S:
                    detected += 1
                    delays.append(max(0, found - entry))
            n_in = sum(1 for k in range(passes) if k % 4 != 3)
            rows.append({
                "policy": policy, "mode": mode, "speed_ms": speed, "passes": n_in,
                "detected_rate": round(detected / n_in, 3),
                "delay_mean_s": round(statistics.mean(delays), 1) if delays else None,
                "delay_p50_s": round(statistics.median(delays), 1) if delays else None,
                "delay_p95_s": round(sorted(delays)[int(0.95 * (len(delays) - 1))], 1) if delays else None,
                "false_rate": round(false_hits / (passes - n_in), 3),
                "checks_per_hour": round(checks / seconds * 3600, 1),
            })
    return {"rows": rows, "policies": {k: {"distance_filter_m": v[0], "min_interval_s": v[1]} for k, v in POLICIES.items()},
            "baseline": BASELINE, "current": CURRENT, "speeds_ms": SPEEDS, "gps_sigma_m": GPS_SIGMA_M, "passes_per_cell": passes,
            "grace_s": GRACE_S}


def server_check_ms(pois, queries=300, seed=1) -> dict:
    """Time of the server's geofence test (services.containing: index + database) at points near the POIs."""
    from apps.gis.services import containing

    rng = random.Random(seed)
    pts = []
    for _ in range(queries):
        _, lat, lng, radius = rng.choice(pois)
        pts.append(_offset(lat, lng, rng.uniform(-1.5, 1.5) * radius, rng.uniform(-1.5, 1.5) * radius))
    containing(*pts[0])  # warm the index
    ms = []
    for lat, lng in pts:
        s = time.perf_counter()
        containing(lat, lng)
        ms.append((time.perf_counter() - s) * 1000)
    ms.sort()
    return {"queries": queries, "mean_ms": round(statistics.mean(ms), 3), "p95_ms": round(ms[int(0.95 * (len(ms) - 1))], 3),
            "max_ms": round(ms[-1], 3)}
