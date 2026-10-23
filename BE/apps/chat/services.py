import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from apps.gamification.services import owns_sticker

from .models import GroupMessage, SupportConversation, SupportMessage

log = logging.getLogger(__name__)


def group_channel(group_id: int) -> str:
    return f"chat_group_{group_id}"


def support_channel(conversation_id: int) -> str:
    return f"chat_support_{conversation_id}"


def _broadcast(channel: str, event: str, payload: dict):
    layer = get_channel_layer()
    if layer is None:
        return
    try:
        async_to_sync(layer.group_send)(channel, {"type": "chat.event", "event": event, "payload": payload})
    except Exception:
        log.exception("chat broadcast failed")


def group_message_payload(m: GroupMessage) -> dict:
    return {
        "id": m.id, "group": m.group_id, "kind": m.kind, "content": m.content, "sticker": m.sticker,
        "badge": {"code": m.badge.code, "name": m.badge.name, "icon": m.badge.icon} if m.badge_id else None,
        "client_id": m.client_id, "created_at": m.created_at.isoformat(),
        "user": {"id": m.user_id, "display_name": m.user.display_name if m.user else ""},
    }


class ChatError(Exception):
    pass


def is_active_member(user, group_id: int) -> bool:
    from apps.community.models import GroupMember

    return GroupMember.objects.filter(group_id=group_id, user=user, status="active").exists()


def send_group_message(user, group_id: int, kind: str = "text", content: str = "", sticker: str = "",
                       badge_code: str = "", client_id: str = "") -> GroupMessage:
    from apps.gamification.models import Badge, UserBadge

    if user.learner_type == "kid" and not user.is_staff_role:
        raise ChatError("Tài khoản trẻ em không dùng được chat nhóm")
    if not is_active_member(user, group_id):
        raise ChatError("Bạn chưa tham gia nhóm này")
    if client_id:
        existing = GroupMessage.objects.filter(group_id=group_id, user=user, client_id=client_id).first()
        if existing:
            return existing
    badge = None
    if kind == GroupMessage.Kind.TEXT and not content.strip():
        raise ChatError("Tin nhắn trống")
    if kind == GroupMessage.Kind.STICKER and not owns_sticker(user, sticker):
        raise ChatError("Bạn chưa sở hữu sticker này")
    if kind == GroupMessage.Kind.BADGE:
        badge = Badge.objects.filter(code=badge_code).first()
        if badge is None or not UserBadge.objects.filter(user=user, badge=badge).exists():
            raise ChatError("Bạn chưa có huy hiệu này")
    m = GroupMessage.objects.create(group_id=group_id, user=user, kind=kind, content=content.strip()[:1000],
                                    sticker=sticker, badge=badge, client_id=client_id[:40])
    _broadcast(group_channel(group_id), "message", group_message_payload(m))
    return m


def support_message_payload(m: SupportMessage) -> dict:
    return {
        "id": m.id, "conversation": m.conversation_id, "content": m.content, "client_id": m.client_id,
        "sender": {"id": m.sender_id, "display_name": m.sender.display_name, "is_staff": m.sender.is_staff_role},
        "created_at": m.created_at.isoformat(),
        "delivered_at": m.delivered_at.isoformat() if m.delivered_at else None,
        "read_at": m.read_at.isoformat() if m.read_at else None,
    }


def can_access_conversation(user, conv: SupportConversation) -> bool:
    return conv.learner_id == user.id or user.is_staff_role


def send_support_message(user, conv: SupportConversation, content: str, client_id: str = "") -> SupportMessage:
    from apps.notifications.models import Notification
    from apps.notifications.services import notify

    if not can_access_conversation(user, conv):
        raise ChatError("Không có quyền truy cập cuộc trò chuyện")
    if not content.strip():
        raise ChatError("Tin nhắn trống")
    if client_id:
        existing = SupportMessage.objects.filter(conversation=conv, sender=user, client_id=client_id).first()
        if existing:
            return existing
    m = SupportMessage.objects.create(conversation=conv, sender=user, content=content.strip()[:2000], client_id=client_id[:40])
    conv.last_message_at = m.created_at
    conv.status = SupportConversation.Status.OPEN
    if user.is_staff_role and conv.staff_id is None:
        conv.staff = user
    conv.save(update_fields=["last_message_at", "status", "staff"])
    _broadcast(support_channel(conv.id), "message", support_message_payload(m))
    recipient = conv.learner if user.is_staff_role else conv.staff
    if recipient and recipient.id != user.id:
        notify(recipient, Notification.Kind.MESSAGE, f"Tin nhắn mới từ {user.display_name}", m.content[:120],
               data={"route": f"/support/{conv.id}", "conversation": conv.id})
    return m


def mark_support_read(user, conv: SupportConversation) -> int:
    now = timezone.now()
    qs = conv.messages.exclude(sender=user).filter(read_at__isnull=True)
    ids = list(qs.values_list("id", flat=True))
    qs.update(read_at=now, delivered_at=now)
    if ids:
        _broadcast(support_channel(conv.id), "read", {"ids": ids, "reader": user.id, "read_at": now.isoformat()})
    return len(ids)


# ------------------------------------------------------------------ private messages

def can_message(user, other) -> bool:
    """Private messages only between two adult learners who are friends or follow each other: no stranger can write first, and
    children's accounts are kept out entirely. Staff use the support chat instead."""
    from apps.community.models import UserFollow

    if other is None or user.id == other.id or not other.is_active:
        return False
    if "kid" in (user.learner_type, other.learner_type):
        return False
    from apps.community.models import blocked_between

    if blocked_between(user.id, other.id):
        return False
    from apps.community.models import are_friends

    return are_friends(user.id, other.id) or (UserFollow.objects.filter(follower=user, following=other).exists()
                                               and UserFollow.objects.filter(follower=other, following=user).exists())


def thread_with(user, other):
    from .models import DirectThread

    a, b = sorted([user, other], key=lambda u: u.id)
    return DirectThread.objects.get_or_create(user_a=a, user_b=b)[0]


def direct_message_payload(m) -> dict:
    return {"id": m.id, "thread": m.thread_id, "sender": m.sender_id, "content": m.content, "sticker": m.sticker,
            "client_id": m.client_id,
            "read_at": m.read_at.isoformat() if m.read_at else None, "created_at": m.created_at.isoformat()}


def send_direct_message(user, thread, content: str, client_id: str = "", sticker: str = ""):
    from apps.notifications.models import Notification
    from apps.notifications.services import notify, push_event

    from .models import DirectMessage

    other = thread.other(user)
    if not can_message(user, other):
        raise ChatError("Hai bạn cần theo dõi nhau mới nhắn tin được")
    content = "" if sticker else content.strip()
    if sticker and not owns_sticker(user, sticker):
        raise ChatError("Bạn chưa sở hữu sticker này")
    if not content and not sticker:
        raise ChatError("Tin nhắn trống")
    if client_id:
        existing = DirectMessage.objects.filter(thread=thread, sender=user, client_id=client_id).first()
        if existing:
            return existing
    # one notification per burst: only when the other person has read everything before this message
    first_unread = not DirectMessage.objects.filter(thread=thread, sender=user, read_at__isnull=True).exists()
    m = DirectMessage.objects.create(thread=thread, sender=user, content=content[:1000], sticker=sticker, client_id=client_id)
    thread.last_message_at = m.created_at
    thread.save(update_fields=["last_message_at"])
    payload = direct_message_payload(m)
    for uid in (user.id, other.id):  # the sender's other tabs / devices too
        push_event(uid, "dm", payload)
    if first_unread:
        notify(other, Notification.Kind.MESSAGE, f"{user.display_name} nhắn tin cho bạn", content[:120] or "[Sticker]",
               data={"route": f"/messages/{thread.id}"})
    return m


def mark_direct_read(user, thread) -> int:
    n = thread.messages.filter(read_at__isnull=True).exclude(sender=user).update(read_at=timezone.now())
    if n:
        from apps.notifications.services import push_event

        push_event(thread.other(user).id, "dm_read", {"thread": thread.id})
    return n
