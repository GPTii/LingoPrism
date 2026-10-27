from django.urls import path

from . import views

urlpatterns = [
    path("releases/", views.releases, name="releases"),
    path("health/", views.health, name="health"),
]
