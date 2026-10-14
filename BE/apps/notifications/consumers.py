from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .services import user_group


class UserEventsConsumer(AsyncJsonWebsocketConsumer):
    """ws/events/?token=<JWT> – notifications, XP/streak updates, progress sync between web and app."""

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return
        self.group = user_group(user.id)
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.send_json({"event": "connected", "payload": {"user": user.id}})

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("event") == "ping":
            await self.send_json({"event": "pong", "payload": {}})

    async def user_event(self, message):
        await self.send_json({"event": message["event"], "payload": message["payload"]})
