from django.urls import path
from rest_framework.routers import DefaultRouter

from .. import views

router = DefaultRouter()
router.register("admin/users", views.AdminUserViewSet, basename="admin-users")

urlpatterns = [
    path("me/", views.MeView.as_view(), name="me"),
    path("me/goal/", views.MyGoalView.as_view(), name="me-goal"),
    path("me/delete/", views.DeleteAccountView.as_view(), name="me-delete"),
    path("me/parent-consent/request/", views.ParentConsentRequestView.as_view(), name="parent-consent-request"),
    path("me/parent-consent/confirm/", views.ParentConsentConfirmView.as_view(), name="parent-consent-confirm"),
    path("users/<int:pk>/", views.PublicUserView.as_view(), name="user-public"),
] + router.urls
