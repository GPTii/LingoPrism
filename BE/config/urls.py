from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.core.dashboard import DashboardView

api_v1 = [
    path("", include("apps.core.urls")),
    path("auth/", include("apps.accounts.urls.auth")),
    path("", include("apps.accounts.urls.users")),
    path("", include("apps.vocab.urls")),
    path("", include("apps.learning.urls")),
    path("", include("apps.algorithms.urls")),
    path("", include("apps.gamification.urls")),
    path("", include("apps.notifications.urls")),
    path("", include("apps.quizzes.urls")),
    path("", include("apps.community.urls")),
    path("", include("apps.chat.urls")),
    path("", include("apps.detection.urls")),
    path("", include("apps.gis.urls")),
    path("", include("apps.literacy.urls")),
    path("", include("apps.games.urls")),
    path("", include("apps.audit.urls")),
    path("", include("apps.aitalk.urls")),
    path("admin/dashboard/", DashboardView.as_view(), name="admin-dashboard"),
]

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/v1/", include(api_v1)),
]
if getattr(settings, "API_DOCS", True):
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
