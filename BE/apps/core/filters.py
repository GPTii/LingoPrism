from datetime import date

from rest_framework.filters import BaseFilterBackend


def _day(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:  # a malformed date is ignored, never a 500
        return None


class CreatedDateFilter(BaseFilterBackend):
    """`?created_from=YYYY-MM-DD&created_to=YYYY-MM-DD` (both days included, Vietnam time) on every list whose model
    has a `created_at` field, or the field a view names in `date_filter_field` (e.g. "submitted_at")."""

    def _field(self, queryset, view):
        name = getattr(view, "date_filter_field", "created_at")
        if not name or queryset is None or not hasattr(queryset, "model"):
            return None
        return name if any(f.name == name for f in queryset.model._meta.get_fields()) else None

    def filter_queryset(self, request, queryset, view):
        field = self._field(queryset, view)
        if not field:
            return queryset
        start, end = _day(request.query_params.get("created_from")), _day(request.query_params.get("created_to"))
        if start:
            queryset = queryset.filter(**{f"{field}__date__gte": start})
        if end:
            queryset = queryset.filter(**{f"{field}__date__lte": end})
        return queryset

