"""Tizim holati endpointlari."""

from django.conf import settings
from django.db import connection
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """Deploy va monitoring uchun: baza ishlayaptimi?"""
    checks = {}

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = "ok"
    except Exception as exc:  # pragma: no cover - faqat baza uzilganda
        checks["database"] = f"error: {exc}"

    checks["telegram_configured"] = bool(
        settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHANNEL_ID
    )

    healthy = checks["database"] == "ok"
    return Response(
        {
            "status": "ok" if healthy else "degraded",
            "service": settings.SITE_NAME,
            "version": "1.0.0",
            "checks": checks,
        },
        status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
    )
