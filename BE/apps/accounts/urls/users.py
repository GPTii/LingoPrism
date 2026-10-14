from django.urls import path
from rest_framework.routers import DefaultRouter

from .. import views

router = DefaultRouter()
router.register("admin/users", views.AdminUserViewSet, basename="admin-users")

urlpatterns = [
    path("me/", views.MeView.as_view(), name="me"),
    path("me/goal/", views.MyGoalView.as_view(), name="me-goal"),
    path("users/<int:pk>/", views.PublicUserView.as_view(), name="user-public"),
] + router.urls
