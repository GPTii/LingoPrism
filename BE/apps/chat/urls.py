from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("support/conversations", views.SupportConversationViewSet, basename="support-conversations")
router.register("messages/threads", views.DirectThreadViewSet, basename="direct-threads")

urlpatterns = [
    path("groups/<int:group_id>/messages/", views.GroupMessagesView.as_view(), name="group-messages"),
    path(
        "groups/<int:group_id>/messages/<int:message_id>/heart/",
        views.GroupMessageHeartView.as_view(),
        name="group-message-heart",
    ),
] + router.urls
