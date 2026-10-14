import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.gis.models import Poi
from apps.vocab.models import Topic

pytestmark = pytest.mark.django_db


@pytest.fixture
def pois(db):
    topic = Topic.objects.create(slug="food", name_vi="Thực phẩm")
    market = Poi.objects.create(name="Chợ Bến Thành", category="market", lat=10.7725, lng=106.6980, radius_m=150)
    market.topics.add(topic)
    Poi.objects.create(name="Dinh Độc Lập", category="landmark", lat=10.7770, lng=106.6953, radius_m=200)
    Poi.objects.create(name="Sân bay", category="airport", lat=10.8185, lng=106.6588, radius_m=800)
    return market, topic


def test_nearby_orders_by_distance(pois):
    user = User.objects.create_user("g@example.com", "Strong!Pass123")
    c = APIClient()
    c.force_authenticate(user)
    res = c.get("/api/v1/pois-nearby/?lat=10.7726&lng=106.6981&radius=1000")
    names = [p["name"] for p in res.data["results"]]
    assert names == ["Chợ Bến Thành", "Dinh Độc Lập"]  # airport is ~6 km away
    assert res.data["results"][0]["distance_m"] < 20


def test_geofence_notifies_once(pois):
    market, topic = pois
    user = User.objects.create_user("g@example.com", "Strong!Pass123")
    c = APIClient()
    c.force_authenticate(user)
    res = c.post("/api/v1/geofence/check/", {"lat": 10.7726, "lng": 106.6981}, format="json")
    assert res.data["entered"][0]["name"] == "Chợ Bến Thành" and res.data["entered"][0]["new"] is True
    c.post("/api/v1/geofence/check/", {"lat": 10.7726, "lng": 106.6981}, format="json")
    assert user.notifications.filter(kind="location").count() == 1  # cooldown
    far = c.post("/api/v1/geofence/check/", {"lat": 10.80, "lng": 106.70}, format="json")
    assert far.data["entered"] == []


def test_only_staff_edit_pois(pois):
    learner = User.objects.create_user("l@example.com", "Strong!Pass123")
    c = APIClient()
    c.force_authenticate(learner)
    assert c.post("/api/v1/pois/", {"name": "X", "category": "park", "lat": 10, "lng": 106}, format="json").status_code == 403
    staff = User.objects.create_user("s@example.com", "Strong!Pass123", role="staff")
    c.force_authenticate(staff)
    assert c.post("/api/v1/pois/", {"name": "X", "category": "park", "lat": 10, "lng": 106}, format="json").status_code == 201
