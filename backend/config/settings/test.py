"""Test sozlamalari — tez va tashqi servislarsiz."""

from .base import *  # noqa: F401,F403

DEBUG = False
TELEGRAM_MOCK = True
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Testlarda throttling xalaqit bermasin.
#
# `DEFAULT_THROTTLE_CLASSES` ni bo'shatish yetarli emas: ayrim view'lar
# o'z `throttle_classes` ini aniq ko'rsatadi. Tezlikni `None` qilish
# esa har qanday throttle'ni ishlamas holga keltiradi.
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = ()  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    scope: None for scope in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]  # noqa: F405
}

LOGGING["root"]["level"] = "ERROR"  # noqa: F405

# Testlar tezroq ishlashi uchun migratsiyalar baribir kerak
# (GIN indekslar va kengaytmalar), lekin media fayllar vaqtinchalik
# papkaga yoziladi — loyiha media/ katalogi iflos bo'lmasin.
import tempfile

MEDIA_ROOT = tempfile.mkdtemp(prefix="ctsale-test-media-")

# Testlarda tashqi tarmoqqa chiqish yo'q.
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHANNEL_ID = "@test_channel"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
