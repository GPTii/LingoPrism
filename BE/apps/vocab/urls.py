from rest_framework.routers import DefaultRouter

from . import views
from .candidates import AdminCandidateViewSet

router = DefaultRouter()
router.register("languages", views.LanguageViewSet, basename="languages")
router.register("topics", views.TopicViewSet, basename="topics")
router.register("words", views.WordViewSet, basename="words")
router.register("reports", views.ErrorReportViewSet, basename="reports")
router.register("admin/topics", views.AdminTopicViewSet, basename="admin-topics")
router.register("admin/words", views.AdminWordViewSet, basename="admin-words")
router.register("admin/translations", views.AdminTranslationViewSet, basename="admin-translations")
router.register("admin/examples", views.AdminExampleViewSet, basename="admin-examples")
router.register("admin/reports", views.AdminErrorReportViewSet, basename="admin-reports")
router.register("admin/vocab-stats", views.AdminVocabStatsView, basename="admin-vocab-stats")
router.register("admin/candidates", AdminCandidateViewSet, basename="admin-candidates")

urlpatterns = router.urls
