from django.urls import path

from . import views

urlpatterns = [
    path("games/map/", views.GameMapView.as_view(), name="games-map"),
    path("games/rounds/<str:node>/", views.GameRoundView.as_view(), name="games-round"),
    path("games/rounds/<str:node>/finish/", views.GameFinishView.as_view(), name="games-finish"),
    path("games/chests/<str:node>/open/", views.ChestOpenView.as_view(), name="games-chest"),
]
