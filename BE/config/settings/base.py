"""Base settings shared by every environment."""
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR.parent / ".env", overwrite=False)

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
# Django admin path: a non-default one keeps password-guessing bots off it (nginx proxies /django-admin/ by default)
ADMIN_URL = env("DJANGO_ADMIN_URL", default="django-admin/")

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # third party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    "corsheaders",
    "channels",
    # local
    "apps.core",
    "apps.accounts",
    "apps.vocab",
    "apps.learning",
    "apps.literacy",
    "apps.notifications",
    "apps.gamification",
    "apps.quizzes",
    "apps.community",
    "apps.chat",
    "apps.detection",
    "apps.gis",
    "apps.algorithms",
    "apps.audit",
    "apps.push",
    "apps.aitalk",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "apps.core.middleware.RejectNulBytesMiddleware",  # a NUL character would be a 500 in PostgreSQL: 400 instead
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.audit.middleware.AuditLogMiddleware",  # admin / staff changes → AuditLog
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": env.db_url(
        "DATABASE_URL",
        default="postgres://postgres:postgres@localhost:5432/lingoprism",
    )
}
# Under ASGI (daphne) every request runs on its own thread, so persistent connections pile up one per thread until
# PostgreSQL refuses new clients ("too many clients", 500s at ~20 concurrent users). Close each one after its request.
# A query running away is killed instead of holding the DB.
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=0)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
DATABASES["default"].setdefault("OPTIONS", {})["options"] = f"-c statement_timeout={env.int('DB_STATEMENT_TIMEOUT_MS', default=15000)}"
DATABASES["default"]["OPTIONS"]["connect_timeout"] = 5  # a database that is down answers fast, not after minutes
# ...but a crowd (200 learners opening the app together) still needs one connection per request in flight, past
# max_connections (100). One pool per process: at most DB_POOL_MAX connections, a request beyond that waits for a
# free one (up to 10 s: longer only holds threads while the database is down) instead of failing.
# Requires CONN_MAX_AGE = 0. DB_POOL_MAX=0 turns it off.
if env.int("DB_POOL_MAX", default=40):
    DATABASES["default"]["OPTIONS"]["pool"] = {"min_size": 2, "max_size": env.int("DB_POOL_MAX", default=40), "timeout": 10}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}

CACHES = {
    "default": {
        # Redis down = an empty cache, not a site down (the rate-limit counters live here: apps/core/cache.py)
        "BACKEND": "apps.core.cache.ResilientRedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"socket_connect_timeout": 2, "socket_timeout": 2},
    }
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TIMEZONE = TIME_ZONE

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.core.authentication.LockAwareJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
        "apps.core.filters.CreatedDateFilter",  # ?created_from=&created_to= on every list with a created_at
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    # rate limits (apps/core/throttles.py); ScopedRateThrottle only acts on views that set throttle_scope
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("THROTTLE_ANON", default="300/min"),  # per IP, shared by a classroom
        "user": env("THROTTLE_USER", default="300/min"),
        "login": env("THROTTLE_LOGIN", default="40/min"),  # per IP (a classroom shares one IP); per account: auth_email
        "auth_email": env("THROTTLE_AUTH_EMAIL", default="10/hour"),  # per target e-mail, any IP
        "register": env("THROTTLE_REGISTER", default="60/hour"),  # per IP: a teacher may sign up a whole class
        "password_reset": env("THROTTLE_PASSWORD_RESET", default="10/hour"),
        "detect": env("THROTTLE_DETECT", default="30/min"),  # YOLO on the CPU: the most expensive endpoint
        "upload": env("THROTTLE_UPLOAD", default="30/hour"),  # community posts, avatars
        "report": env("THROTTLE_REPORT", default="30/hour"),
        "ai_dialogue": env("THROTTLE_AI_DIALOGUE", default="20/hour"),  # each one is a paid AI call
        "message": env("THROTTLE_MESSAGE", default="60/min"),  # private messages
    },
    # proxies in front of Django whose X-Forwarded-For is trusted (nginx = 1, Cloudflare + nginx = 2)
    "NUM_PROXIES": env.int("NUM_PROXIES", default=0),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=60)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS", default=30)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "USER_AUTHENTICATION_RULE": "apps.core.authentication.can_sign_in",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "LingoPrism API",
    "DESCRIPTION": "REST API dùng chung cho web (React) và app mobile (Flutter).",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["http://localhost:5173"])

GOOGLE_CLIENT_IDS = env.list("GOOGLE_CLIENT_IDS", default=[])
# Firebase Cloud Messaging: path to the service-account JSON (secret, on the server only); empty = push off
FIREBASE_CREDENTIALS_FILE = env("FIREBASE_CREDENTIALS_FILE", default="")
# AI dialogue from a photo (Anthropic API key, secret); empty = the feature is off
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")
AI_TALK_MODEL = env("AI_TALK_MODEL", default="claude-opus-5-5")
# Gemini (Google AI Studio, free tier) is used first when its key is set
GEMINI_API_KEY = env("GEMINI_API_KEY", default="")
GEMINI_MODEL = env("GEMINI_MODEL", default="gemini-flash-latest")
# the "Web application" client the web page signs in with (public; defaults to the first accepted ID)
GOOGLE_WEB_CLIENT_ID = env("GOOGLE_WEB_CLIENT_ID", default="") or (GOOGLE_CLIENT_IDS[0] if GOOGLE_CLIENT_IDS else "")

EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="LingoPrism <no-reply@lingoprism.local>")

YOLO_MODEL_PATH = env("YOLO_MODEL_PATH", default=str(BASE_DIR / "models" / "yolov10n.onnx"))
# pretrained COCO model used alongside the trained one for the COCO classes (see detection.inference.EnsembleDetector)
YOLO_BASE_MODEL_PATH = env("YOLO_BASE_MODEL_PATH", default=str(BASE_DIR / "models" / "yolov10m-int8.onnx"))
# CLIP re-check of look-alike labels (AI/scripts/export_clip.py, detection.inference.LabelVerifier); missing = off
DETECTION_CLIP_PATH = env("DETECTION_CLIP_PATH", default=str(BASE_DIR / "models" / "clip-mobileclip2-s2.onnx"))
# image embedder of the detection correction memory (AI/scripts/export_embedder.py); missing = memory off
DETECTION_EMBEDDER_PATH = env("DETECTION_EMBEDDER_PATH", default=str(BASE_DIR / "models" / "embedder.onnx"))
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
}
