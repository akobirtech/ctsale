"""Moderatsiya navbati."""

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class ModerationStatus(models.TextChoices):
    PENDING = "pending", "Navbatda"
    IN_REVIEW = "in_review", "Ko'rib chiqilmoqda"
    APPROVED = "approved", "Tasdiqlangan"
    REJECTED = "rejected", "Rad etilgan"


class RejectReasonCode(models.TextChoices):
    WRONG_CATEGORY = "wrong_category", "Noto'g'ri kategoriya tanlangan"
    BAD_PHOTOS = "bad_photos", "Rasmlar sifatsiz yoki mahsulotga tegishli emas"
    PROHIBITED = "prohibited", "Taqiqlangan mahsulot"
    CONTACT_IN_TEXT = "contact_in_text", "Matnda aloqa ma'lumoti ko'rsatilgan"
    SPAM = "spam", "Spam yoki takroriy e'lon"
    WRONG_PRICE = "wrong_price", "Narx haqiqatga to'g'ri kelmaydi"
    INCOMPLETE = "incomplete", "Ma'lumot yetarli emas"
    COPYRIGHT = "copyright", "Boshqa e'londan ko'chirilgan"
    OTHER = "other", "Boshqa sabab"


class ModerationTask(TimeStampedModel):
    """Har bir moderatsiyaga yuborish uchun alohida yozuv.

    Tarix saqlanadi: e'lon bir necha marta rad etilib qayta yuborilsa,
    har bir urinish alohida yozuv bo'ladi.
    """

    product = models.ForeignKey(
        "products.Product",
        verbose_name="mahsulot",
        on_delete=models.CASCADE,
        related_name="moderation_tasks",
    )
    status = models.CharField(
        "status", max_length=20, choices=ModerationStatus.choices, default=ModerationStatus.PENDING
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="moderator",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderation_tasks",
    )

    reason_code = models.CharField(
        "rad etish sababi", max_length=30, choices=RejectReasonCode.choices, blank=True
    )
    comment = models.TextField(
        "izoh", max_length=1000, blank=True, help_text="Sotuvchiga ko'rinadi"
    )
    internal_note = models.TextField(
        "ichki izoh", max_length=1000, blank=True, help_text="Faqat xodimlarga ko'rinadi"
    )

    is_resubmission = models.BooleanField("qayta yuborilgan", default=False)
    reviewed_at = models.DateTimeField("ko'rib chiqilgan vaqt", null=True, blank=True)

    class Meta:
        verbose_name = "moderatsiya vazifasi"
        verbose_name_plural = "moderatsiya vazifalari"
        # `id` tiebreaker sifatida: bir e'lon rad etilib darhol qayta
        # yuborilsa ikki vazifa bir xil vaqt tamg'asini olishi mumkin
        # va tartib tasodifiy bo'lib qolardi.
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="moderation_status_idx"),
            models.Index(fields=["assignee", "status"], name="moderation_assignee_idx"),
            models.Index(fields=["product", "-created_at"], name="moderation_product_idx"),
        ]

    def __str__(self):
        return f"{self.product_id} — {self.get_status_display()}"

    @property
    def reject_message(self):
        """Sotuvchiga ko'rsatiladigan to'liq sabab."""
        parts = []
        if self.reason_code:
            parts.append(self.get_reason_code_display())
        if self.comment:
            parts.append(self.comment)
        return ". ".join(parts) or "Sabab ko'rsatilmagan."
