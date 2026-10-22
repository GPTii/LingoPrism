from django.urls import path

from . import views

urlpatterns = [
    path("literacy/lessons/", views.LessonListView.as_view(), name="literacy-lessons"),
    path("literacy/lessons/<int:n>/", views.LessonView.as_view(), name="literacy-lesson"),
    path("literacy/lessons/<int:n>/finish/", views.FinishView.as_view(), name="literacy-finish"),
    path("literacy/check/", views.CheckView.as_view(), name="literacy-check"),
]
