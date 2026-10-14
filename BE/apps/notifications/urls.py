from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("notifications", views.NotificationViewSet, basename="notifications")
router.register("devices", views.DeviceViewSet, basename="devices")

urlpatterns = [
    path("notification-settings/", views.NotificationSettingView.as_view(), name="notification-settings"),
    path("admin/broadcast/", views.BroadcastView.as_view(), name="admin-broadcast"),
] + router.urls
