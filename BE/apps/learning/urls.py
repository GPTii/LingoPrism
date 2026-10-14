from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("my-words", views.MyWordViewSet, basename="my-words")
router.register("sessions", views.StudySessionViewSet, basename="sessions")

urlpatterns = router.urls
