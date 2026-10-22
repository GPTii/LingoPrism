from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("detections", views.DetectionViewSet, basename="detections")
router.register("admin/model-versions", views.AdminModelVersionViewSet, basename="admin-model-versions")
router.register("admin/detections", views.AdminDetectionViewSet, basename="admin-detections")
router.register("admin/detection-reports", views.AdminCorrectionViewSet, basename="admin-detection-reports")

urlpatterns = [
    path("detect/", views.DetectView.as_view(), name="detect"),
] + router.urls
