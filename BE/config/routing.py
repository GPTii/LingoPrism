from django.urls import path

from apps.chat.consumers import GroupChatConsumer, SupportChatConsumer
from apps.notifications.consumers import UserEventsConsumer

websocket_urlpatterns = [
    path("ws/events/", UserEventsConsumer.as_asgi()),
    path("ws/groups/<int:group_id>/", GroupChatConsumer.as_asgi()),
    path("ws/support/<int:conversation_id>/", SupportChatConsumer.as_asgi()),
]
