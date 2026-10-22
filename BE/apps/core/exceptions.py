from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """Wrap DRF errors in a consistent shape: {"detail": str, "errors": {...}}."""
    response = exception_handler(exc, context)
    if response is None:
        return None
    data = response.data
    if isinstance(exc, Throttled):  # 429: rate limit (apps/core/throttles.py)
        wait = f" Hãy thử lại sau {int(exc.wait)} giây." if exc.wait else ""
        response.data = {"detail": f"Bạn thao tác quá nhanh.{wait}", "errors": {}}
        return response
    if isinstance(data, dict) and "detail" in data and len(data) == 1:
        response.data = {"detail": str(data["detail"]), "errors": {}}
    elif isinstance(data, dict):
        first = next(iter(data.values()), "")
        message = first[0] if isinstance(first, list) and first else str(first)
        response.data = {"detail": str(message), "errors": data}
    else:
        response.data = {"detail": str(data[0]) if data else "Error", "errors": {"non_field_errors": data}}
    return response
