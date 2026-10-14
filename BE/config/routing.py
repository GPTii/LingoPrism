from django.urls import path

from apps.notifications.consumers import UserEventsConsumer

websocket_urlpatterns = [
    path("ws/events/", UserEventsConsumer.as_asgi()),
]
