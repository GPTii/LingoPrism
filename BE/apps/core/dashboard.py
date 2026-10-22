from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsStaffRole


class DashboardView(APIView):
    permission_classes = [IsStaffRole]

    @extend_schema(tags=["admin-dashboard"], responses={200: dict})
    def get(self, request):
        from apps.chat.models import SupportConversation
        from apps.community.models import Post, PostReport, UserReport
        from apps.detection.models import Detection, DetectionItem
        from apps.learning.models import ReviewLog, StudySession
        from apps.quizzes.models import Submission
        from apps.vocab.models import ErrorReport, WordTranslation

        User = get_user_model()
        now = timezone.now()
        start = timezone.localdate() - timedelta(days=13)
        today = timezone.localdate()

        def per_day(qs, field):
            rows = qs.filter(**{f"{field}__date__gte": start}).annotate(day=TruncDate(field)).values("day").annotate(n=Count("id"))
            got = {r["day"]: r["n"] for r in rows}
            days = [start + timedelta(days=i) for i in range(14)]
            return [{"date": d, "count": got.get(d, 0)} for d in days]

        return Response({
            "users": {
                "total": User.objects.count(),
                "learners": User.objects.filter(role="learner").count(),
                "kids": User.objects.filter(learner_type="kid").count(),
                "new_7d": User.objects.filter(created_at__gte=now - timedelta(days=7)).count(),
                "active_today": ReviewLog.objects.filter(created_at__date=today).values("user").distinct().count(),
                "by_language": list(User.objects.filter(role="learner").values("active_language", "zh_script").annotate(n=Count("id"))),
            },
            "learning": {
                "sessions_per_day": per_day(StudySession.objects.all(), "started_at"),
                "answers_today": ReviewLog.objects.filter(created_at__date=today).count(),
            },
            "detection": {
                "per_day": per_day(Detection.objects.all(), "created_at"),
                "top_labels": list(DetectionItem.objects.values("label").annotate(n=Count("id")).order_by("-n")[:10]),
            },
            "content": {
                "translations": list(WordTranslation.objects.values("language_id", "status").annotate(n=Count("id"))),
                "open_error_reports": ErrorReport.objects.filter(status="open").count(),
                "pending_post_reports": PostReport.objects.filter(status="pending").count(),
                "pending_user_reports": UserReport.objects.filter(status="pending").count(),
                "posts_7d": Post.objects.filter(created_at__gte=now - timedelta(days=7)).count(),
            },
            "exams": {"waiting_for_grading": Submission.objects.filter(status="submitted").count()},
            "support": {"open_conversations": SupportConversation.objects.filter(status="open").count()},
        })
