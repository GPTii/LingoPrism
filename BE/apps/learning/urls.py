from django.urls import path
from rest_framework.routers import DefaultRouter

from . import levels, sentences, stats, views

router = DefaultRouter()
router.register("my-words", views.MyWordViewSet, basename="my-words")
router.register("sessions", views.StudySessionViewSet, basename="sessions")
router.register("sentences", sentences.SentencePracticeViewSet, basename="sentences")

urlpatterns = router.urls + [
    path("levels/", levels.LevelsView.as_view(), name="levels"),
    path("stats/learning/", stats.LearningStatsView.as_view(), name="learning-stats"),
    path("levels/<int:n>/test/", levels.LevelTestView.as_view(), name="level-test"),
]
