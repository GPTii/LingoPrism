from django.http import JsonResponse


class RejectNulBytesMiddleware:
    """PostgreSQL cannot store or compare text holding a NUL character: one in the query string or in a JSON body ends
    in a 500 deep inside a query (search, filters, any saved field). No real input contains one, so refuse it with a
    400 before any view runs."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if any("\x00" in key or any("\x00" in v for v in values) for key, values in request.GET.lists()):
            return self.refuse()
        if request.content_type == "application/json" and (b"\\u0000" in request.body or b"\x00" in request.body):
            return self.refuse()
        return self.get_response(request)

    @staticmethod
    def refuse():
        return JsonResponse({"detail": "Dữ liệu gửi lên có ký tự không hợp lệ", "errors": {}}, status=400)
