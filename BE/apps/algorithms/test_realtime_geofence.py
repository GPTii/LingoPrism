"""The two measurements of thesis §4.5 that are not algorithms of their own: geofence trigger delay and realtime."""

import pytest

from . import geofence, realtime


def test_denser_geofence_checks_find_fast_passes_the_old_policy_misses():
    # four POIs of 150 m around Hồ Gươm, like the seeded ones
    pois = [
        (1, 21.0288, 105.8525, 150),
        (2, 21.0245, 105.8412, 150),
        (3, 21.0368, 105.8342, 200),
        (4, 21.0170, 105.8500, 100),
    ]
    rows = {(r["policy"], r["mode"]): r for r in geofence.simulate(pois, passes=60, seed=3)["rows"]}
    old, new = rows[(geofence.BASELINE, "xe máy")], rows[(geofence.CURRENT, "xe máy")]
    assert old["detected_rate"] < 0.5 and new["detected_rate"] >= 0.9
    # delays are averaged over the passes that were found, so compare them walking, where both find nearly all
    assert rows[(geofence.CURRENT, "đi bộ")]["delay_mean_s"] < rows[(geofence.BASELINE, "đi bộ")]["delay_mean_s"] / 3
    assert all(r["delay_p50_s"] is None or r["delay_p50_s"] >= 0 for r in rows.values())
    assert rows[(geofence.CURRENT, "đi bộ")]["checks_per_hour"] > rows[(geofence.BASELINE, "đi bộ")]["checks_per_hour"]


@pytest.mark.django_db(transaction=True)  # the consumers reach the database from another thread
def test_realtime_measurement_delivers_everything_once_in_order_and_cleans_up():
    from apps.accounts.models import User

    out = realtime.run()
    g = out["group"]
    assert g["deliveries"] == g["deliveries_expected"] == realtime.GROUP_MEMBERS**2 * realtime.PER_MEMBER
    assert g["missing"] == g["duplicates"] == 0 and g["same_order_everywhere"] and not g["resend_creates_new"]
    assert out["dm"]["to_recipient"]["received"] == realtime.DMS and out["dm"]["to_recipient"]["in_order"]
    assert out["flood"]["accepted"] == out["flood"]["burst_allowed"] and out["flood"]["refused"] > 0
    assert out["ping"]["n"] == realtime.PINGS and g["to_other_members"]["p95_ms"] > 0
    assert not User.objects.filter(email__endswith="@bench.invalid").exists()
