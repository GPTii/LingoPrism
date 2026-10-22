"""Realtime chat over WebSocket (Django Channels).

Client → server:  {"action": "send", "content": "...", "kind": "text|sticker|badge", "sticker": "...", "client_id": "..."}
                  {"action": "read"}                 (support chat)
                  {"action": "typing"}
Server → client:  {"event": "message" | "read" | "typing" | "error", "payload": {...}}
Every message carries the client's `client_id` back so the sender can measure latency and de-duplicate.
"""
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from . import services
from .models import SupportConversation


# per connection: a short burst is fine, a script flooding the room is not (token bucket)
BURST, PER_SECOND = 8, 1.0
MAX_FRAME_BYTES = 8 * 1024  # messages are cut to 1-2k characters anyway


class _BaseChatConsumer(AsyncJsonWebsocketConsumer):
    channel_group: str = ""

    def _allow(self) -> bool:
        now = time.monotonic()
        tokens, last = getattr(self, "_bucket", (BURST, now))
        tokens = min(BURST, tokens + (now - last) * PER_SECOND)
        if tokens < 1:
            self._bucket = (tokens, now)
            return False
        self._bucket = (tokens - 1, now)
        return True

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        if bytes_data is not None or (text_data and len(text_data) > MAX_FRAME_BYTES):
            await self.close(code=4413)
            return
        if not self._allow():
            await self._error("Bạn gửi quá nhanh, hãy chờ một chút")
            return
        try:
            await super().receive(text_data=text_data, **kwargs)
        except ValueError:  # not JSON
            await self._error("Dữ liệu không hợp lệ")

    async def disconnect(self, code):
        if self.channel_group:
            await self.channel_layer.group_discard(self.channel_group, self.channel_name)

    async def chat_event(self, message):
        await self.send_json({"event": message["event"], "payload": message["payload"]})

    async def _error(self, text):
        await self.send_json({"event": "error", "payload": {"detail": text}})


class GroupChatConsumer(_BaseChatConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        self.group_id = int(self.scope["url_route"]["kwargs"]["group_id"])
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return
        if not await database_sync_to_async(services.is_active_member)(self.user, self.group_id):
            await self.close(code=4403)
            return
        self.channel_group = services.group_channel(self.group_id)
        await self.channel_layer.group_add(self.channel_group, self.channel_name)
        await self.accept()

    async def receive_json(self, content, **kwargs):
        action = content.get("action")
        if action == "typing":
            await self.channel_layer.group_send(self.channel_group, {
                "type": "chat.event", "event": "typing", "payload": {"user": self.user.id, "display_name": self.user.display_name}})
            return
        if action != "send":
            return
        try:
            await database_sync_to_async(services.send_group_message)(
                self.user, self.group_id, kind=content.get("kind", "text"), content=content.get("content", ""),
                sticker=content.get("sticker", ""), badge_code=content.get("badge", ""), client_id=content.get("client_id", ""))
        except services.ChatError as e:
            await self._error(str(e))


class SupportChatConsumer(_BaseChatConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        conv_id = int(self.scope["url_route"]["kwargs"]["conversation_id"])
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return
        self.conv = await database_sync_to_async(SupportConversation.objects.filter(pk=conv_id).first)()
        if self.conv is None or not services.can_access_conversation(self.user, self.conv):
            await self.close(code=4403)
            return
        self.channel_group = services.support_channel(conv_id)
        await self.channel_layer.group_add(self.channel_group, self.channel_name)
        await self.accept()

    async def receive_json(self, content, **kwargs):
        action = content.get("action")
        try:
            if action == "send":
                await database_sync_to_async(services.send_support_message)(
                    self.user, self.conv, content.get("content", ""), content.get("client_id", ""))
            elif action == "read":
                await database_sync_to_async(services.mark_support_read)(self.user, self.conv)
            elif action == "typing":
                await self.channel_layer.group_send(self.channel_group, {
                    "type": "chat.event", "event": "typing", "payload": {"user": self.user.id}})
        except services.ChatError as e:
            await self._error(str(e))
