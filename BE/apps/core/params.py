def int_param(request, name: str, default=None):
    """An integer query parameter; a missing or malformed one (?before=abc) is the default instead of a 500."""
    try:
        return int(request.query_params[name])
    except (KeyError, TypeError, ValueError):
        return default
