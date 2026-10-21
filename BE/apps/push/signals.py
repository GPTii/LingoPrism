from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.notifications.models import Notification, NotificationSetting

from . import fcm

SOCIAL = {Notification.Kind.FOLLOW, Notification.Kind.COMMENT, Notification.Kind.LIKE, Notification.Kind.MESSAGE}


@receiver(post_save, sender=Notification, dispatch_uid="push-new-notification")
def push_new_notification(sender, instance: Notification, created: bool, **kwargs):
    """Every new in-app notification also reaches the learner's phone when it is closed –
    unless they turned push (or social push) off in their settings."""
    if not created or not fcm.enabled():
        return
    pref = NotificationSetting.objects.filter(user_id=instance.user_id).first()
    if pref and (not pref.push_enabled or (instance.kind in SOCIAL and not pref.social_enabled)):
        return
    fcm.send_to_user_async(instance.user_id, instance.title, instance.body,
                           {**(instance.data or {}), "notification_id": instance.id, "kind": instance.kind})
