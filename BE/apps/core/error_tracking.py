"""Error tracking (Sentry): a crash on the server reaches the owner with its stack trace, instead of only a 500 that
nobody reports. Off until SENTRY_DSN is set (a free project on sentry.io gives one); config/settings/prod.py.

What leaves the server is the error itself and where in the code it happened, nothing about the learner
(Privacy policy, "Chia sẻ"): no request body, query string, cookies, headers, IP address or user, and no values of
local variables (they can hold an e-mail, a message, a child's name). Many learners are children."""
import json
import re

from .releases import SOURCE

KEEP_HEADERS = {"User-Agent", "Content-Type", "Accept-Language"}
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")


def _hide_emails(text):
    return EMAIL.sub("[email]", text) if isinstance(text, str) else text


def scrub(event, hint=None):
    # error messages can quote data, e.g. Key (email)=(an@address) already exists
    for exc in (event.get("exception") or {}).get("values", []):
        exc["value"] = _hide_emails(exc.get("value"))
    if isinstance(event.get("logentry"), dict):
        event["logentry"]["message"] = _hide_emails(event["logentry"].get("message"))
        event["logentry"].pop("params", None)
    event["message"] = _hide_emails(event.get("message"))
    if event["message"] is None:
        event.pop("message")
    request = event.get("request")
    if request:
        for key in ("data", "query_string", "cookies", "env"):
            request.pop(key, None)
        request["headers"] = {k: v for k, v in (request.get("headers") or {}).items() if k in KEEP_HEADERS}
        if "url" in request:
            request["url"] = request["url"].split("?", 1)[0]
    event.pop("user", None)
    for crumb in (event.get("breadcrumbs") or {}).get("values", []):
        crumb.pop("data", None)  # SQL parameters, HTTP query strings
    return event


def init(dsn: str, environment: str = "production", **options):
    import sentry_sdk

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=f"lingoprism@{json.loads(SOURCE.read_text(encoding='utf-8'))[0]['version']}",
        send_default_pii=False,
        include_local_variables=False,
        max_request_body_size="never",
        traces_sample_rate=0,  # errors only: performance tracing would use the free quota and send more data
        before_send=scrub,
        before_send_transaction=lambda event, hint: None,
        **options,
    )
