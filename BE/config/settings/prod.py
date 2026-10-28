from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import LOGGING, REST_FRAMEWORK, SECRET_KEY, env

DEBUG = False
if SECRET_KEY == "dev-insecure-change-me" or len(SECRET_KEY) < 40:
    # a known key lets anyone forge sessions/tokens: refuse to start rather than run insecure
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set to a long random value in production")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)  # usually done by nginx/Cloudflare
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
# turn on (31536000) once HTTPS works for the domain and every subdomain: browsers then refuse plain HTTP
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)

# behind nginx: the client IP for rate limits is the one nginx puts in X-Forwarded-For
REST_FRAMEWORK["NUM_PROXIES"] = env.int("NUM_PROXIES", default=1)
# the browsable API is a debugging aid, not something to expose
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = ["rest_framework.renderers.JSONRenderer"]

# Swagger / OpenAPI schema list every endpoint: off in production unless asked for
API_DOCS = env.bool("API_DOCS", default=False)

LOGGING["loggers"] = {"security": {"handlers": ["console"], "level": "WARNING", "propagate": False}}

# server errors (API and the e-mail worker) go to Sentry once SENTRY_DSN is set: apps/core/error_tracking.py
if env("SENTRY_DSN", default=""):
    from apps.core import error_tracking

    error_tracking.init(env("SENTRY_DSN"), env("SENTRY_ENVIRONMENT", default="production"))
