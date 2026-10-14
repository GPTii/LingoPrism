from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("exams", views.ExamViewSet, basename="exams")
router.register("submissions", views.SubmissionViewSet, basename="submissions")
router.register("admin/questions", views.AdminQuestionViewSet, basename="admin-questions")
router.register("admin/exams", views.AdminExamViewSet, basename="admin-exams")
router.register("admin/submissions", views.AdminSubmissionViewSet, basename="admin-submissions")

urlpatterns = router.urls
