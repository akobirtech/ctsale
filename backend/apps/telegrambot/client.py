"""Telegram Bot API klienti.

Token faqat `settings.TELEGRAM_BOT_TOKEN` dan (ya'ni `.env` dan)
o'qiladi — hech qachon bazada, kodda yoki javoblarda ko'rinmaydi.

Token yoki kanal sozlanmagan bo'lsa klient MOCK rejimda ishlaydi:
so'rov yuborilmaydi, lekin butun oqim (shablon, media tanlash,
TelegramPost yozuvi) xuddi haqiqiydek bajariladi.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org/bot{token}/{method}"

# Telegram cheklovlari
MAX_CAPTION_LENGTH = 1024
MAX_MESSAGE_LENGTH = 4096
MAX_MEDIA_GROUP = 10


# Botga keladigan hodisalar. Ro'yxat cheklangan: kanal postlariga
# yozilgan izohlar kabi keraksiz oqim bot jarayonini band qilmasin.
ALLOWED_UPDATES = ["message", "callback_query", "my_chat_member"]


class TelegramError(Exception):
    """Telegram API xato qaytardi yoki javob bermadi."""

    def __init__(self, message, response=None, retryable=True):
        super().__init__(message)
        self.response = response or {}
        self.retryable = retryable


class TelegramClient:
    def __init__(self, token=None, timeout=None):
        self.token = token if token is not None else settings.TELEGRAM_BOT_TOKEN
        self.timeout = timeout or settings.TELEGRAM_API_TIMEOUT

    @property
    def is_mock(self):
        """Sozlanmagan bo'lsa yoki majburan mock yoqilgan bo'lsa."""
        return settings.TELEGRAM_MOCK or not self.token

    # ------------------------------------------------------------------
    def call(self, method, payload=None, files=None):
        if self.is_mock:
            logger.info("[MOCK] Telegram %s: %s", method, _brief(payload))
            return {"ok": True, "result": {"message_id": 0, "mock": True}}

        url = API_BASE.format(token=self.token, method=method)
        try:
            response = requests.post(
                url,
                json=payload if files is None else None,
                data=payload if files is not None else None,
                files=files,
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            raise TelegramError("Telegram javob bermadi (timeout).") from exc
        except requests.RequestException as exc:
            raise TelegramError(f"Telegramga ulanib bo'lmadi: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise TelegramError(
                f"Telegram noto'g'ri javob qaytardi (HTTP {response.status_code})."
            ) from exc

        if not data.get("ok"):
            description = data.get("description", "noma'lum xato")
            # 4xx — so'rovimiz noto'g'ri, qayta urinish yordam bermaydi.
            # 429 va 5xx — vaqtinchalik, qayta urinish mantiqiy.
            retryable = response.status_code == 429 or response.status_code >= 500
            raise TelegramError(
                f"Telegram xatosi: {description}", response=data, retryable=retryable
            )

        return data

    # ------------------------------------------------------------------
    def get_me(self):
        return self.call("getMe")

    def send_message(self, chat_id, text, reply_markup=None, disable_preview=False):
        payload = {
            "chat_id": chat_id,
            "text": text[:MAX_MESSAGE_LENGTH],
            "parse_mode": "HTML",
            "link_preview_options": {"is_disabled": disable_preview},
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self.call("sendMessage", payload)

    def send_photo(self, chat_id, photo_url, caption="", reply_markup=None):
        payload = {
            "chat_id": chat_id,
            "photo": photo_url,
            "caption": caption[:MAX_CAPTION_LENGTH],
            "parse_mode": "HTML",
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self.call("sendPhoto", payload)

    def send_media_group(self, chat_id, media):
        """Bir nechta rasm. Telegram bu usulda reply_markup qabul qilmaydi."""
        return self.call(
            "sendMediaGroup", {"chat_id": chat_id, "media": media[:MAX_MEDIA_GROUP]}
        )

    def send_video(self, chat_id, video_url, caption="", reply_markup=None):
        payload = {
            "chat_id": chat_id,
            "video": video_url,
            "caption": caption[:MAX_CAPTION_LENGTH],
            "parse_mode": "HTML",
            "supports_streaming": True,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self.call("sendVideo", payload)

    def edit_message_caption(self, chat_id, message_id, caption, reply_markup=None):
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "caption": caption[:MAX_CAPTION_LENGTH],
            "parse_mode": "HTML",
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self.call("editMessageCaption", payload)

    def edit_message_text(self, chat_id, message_id, text, reply_markup=None):
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text[:MAX_MESSAGE_LENGTH],
            "parse_mode": "HTML",
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self.call("editMessageText", payload)

    def delete_message(self, chat_id, message_id):
        return self.call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

    def get_chat(self, chat_id):
        return self.call("getChat", {"chat_id": chat_id})

    def set_webhook(self, url, secret_token=""):
        payload = {"url": url, "allowed_updates": ALLOWED_UPDATES}
        if secret_token:
            payload["secret_token"] = secret_token
        return self.call("setWebhook", payload)

    def delete_webhook(self):
        return self.call("deleteWebhook", {"drop_pending_updates": False})

    def get_updates(self, offset=None, timeout=25):
        payload = {"timeout": timeout, "allowed_updates": ALLOWED_UPDATES}
        if offset is not None:
            payload["offset"] = offset
        return self.call("getUpdates", payload)


def _brief(payload):
    """Logda uzun matnlarni qisqartirish."""
    if not isinstance(payload, dict):
        return payload
    return {
        key: (value[:80] + "..." if isinstance(value, str) and len(value) > 80 else value)
        for key, value in payload.items()
    }


def get_client():
    return TelegramClient()
