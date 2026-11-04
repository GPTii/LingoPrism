from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("assignments", views.AssignmentViewSet, basename="assignments")
urlpatterns = router.urls
