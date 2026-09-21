"""Botni long polling rejimida ishga tushiradi (development uchun).

Productionda webhook ishlatiladi — u tezroq va bitta jarayon
band qilmaydi. Lekin localhost'ga Telegram webhook yubora olmaydi,
shuning uchun ishlab chiqishda shu buyruq kerak:

    python manage.py run_bot

Webhook o'rnatish/o'chirish uchun `--set-webhook` / `--drop-webhook`.
"""

import signal
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.telegrambot.bot import handle_update
from apps.telegrambot.client import TelegramError, get_client

# Telegram uzoq kutishni o'zi qo'llab-quvvatlaydi: so'rov 25 soniyagacha
# ochiq turadi va update kelishi bilan qaytadi. Bu tinimsiz so'rov
# yuborishdan ancha tejamli.
LONG_POLL_TIMEOUT = 25


class Command(BaseCommand):
    help = "Telegram botni long polling rejimida ishga tushiradi."

    def add_arguments(self, parser):
        parser.add_argument(
            "--set-webhook",
            metavar="URL",
            help="Webhook o'rnatadi va chiqadi (masalan https://domain.uz/telegram/webhook/)",
        )
        parser.add_argument(
            "--drop-webhook",
            action="store_true",
            help="Webhookni o'chiradi (long polling uchun shart)",
        )

    def handle(self, *args, **options):
        client = get_client()

        if options["set_webhook"]:
            return self._set_webhook(client, options["set_webhook"])
        if options["drop_webhook"]:
            client.delete_webhook()
            self.stdout.write(self.style.SUCCESS("Webhook o'chirildi."))
            return

        if not settings.TELEGRAM_BOT_TOKEN and not settings.TELEGRAM_MOCK:
            raise CommandError("TELEGRAM_BOT_TOKEN sozlanmagan.")

        # Webhook yoqilgan bo'lsa getUpdates ishlamaydi — Telegram
        # ikkalasini bir vaqtda bermaydi.
        try:
            client.delete_webhook()
        except TelegramError as exc:
            self.stderr.write(f"Webhookni o'chirib bo'lmadi: {exc}")

        self._poll(client)

    def _set_webhook(self, client, url):
        secret = settings.TELEGRAM_WEBHOOK_SECRET
        if not secret:
            raise CommandError(
                "TELEGRAM_WEBHOOK_SECRET bo'sh. Sirsiz webhook ochiq qoladi."
            )
        client.set_webhook(url, secret_token=secret)
        self.stdout.write(self.style.SUCCESS(f"Webhook o'rnatildi: {url}"))

    def _poll(self, client):
        running = {"value": True}

        def stop(*_):
            running["value"] = False

        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)

        # `call()` to'liq konvertni qaytaradi: {"ok": ..., "result": ...}
        me = (client.get_me() or {}).get("result") or {}
        self.stdout.write(
            self.style.SUCCESS(
                f"Bot ishlayapti: @{me.get('username', '?')} (Ctrl+C — to'xtatish)"
            )
        )

        offset = None
        while running["value"]:
            try:
                response = client.get_updates(offset=offset, timeout=LONG_POLL_TIMEOUT)
                updates = (response or {}).get("result")
                # Mock rejimda `result` lug'at bo'ladi — bo'sh deb qaraymiz.
                updates = updates if isinstance(updates, list) else []
            except TelegramError as exc:
                # Tarmoq uzilishi bot to'xtashiga sabab bo'lmasin.
                self.stderr.write(f"getUpdates xatosi: {exc}")
                time.sleep(3)
                continue

            for update in updates or []:
                offset = update["update_id"] + 1
                handle_update(update, client=client)

        self.stdout.write("To'xtatildi.")
