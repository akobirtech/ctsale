"""
CT Sale — umumiy sozlamalar.

Muhitga bog'liq farqlar dev.py / prod.py / test.py fayllarida.
Barcha sirlar .env orqali keladi (django-environ).
"""

from datetime import timedelta
from pathlib import Path

import environ

# backend/config/settings/base.py -> backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BASE_DIR.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

# --------------------------------------------------------------------------
# Asosiy
# --------------------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

SITE_NAME = env("SITE_NAME", default="CT Sale")
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:5173").rstrip("/")

# --------------------------------------------------------------------------
# Ilovalar
# --------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.rbac",
    "apps.catalog",
    "apps.products",
    "apps.mediafiles",
    "apps.moderation",
    "apps.interactions",
    "apps.notifications",
    "apps.telegrambot",
    "apps.analytics",
    "apps.seo",
    "apps.adminapi",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# --------------------------------------------------------------------------
# Middleware
# --------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
    "apps.core.middleware.LastSeenMiddleware",
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

# --------------------------------------------------------------------------
# Ma'lumotlar bazasi
# --------------------------------------------------------------------------
DATABASES = {
    "default": env.db("DATABASE_URL"),
}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
DATABASES["default"]["ATOMIC_REQUESTS"] = False

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

# --------------------------------------------------------------------------
# Parol xavfsizligi
# --------------------------------------------------------------------------
# Argon2id — parol hashlash uchun hozirgi tavsiya etilgan algoritm
# (OWASP). Ro'yxat tartibi muhim: birinchisi yangi parollar uchun,
# qolganlari eski hashlarni tekshirib, kirish paytida jimgina
# Argon2 ga ko'chirish uchun.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------------------------------------------------------------
# Til va vaqt
# --------------------------------------------------------------------------
LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("uz", "O'zbekcha"),
    ("ru", "Русский"),
    ("en", "English"),
]
DEFAULT_LANGUAGE = "uz"
SUPPORTED_LANGUAGES = [code for code, _ in LANGUAGES]
LOCALE_PATHS = [BASE_DIR / "locale"]

# --------------------------------------------------------------------------
# Statik va media
# --------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# --------------------------------------------------------------------------
# REST Framework
# --------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 24,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "120/min",
        "user": "300/min",
        "login": "5/min",
        "register": "3/hour",
        "otp": "5/hour",
        "search": "60/min",
        "product_create": "10/day",
        "media_upload": "30/hour",
        "phone_reveal": "30/hour",
        "report": "10/day",
    },
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
}

# --------------------------------------------------------------------------
# JWT
# --------------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=15)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS", default=7)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env("JWT_SECRET", default=SECRET_KEY),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_OBTAIN_SERIALIZER": "apps.accounts.serializers.LoginSerializer",
}

# Refresh token httpOnly cookie'da saqlanadi (XSS himoyasi)
REFRESH_COOKIE_NAME = "ctsale_refresh"
REFRESH_COOKIE_PATH = "/api/v1/auth/"
REFRESH_COOKIE_SAMESITE = env("REFRESH_COOKIE_SAMESITE", default="Lax")
REFRESH_COOKIE_SECURE = env.bool("REFRESH_COOKIE_SECURE", default=False)

# --------------------------------------------------------------------------
# CORS
# --------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"])
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["http://localhost:5173"])

# --------------------------------------------------------------------------
# OpenAPI
# --------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "CT Sale API",
    "DESCRIPTION": "IT texnika marketplace REST API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api/v1",
}

# --------------------------------------------------------------------------
# Celery
# --------------------------------------------------------------------------
CELERY_BROKER_URL = env("REDIS_URL", default="redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://127.0.0.1:6379/1")
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300
CELERY_TASK_SOFT_TIME_LIMIT = 240
# Redis bo'lmasa vazifalar sinxron bajariladi — dev muhiti to'xtab qolmaydi.
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_EAGER_PROPAGATES = False

# --------------------------------------------------------------------------
# Cache
# --------------------------------------------------------------------------
if env.bool("USE_REDIS_CACHE", default=False):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": env("REDIS_URL", default="redis://127.0.0.1:6379/2"),
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "ctsale-locmem",
        }
    }

# --------------------------------------------------------------------------
# Media limitlari (Phase 7)
# --------------------------------------------------------------------------
MAX_IMAGES_PER_PRODUCT = env.int("MAX_IMAGES_PER_PRODUCT", default=10)
MAX_VIDEOS_PER_PRODUCT = env.int("MAX_VIDEOS_PER_PRODUCT", default=2)
MAX_IMAGE_SIZE_MB = env.int("MAX_IMAGE_SIZE_MB", default=10)
MAX_VIDEO_SIZE_MB = env.int("MAX_VIDEO_SIZE_MB", default=50)
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/webm"]
IMAGE_SIZES = {"thumb": 300, "medium": 800, "large": 1600}

DATA_UPLOAD_MAX_MEMORY_SIZE = 55 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# --------------------------------------------------------------------------
# Biznes qoidalari
# --------------------------------------------------------------------------
PRODUCT_EXPIRY_DAYS = env.int("PRODUCT_EXPIRY_DAYS", default=30)
OTP_TTL_SECONDS = env.int("OTP_TTL_SECONDS", default=300)
OTP_MAX_ATTEMPTS = env.int("OTP_MAX_ATTEMPTS", default=5)
PRODUCT_VIEW_TTL_HOURS = 24

# --------------------------------------------------------------------------
# Telegram
# --------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_CHANNEL_ID = env("TELEGRAM_CHANNEL_ID", default="")
TELEGRAM_WEBHOOK_SECRET = env("TELEGRAM_WEBHOOK_SECRET", default="")
# Token yoki kanal bo'lmasa avtomatik mock rejimga o'tadi (telegrambot/client.py).
TELEGRAM_MOCK = env.bool("TELEGRAM_MOCK", default=False)
TELEGRAM_API_TIMEOUT = 20

# --------------------------------------------------------------------------
# SEO
# --------------------------------------------------------------------------
# Qidiruv tizimi tasdiqlash kodlari hech qachon kodga yozilmaydi — .env
# yoki admin paneldagi SeoSettings orqali beriladi.
GOOGLE_SITE_VERIFICATION = env("GOOGLE_SITE_VERIFICATION", default="")
YANDEX_VERIFICATION = env("YANDEX_VERIFICATION", default="")
BING_VERIFICATION = env("BING_VERIFICATION", default="")

# Indekslashga umumiy ruxsat. Staging serverda False qilinadi —
# aks holda test nusxasi Google indeksiga tushib, asosiy saytga
# duplicate content sifatida zarar yetkazadi.
SEO_ALLOW_INDEXING = env.bool("SEO_ALLOW_INDEXING", default=True)
SITEMAP_PAGE_SIZE = env.int("SITEMAP_PAGE_SIZE", default=5000)
SITEMAP_CACHE_SECONDS = env.int("SITEMAP_CACHE_SECONDS", default=1800)

# --------------------------------------------------------------------------
# Xavfsizlik headerlari (apps/core/middleware.py)
# --------------------------------------------------------------------------
# Content-Security-Policy. Frontend alohida domenda ishlaganda bu
# siyosat Django javoblariga (API, sitemap, robots, django-admin)
# tegishli bo'ladi.
CSP_DIRECTIVES = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "'unsafe-inline'"],
    "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
    "font-src": ["'self'", "https://fonts.gstatic.com", "data:"],
    "img-src": ["'self'", "data:", "blob:", "https:"],
    "media-src": ["'self'", "blob:", "https:"],
    "connect-src": ["'self'"] + env.list("CSP_CONNECT_SRC", default=[]),
    "frame-ancestors": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
    "object-src": ["'none'"],
}
CSP_REPORT_ONLY = env.bool("CSP_REPORT_ONLY", default=False)

PERMISSIONS_POLICY = "geolocation=(), microphone=(), camera=(), payment=(), usb=()"

# --------------------------------------------------------------------------
# Email
# --------------------------------------------------------------------------
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="CT Sale <noreply@ctsale.uz>")

# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}:{lineno} — {message}",
            "style": "{",
        },
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "ctsale.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
    },
    "root": {"handlers": ["console", "file"], "level": "INFO"},
    "loggers": {
        "django.db.backends": {"level": "WARNING", "propagate": True},
        "apps": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": False},
    },
}
