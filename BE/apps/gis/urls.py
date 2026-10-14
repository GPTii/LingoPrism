from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("pois", views.PoiViewSet, basename="pois")

urlpatterns = [
    path("pois-nearby/", views.NearbyView.as_view(), name="pois-nearby"),
    path("geofence/check/", views.GeofenceCheckView.as_view(), name="geofence-check"),
] + router.urls
