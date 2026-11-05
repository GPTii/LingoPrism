from django.urls import path

from . import views

urlpatterns = [
    path("speech/status/", views.SpeechStatusView.as_view(), name="speech-status"),
    path("speech/assess/", views.AssessView.as_view(), name="speech-assess"),
    path("speech/progress/", views.ProgressView.as_view(), name="speech-progress"),
]
