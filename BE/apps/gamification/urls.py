from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("quests", views.QuestViewSet, basename="quests")
router.register("badges", views.BadgeViewSet, basename="badges")
router.register("shop/items", views.ShopViewSet, basename="shop-items")
router.register("admin/badges", views.AdminBadgeViewSet, basename="admin-badges")
router.register("admin/items", views.AdminItemViewSet, basename="admin-items")
router.register("admin/league-tiers", views.AdminTierViewSet, basename="admin-league-tiers")

urlpatterns = [
    path("gamification/summary/", views.SummaryView.as_view(), name="gamification-summary"),
    path("gamification/progress/", views.ProgressView.as_view(), name="gamification-progress"),
    path("gamification/xp-history/", views.XpHistoryView.as_view(), name="gamification-xp-history"),
    path("mascot/", views.MascotView.as_view(), name="mascot"),
    path("mascot/buy/", views.MascotBuyView.as_view(), name="mascot-buy"),
    path("leaderboard/", views.LeaderboardView.as_view(), name="leaderboard"),
    path("users/<int:user_id>/stats/", views.PublicProfileStatsView.as_view(), name="user-stats"),
] + router.urls
