"""Yagona xato formati.

Frontend har doim bir xil shaklni oladi, shuning uchun xato ko'rsatish
mantiqi bitta joyda yoziladi:

    {
      "error": {
        "code": "validation_error",
        "message": "Rasm hajmi 10 MB dan oshmasligi kerak.",
        "details": {"image": ["Rasm hajmi 10 MB dan oshmasligi kerak."]}
      }
    }
"""

import logging

from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)

# Texnik kodlarni foydalanuvchi tushunadigan o'zbekcha xabarga aylantiramiz.
DEFAULT_MESSAGES = {
    400: "So'rovda xatolik bor. Maydonlarni tekshirib qaytadan urinib ko'ring.",
    401: "Bu amal uchun tizimga kirishingiz kerak.",
    403: "Sizda bu amalni bajarish uchun ruxsat yo'q.",
    404: "So'ralgan ma'lumot topilmadi.",
    405: "Bu amal qo'llab-quvvatlanmaydi.",
    409: "Ma'lumotlarda ziddiyat bor.",
    413: "Yuborilgan fayl juda katta.",
    415: "Fayl turi qo'llab-quvvatlanmaydi.",
    429: "Juda ko'p so'rov yuborildi. Biroz kutib qaytadan urinib ko'ring.",
    500: "Serverda kutilmagan xatolik yuz berdi. Biroz o'tib qaytadan urinib ko'ring.",
}

CODE_BY_STATUS = {
    400: "validation_error",
    401: "not_authenticated",
    403: "permission_denied",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "payload_too_large",
    415: "unsupported_media_type",
    429: "throttled",
    500: "server_error",
}


class BusinessError(APIException):
    """Biznes qoidasi buzilganda — servis qatlamidan otiladi."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Amalni bajarib bo'lmadi."
    default_code = "business_error"

    def __init__(self, detail=None, code=None, status_code=None, details=None):
        if status_code is not None:
            self.status_code = status_code
        self.error_code = code or self.default_code
        self.details = details or {}
        super().__init__(detail or self.default_detail)


class InvalidStatusTransition(BusinessError):
    default_detail = "Mahsulot holatini bu tartibda o'zgartirib bo'lmaydi."
    default_code = "invalid_status_transition"


def _first_message(data):
    """Ichma-ich joylashgan DRF xatolaridan birinchi o'qiladigan matnni oladi."""
    if isinstance(data, str):
        return data
    if isinstance(data, list) and data:
        return _first_message(data[0])
    if isinstance(data, dict):
        for value in data.values():
            message = _first_message(value)
            if message:
                return message
    return None


def api_exception_handler(exc, context):
    if isinstance(exc, Http404):
        exc = APIException(DEFAULT_MESSAGES[404])
        exc.status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, PermissionDenied):
        exc = APIException(DEFAULT_MESSAGES[403])
        exc.status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, DjangoValidationError):
        exc = APIException(getattr(exc, "messages", [str(exc)]))
        exc.status_code = status.HTTP_400_BAD_REQUEST

    response = drf_exception_handler(exc, context)

    if response is None:
        # Kutilmagan xato: batafsilini logga, foydalanuvchiga umumiy xabar.
        logger.exception("Kutilmagan server xatosi: %s", exc, exc_info=exc)
        return Response(
            {
                "error": {
                    "code": "server_error",
                    "message": DEFAULT_MESSAGES[500],
                    "details": {},
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    code = getattr(exc, "error_code", None) or CODE_BY_STATUS.get(
        response.status_code, "error"
    )
    details = response.data if isinstance(response.data, dict) else {"detail": response.data}
    message = _first_message(response.data) or DEFAULT_MESSAGES.get(
        response.status_code, "Xatolik yuz berdi."
    )

    # SimpleJWT xabarni argument sifatida uzatadi, shuning uchun uning
    # default_detail'ini almashtirish yetarli emas.
    if isinstance(details, dict) and details.get("code") == "token_not_valid":
        code = "token_not_valid"
        message = "Sessiya muddati tugagan. Qaytadan kiring."
        details = {"detail": message}

    # Throttle uchun qancha kutish kerakligini aniq aytamiz.
    wait = getattr(exc, "wait", None)
    if wait:
        message = f"Juda ko'p so'rov yuborildi. {int(wait)} soniyadan keyin urinib ko'ring."
        # DRF o'z matnini ("Expected available in N seconds") qo'shadi —
        # uni almashtiramiz, aks holda javobda ikki til aralashadi.
        details = {"detail": message, "retry_after": int(wait)}

    response.data = {"error": {"code": code, "message": message, "details": details}}
    return response
