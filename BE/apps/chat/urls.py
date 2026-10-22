from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("support/conversations", views.SupportConversationViewSet, basename="support-conversations")
router.register("messages/threads", views.DirectThreadViewSet, basename="direct-threads")

urlpatterns = [
    path("groups/<int:group_id>/messages/", views.GroupMessagesView.as_view(), name="group-messages"),
] + router.urls
