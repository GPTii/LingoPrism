from django.urls import path

from . import views

urlpatterns = [
    path("admin/algorithms/", views.AlgorithmsView.as_view(), name="admin-algorithms"),
    path("admin/algorithms/run/<str:kind>/", views.RunExperimentView.as_view(), name="admin-algorithms-run"),
    path("admin/algorithms/vip-preview/", views.VipPreviewView.as_view(), name="admin-algorithms-vip"),
    path("admin/algorithms/distractor-preview/", views.DistractorPreviewView.as_view(), name="admin-algorithms-distractor"),
]
