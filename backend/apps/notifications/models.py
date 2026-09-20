"""Bildirishnomalar: sayt ichi + Telegram + Email."""

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class NotificationType(models.TextChoices):
    PRODUCT_APPROVED = "product_approved", "E'lon tasdiqlandi"
    PRODUCT_REJECTED = "product_rejected", "E'lon rad etildi"
    PRODUCT_EXPIRING = "product_expiring", "E'lon muddati tugayapti"
    PRODUCT_EXPIRED = "product_expired", "E'lon muddati tugadi"
    PRODUCT_SOLD = "product_sold", "E'lon sotilgan deb belgilandi"
    PRODUCT_REPORTED = "product_reported", "E'longa shikoyat tushdi"
    SELLER_VERIFIED = "seller_verified", "Sotuvchi tasdiqlandi"
    TELEGRAM_PUBLISHED = "telegram_published", "Telegram kanalga joylandi"
    TELEGRAM_FAILED = "telegram_failed", "Telegramga joylashda xatolik"
    SAVED_SEARCH_MATCH = "saved_search_match", "Saqlangan qidiruvga mos e'lon"
    ACCOUNT_BANNED = "account_banned", "Hisob bloklandi"
    SYSTEM = "system", "Tizim xabari"


class NotificationChannel(models.TextChoices):
    IN_APP = "in_app", "Saytda"
    TELEGRAM = "telegram", "Telegram"
    EMAIL = "email", "Email"
    SMS = "sms", "SMS"


class Notification(TimeStampedModel):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="qabul qiluvchi",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField("turi", max_length=30, choices=NotificationType.choices)
    title = models.CharField("sarlavha", max_length=200)
    body = models.TextField("matn", max_length=1000, blank=True)

    # Bosilganda qayerga o'tish kerakligi (frontend marshruti).
    link = models.CharField("havola", max_length=300, blank=True)
    payload = models.JSONField("qo'shimcha ma'lumot", default=dict, blank=True)

    is_read = models.BooleanField("o'qilgan", default=False)
    read_at = models.DateTimeField("o'qilgan vaqt", null=True, blank=True)

    # Qaysi kanallarga yetkazilgani
    sent_channels = models.JSONField("yuborilgan kanallar", default=list, blank=True)

    class Meta:
        verbose_name = "bildirishnoma"
        verbose_name_plural = "bildirishnomalar"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"], name="notif_inbox_idx"),
        ]

    def __str__(self):
        return f"{self.recipient} — {self.title}"


class NotificationPreference(TimeStampedModel):
    """Foydalanuvchi qaysi kanaldan xabar olishni xohlaydi."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="foydalanuvchi",
        on_delete=models.CASCADE,
        related_name="notification_preference",
    )
    in_app_enabled = models.BooleanField("saytda", default=True)
    telegram_enabled = models.BooleanField("Telegram", default=True)
    email_enabled = models.BooleanField("Email", default=False)

    # Marketing xabarlari alohida — huquqiy jihatdan ham to'g'ri.
    marketing_enabled = models.BooleanField("yangiliklar va takliflar", default=False)

    class Meta:
        verbose_name = "bildirishnoma sozlamasi"
        verbose_name_plural = "bildirishnoma sozlamalari"

    def __str__(self):
        return str(self.user)

    def enabled_channels(self):
        channels = []
        if self.in_app_enabled:
            channels.append(NotificationChannel.IN_APP)
        if self.telegram_enabled and self.user.telegram_id:
            channels.append(NotificationChannel.TELEGRAM)
        if self.email_enabled and self.user.email:
            channels.append(NotificationChannel.EMAIL)
        return channels
