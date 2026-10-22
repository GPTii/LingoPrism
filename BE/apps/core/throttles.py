"""Rate limits (OWASP API4:2023 Unrestricted Resource Consumption, API6 sensitive business flows).

Defaults in settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]; a view opts into a stricter scope with
`throttle_scope = "login"` etc. The client IP comes from X-Forwarded-For only for NUM_PROXIES trusted proxies
(nginx), otherwise every user would share nginx's IP and one abuser would block everybody.
"""
import hashlib

from rest_framework.throttling import SimpleRateThrottle


class EmailRateThrottle(SimpleRateThrottle):
    """Per target e-mail, whatever the IP: stops spreading a password guess / reset-code flood over many IPs and
    e-mail bombing one person's mailbox."""

    scope = "auth_email"

    def get_cache_key(self, request, view):
        email = str(request.data.get("email", "") if hasattr(request, "data") else "").strip().lower()
        if not email:
            return None
        return self.cache_format % {"scope": self.scope, "ident": hashlib.sha256(email.encode()).hexdigest()[:32]}


class ActionThrottleMixin:
    """ViewSet: a stricter scope for some actions only, e.g. throttle_scopes = {"create": "upload"} (listing stays
    under the default user rate)."""

    throttle_scopes: dict[str, str] = {}

    def get_throttles(self):
        self.throttle_scope = self.throttle_scopes.get(getattr(self, "action", None), "")
        return super().get_throttles()
