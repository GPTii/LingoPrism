from django.urls import path

from . import views

urlpatterns = [
    path("ai/status/", views.AiStatusView.as_view(), name="ai-status"),
    path("detections/<int:pk>/dialogue/", views.PhotoDialogueView.as_view(), name="photo-dialogue"),
]
