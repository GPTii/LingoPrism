from django.urls import path
from rest_framework.routers import DefaultRouter

from . import stats, views

router = DefaultRouter()
router.register("my-words", views.MyWordViewSet, basename="my-words")
router.register("sessions", views.StudySessionViewSet, basename="sessions")

urlpatterns = router.urls + [
    path("stats/learning/", stats.LearningStatsView.as_view(), name="learning-stats"),
]
