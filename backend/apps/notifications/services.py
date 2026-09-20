"""Bildirishnoma yaratish va kanallarga yuborish."""

import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import Notification, NotificationChannel, NotificationPreference

logger = logging.getLogger(__name__)


def notify(recipient, notification_type, title, body="", link="", payload=None):
    """Bildirishnoma yaratadi va foydalanuvchi tanlagan kanallarga yuboradi.

    Sayt ichidagi yozuv har doim yaratiladi — tashqi kanal ishlamasa
    ham foydalanuvchi xabarni saytda ko'radi.
    """
    if recipient is None:
        return None

    notification = Notification.objects.create(
        recipient=recipient,
        type=notification_type,
        title=title[:200],
        body=body[:1000],
        link=link[:300],
        payload=payload or {},
        sent_channels=[NotificationChannel.IN_APP],
    )

    preference, _ = NotificationPreference.objects.get_or_create(user=recipient)
    delivered = [NotificationChannel.IN_APP]

    for channel in preference.enabled_channels():
        if channel == NotificationChannel.IN_APP:
            continue
        if _deliver(channel, recipient, notification):
            delivered.append(channel)

    if delivered != notification.sent_channels:
        notification.sent_channels = delivered
        notification.save(update_fields=["sent_channels"])
    return notification


def _deliver(channel, recipient, notification):
    try:
        if channel == NotificationChannel.TELEGRAM:
            from apps.telegrambot.services import send_direct_message

            text = f"<b>{notification.title}</b>"
            if notification.body:
                text += f"\n\n{notification.body}"
            if notification.link:
                text += f"\n\n{settings.FRONTEND_URL}{notification.link}"
            return send_direct_message(recipient.telegram_id, text)

        if channel == NotificationChannel.EMAIL:
            send_mail(
                subject=notification.title,
                message=notification.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            return True
    except Exception:  # pragma: no cover - tashqi servislar
        logger.warning(
            "Bildirishnomani %s orqali yuborib bo'lmadi (user=%s)",
            channel,
            recipient.pk,
            exc_info=True,
        )
    return False


def mark_all_read(user):
    from django.utils import timezone

    return Notification.objects.filter(recipient=user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )
