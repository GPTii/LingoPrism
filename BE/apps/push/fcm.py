"""Firebase Cloud Messaging (HTTP v1) without an extra SDK: google-auth (already used for Google sign-in)
signs a short-lived token from the service-account file, `requests` posts the message.

Off until FIREBASE_CREDENTIALS_FILE points to the project's service-account JSON (a secret: it lives
on the server next to .env, never in git)."""
import json
import logging
import threading
from functools import lru_cache

from django.conf import settings

log = logging.getLogger(__name__)
SCOPE = "https://www.googleapis.com/auth/firebase.messaging"


def enabled() -> bool:
    return bool(getattr(settings, "FIREBASE_CREDENTIALS_FILE", ""))


@lru_cache(maxsize=1)
def _credentials():
    from google.oauth2 import service_account

    path = settings.FIREBASE_CREDENTIALS_FILE
    with open(path, encoding="utf-8") as f:
        project = json.load(f)["project_id"]
    return service_account.Credentials.from_service_account_file(path, scopes=[SCOPE]), project


def _access_token() -> tuple[str, str]:
    from google.auth.transport.requests import Request

    creds, project = _credentials()
    if not creds.valid:
        creds.refresh(Request())
    return creds.token, project


def send(token: str, title: str, body: str, data: dict | None = None) -> str:
    """Send one message. Returns "ok", "gone" (the app was uninstalled: forget this token) or "error"."""
    import requests

    access, project = _access_token()
    message = {
        "message": {
            "token": token,
            "notification": {"title": title[:120], "body": body[:300]},
            # data values must be strings; the app opens data["route"] when tapped
            "data": {k: str(v) for k, v in (data or {}).items()},
            "android": {"priority": "high", "notification": {"channel_id": "lingoprism_default"}},
        }
    }
    res = requests.post(f"https://fcm.googleapis.com/v1/projects/{project}/messages:send",
                        json=message, headers={"Authorization": f"Bearer {access}"}, timeout=10)
    if res.ok:
        return "ok"
    if res.status_code in (404, 400) and ("UNREGISTERED" in res.text or "registration-token-not-registered" in res.text):
        return "gone"
    log.warning("FCM %s: %s", res.status_code, res.text[:300])
    return "error"


def send_to_user_async(user_id: int, title: str, body: str, data: dict | None = None):
    """Deliver to every device of the user in a background thread (the request that created the
    notification does not wait for Google)."""
    from apps.notifications.models import DeviceToken

    tokens = list(DeviceToken.objects.filter(user_id=user_id).values_list("token", flat=True))
    if not tokens:
        return

    def run():
        for t in tokens:
            try:
                if send(t, title, body, data) == "gone":
                    DeviceToken.objects.filter(token=t).delete()
            except Exception:  # a failed push must never break anything else
                log.exception("FCM send failed")

    threading.Thread(target=run, daemon=True).start()
