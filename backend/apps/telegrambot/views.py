"""Telegram webhook va hisobni ulash endpointi."""

import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .bot import handle_update, issue_link_token

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def webhook(request):
    """Telegram yuboradigan update.

    Telegram sessiya ham, CSRF tokeni ham yubormaydi — himoya
    `X-Telegram-Bot-Api-Secret-Token` orqali. Sir sozlanmagan bo'lsa
    endpoint umuman yopiq: ochiq qoldirilsa istalgan odam bot nomidan
    xabar yuborishni boshlay olardi.
    """
    secret = settings.TELEGRAM_WEBHOOK_SECRET
    if not secret:
        logger.warning("Webhook so'rovi keldi, lekin TELEGRAM_WEBHOOK_SECRET bo'sh")
        return HttpResponse(status=403)

    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != secret:
        return HttpResponse(status=403)

    try:
        update = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return HttpResponse(status=400)

    handle_update(update)

    # Telegram javob kodiga qaraydi: 200 bo'lmasa update qayta keladi.
    # Ishlov paytidagi xato `handle_update` ichida yutiladi.
    return JsonResponse({"ok": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def link_token(request):
    """Profil sahifasi uchun: botga ulanish havolasi.

    Token javobda bir marta ko'rsatiladi va 30 daqiqada eskiradi.
    """
    from .services import bot_username

    token = issue_link_token(request.user)
    username = bot_username()

    return Response(
        {
            "token": token,
            "url": f"https://t.me/{username}?start={token}" if username else None,
            "expires_in_minutes": 30,
        }
    )
