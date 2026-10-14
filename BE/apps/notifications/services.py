import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Notification

log = logging.getLogger(__name__)


def user_group(user_id: int) -> str:
    return f"user_{user_id}"


def push_event(user_id: int, event: str, payload: dict):
    """Send a realtime event to every open web/app connection of a user (best effort)."""
    layer = get_channel_layer()
    if layer is None:
        return
    try:
        async_to_sync(layer.group_send)(user_group(user_id), {"type": "user.event", "event": event, "payload": payload})
    except Exception:  # realtime must never break the request
        log.exception("push_event failed")


def notify(user, kind: str, title: str, body: str = "", data: dict | None = None, image: str = "") -> Notification:
    n = Notification.objects.create(user=user, kind=kind, title=title, body=body, data=data or {}, image=image)
    push_event(user.id, "notification", {
        "id": n.id, "kind": n.kind, "title": n.title, "body": n.body, "image": n.image, "data": n.data,
        "created_at": n.created_at.isoformat(),
    })
    return n
