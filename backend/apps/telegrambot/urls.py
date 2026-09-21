"""Telegram yo'llari.

Webhook ataylab `/api/v1/` ostida emas: u Telegram serveri uchun,
brauzer uchun emas — DRF autentifikatsiyasi ham, versiyalash ham
unga tegishli emas.
"""

from django.urls import path

from . import views

app_name = "telegrambot"

urlpatterns = [
    path("telegram/webhook/", views.webhook, name="webhook"),
    path("api/v1/telegram/link-token/", views.link_token, name="link-token"),
]
