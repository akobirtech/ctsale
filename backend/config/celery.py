"""Celery ilovasi.

Redis mavjud bo'lmasa .env dagi CELERY_TASK_ALWAYS_EAGER=True bilan
vazifalar sinxron bajariladi — development to'xtab qolmaydi.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("ctsale")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    return f"Request: {self.request!r}"
