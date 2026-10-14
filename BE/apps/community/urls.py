from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("posts", views.PostViewSet, basename="posts")
router.register("community/users", views.CommunityUserViewSet, basename="community-users")
router.register("groups", views.GroupViewSet, basename="groups")
router.register("admin/post-reports", views.AdminPostReportViewSet, basename="admin-post-reports")
router.register("admin/posts", views.AdminPostViewSet, basename="admin-posts")

urlpatterns = router.urls
