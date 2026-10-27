from django.db import transaction
from django.db.models import ProtectedError
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response

BULK_LIMIT = 500


class Conflict(APIException):
    """The object is still used by other data (a database PROTECT): lock or hide it instead."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "Đang được dữ liệu khác sử dụng nên không xoá được."


def _reason(exc: APIException) -> str:
    detail = exc.detail
    while isinstance(detail, (list, dict)) and detail:
        detail = next(iter(detail.values())) if isinstance(detail, dict) else detail[0]
    return str(detail)


class BulkDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), min_length=1, max_length=BULK_LIMIT)


class BulkDeleteMixin:
    """POST <list>/bulk-delete/ {"ids": [...]}: deletes many rows at once (the ticked rows of a table).

    Each object goes through the same rules as deleting it alone: it must be in the view's queryset (so a learner only
    ever reaches their own things), pass the object permissions, and `perform_destroy` (where the guards live, e.g.
    "not your own account"). An object that cannot go is skipped with its reason; the others are still deleted.
    """

    def get_bulk_delete_queryset(self):
        return self.get_queryset()

    @extend_schema(request=BulkDeleteSerializer, responses={200: dict})
    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete(self, request):
        ser = BulkDeleteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ids = set(ser.validated_data["ids"])
        deleted, skipped = 0, []
        found = list(self.get_bulk_delete_queryset().filter(pk__in=ids))
        for obj in found:
            pk = obj.pk
            try:
                self.check_object_permissions(request, obj)
                with transaction.atomic():
                    self.perform_destroy(obj)
                deleted += 1
            except APIException as e:
                skipped.append({"id": pk, "reason": _reason(e)})
            except ProtectedError:
                skipped.append({"id": pk, "reason": Conflict.default_detail})
        return Response({"deleted": deleted, "skipped": skipped, "not_found": len(ids) - len(found)})
