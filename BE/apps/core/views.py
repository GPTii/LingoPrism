from django.db import DatabaseError, connection
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@extend_schema(tags=["system"], responses={200: dict})
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """200 when the database answers, 503 when it does not (what an uptime monitor watches)."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version(), (SELECT extversion FROM pg_extension WHERE extname = 'earthdistance')")
            version, earthdistance = cursor.fetchone()
    except DatabaseError:
        return Response({"status": "error", "database": "unreachable"}, status=503)
    return Response({"status": "ok", "database": version.split(",")[0], "earthdistance": earthdistance})
