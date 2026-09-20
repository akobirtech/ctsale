"""Foydalanuvchi va mahsulot o'rtasidagi harakatlar:
sevimlilar, ko'rishlar, telefon ochish, shikoyatlar."""

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Favorite(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="foydalanuvchi",
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    product = models.ForeignKey(
        "products.Product",
        verbose_name="mahsulot",
        on_delete=models.CASCADE,
        related_name="favorites",
    )

    class Meta:
        verbose_name = "sevimli"
        verbose_name_plural = "sevimlilar"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "product"], name="uniq_user_favorite")
        ]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"{self.user} -> {self.product_id}"


class ProductView(models.Model):
    """Mahsulot ko'rishlari.

    Bir foydalanuvchi/IP 24 soat ichida qayta ochsa yangi yozuv
    yaratilmaydi — statistika haqiqatga yaqin bo'lishi uchun.
    """

    product = models.ForeignKey(
        "products.Product", on_delete=models.CASCADE, related_name="views"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_views",
    )
    ip_hash = models.CharField(
        "IP hash",
        max_length=64,
        db_index=True,
        help_text="IP ochiq saqlanmaydi — faqat takrorni aniqlash uchun hash.",
    )
    referrer = models.CharField("manba", max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "mahsulot ko'rishi"
        verbose_name_plural = "mahsulot ko'rishlari"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "-created_at"], name="view_product_date_idx"),
            models.Index(fields=["product", "ip_hash", "-created_at"], name="view_dedupe_idx"),
        ]


class PhoneReveal(models.Model):
    """Telefon raqam ochilgani — sotuvchi uchun eng qimmatli metrika."""

    product = models.ForeignKey(
        "products.Product", on_delete=models.CASCADE, related_name="phone_reveals"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="phone_reveals",
    )
    ip_hash = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "telefon ochilishi"
        verbose_name_plural = "telefon ochilishlari"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["product", "-created_at"])]


class ReportReason(models.TextChoices):
    SCAM = "scam", "Firibgarlik"
    FAKE = "fake", "Soxta mahsulot"
    WRONG_INFO = "wrong_info", "Noto'g'ri ma'lumot"
    PROHIBITED = "prohibited", "Taqiqlangan mahsulot"
    DUPLICATE = "duplicate", "Takroriy e'lon"
    OTHER = "other", "Boshqa"


class ReportStatus(models.TextChoices):
    NEW = "new", "Yangi"
    IN_REVIEW = "in_review", "Ko'rib chiqilmoqda"
    RESOLVED = "resolved", "Hal qilindi"
    DISMISSED = "dismissed", "Rad etildi"


class Report(TimeStampedModel):
    product = models.ForeignKey(
        "products.Product",
        verbose_name="mahsulot",
        on_delete=models.CASCADE,
        related_name="reports",
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="shikoyatchi",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports",
    )
    reason = models.CharField("sabab", max_length=20, choices=ReportReason.choices)
    comment = models.TextField("izoh", max_length=1000, blank=True)

    status = models.CharField(
        "status", max_length=20, choices=ReportStatus.choices, default=ReportStatus.NEW
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="hal qilgan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_reports",
    )
    resolution_note = models.TextField("qaror izohi", max_length=1000, blank=True)
    resolved_at = models.DateTimeField("hal qilingan vaqt", null=True, blank=True)

    class Meta:
        verbose_name = "shikoyat"
        verbose_name_plural = "shikoyatlar"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"], name="report_status_idx"),
            models.Index(fields=["product", "-created_at"], name="report_product_idx"),
        ]
        constraints = [
            # Bitta foydalanuvchi bitta e'longa bir marta shikoyat qiladi.
            models.UniqueConstraint(
                fields=["product", "reporter"],
                condition=models.Q(reporter__isnull=False),
                name="uniq_report_per_user_product",
            )
        ]

    def __str__(self):
        return f"{self.product_id} — {self.get_reason_display()}"
