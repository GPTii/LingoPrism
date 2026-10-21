import json
import re

from .models import AuditLog

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
API_PREFIX = "/api/v1/"
# signing in, refreshing a token or changing one's own password is not an administrative action
SKIP = re.compile(r"^/api/v1/(auth/|me/)")
ID = re.compile(r"^\d+$")


def _resource_and_id(path: str) -> tuple[str, str]:
    parts = [p for p in path[len(API_PREFIX):].strip("/").split("/") if p]
    ids = [p for p in parts if ID.match(p)]
    names = [p for p in parts if not ID.match(p)]
    return "/".join(names[:2])[:60], (ids[0] if ids else "")


def _field_names(request) -> list[str]:
    """Field names of a JSON body. Multipart uploads are left unread here so the view can parse them."""
    try:
        if request.content_type == "application/json" and request.body:
            data = json.loads(request.body)
            return sorted(data.keys())[:40] if isinstance(data, dict) else []
    except Exception:  # unreadable bodies are simply not described
        pass
    return []


class AuditLogMiddleware:
    """Writes an AuditLog row for every successful change an admin / staff member makes through the API."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        fields = _field_names(request) if request.method in WRITE_METHODS and request.path.startswith(API_PREFIX) else None
        response = self.get_response(request)
        if fields is None or SKIP.match(request.path) or response.status_code >= 400:
            return response
        user = getattr(request, "user", None)  # set by DRF once the JWT is authenticated
        if not (user and user.is_authenticated and getattr(user, "role", "") in ("admin", "staff")):
            return response
        resource, object_id = _resource_and_id(request.path)
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
        try:
            AuditLog.objects.create(
                actor=user, actor_email=user.email, actor_role=user.role, method=request.method,
                path=request.path[:300], resource=resource, object_id=object_id, status_code=response.status_code,
                fields=fields, ip=forwarded or request.META.get("REMOTE_ADDR") or None,
            )
        except Exception:  # logging must never break the action itself
            pass
        return response
