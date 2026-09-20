"""Test sozlamalari — tez va tashqi servislarsiz."""

from .base import *  # noqa: F401,F403

DEBUG = False
TELEGRAM_MOCK = True
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Testlarda throttling xalaqit bermasin.
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = ()  # noqa: F405

LOGGING["root"]["level"] = "ERROR"  # noqa: F405
