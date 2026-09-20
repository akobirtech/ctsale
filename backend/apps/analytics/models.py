"""Audit jurnali va kunlik statistika."""

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class AuditAction(models.TextChoices):
    CREATE = "create", "Yaratildi"
    UPDATE = "update", "O'zgartirildi"
    DELETE = "delete", "O'chirildi"
    RESTORE = "restore", "Tiklandi"
    APPROVE = "approve", "Tasdiqlandi"
    REJECT = "reject", "Rad etildi"
    LOGIN = "login", "Tizimga kirdi"
    LOGIN_FAILED = "login_failed", "Kirish muvaffaqiyatsiz"
    LOGOUT = "logout", "Tizimdan chiqdi"
    BAN = "ban", "Bloklandi"
    UNBAN = "unban", "Blokdan chiqarildi"
    ROLE_CHANGE = "role_change", "Rol o'zgartirildi"
    TELEGRAM_PUBLISH = "telegram_publish", "Telegramga joylandi"
    TELEGRAM_DELETE = "telegram_delete", "Telegramdan o'chirildi"
    SETTINGS_CHANGE = "settings_change", "Sozlama o'zgartirildi"
    EXPORT = "export", "Ma'lumot eksport qilindi"


class AuditLog(models.Model):
    """Kim, nima qildi, qachon, qayerdan.

    O'zgartirib bo'lmaydigan jurnal: faqat yoziladi va o'qiladi.
    """

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="kim",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    actor_label = models.CharField(
        "kim (matn)",
        max_length=120,
        blank=True,
        help_text="Foydalanuvchi o'chirilsa ham kim ekani ma'lum qolsin.",
    )
    action = models.CharField("harakat", max_length=30, choices=AuditAction.choices, db_index=True)

    # Qaysi obyekt ustida — generic, FK'siz (obyekt o'chsa ham log qoladi).
    target_type = models.CharField("obyekt turi", max_length=60, blank=True, db_index=True)
    target_id = models.CharField("obyekt ID", max_length=64, blank=True, db_index=True)
    target_label = models.CharField("obyekt nomi", max_length=200, blank=True)

    changes = models.JSONField(
        "o'zgarishlar", default=dict, blank=True, help_text="{maydon: [eski, yangi]}"
    )
    note = models.CharField("izoh", max_length=255, blank=True)

    ip_address = models.GenericIPAddressField("IP", null=True, blank=True)
    user_agent = models.CharField("User-Agent", max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "audit yozuvi"
        verbose_name_plural = "audit jurnali"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor", "-created_at"], name="audit_actor_idx"),
            models.Index(fields=["target_type", "target_id"], name="audit_target_idx"),
            models.Index(fields=["action", "-created_at"], name="audit_action_idx"),
        ]

    def __str__(self):
        return f"{self.actor_label or 'tizim'} — {self.get_action_display()}"


class DailyStat(TimeStampedModel):
    """Kunlik yig'ma ko'rsatkichlar.

    Dashboard har safar million qatorni sanamasligi uchun kechasi
    Celery task bu jadvalni to'ldiradi.
    """

    date = models.DateField("sana", unique=True)

    new_users = models.PositiveIntegerField("yangi foydalanuvchilar", default=0)
    new_products = models.PositiveIntegerField("yangi e'lonlar", default=0)
    approved_products = models.PositiveIntegerField("tasdiqlangan", default=0)
    rejected_products = models.PositiveIntegerField("rad etilgan", default=0)
    sold_products = models.PositiveIntegerField("sotilgan", default=0)
    total_views = models.PositiveIntegerField("ko'rishlar", default=0)
    total_favorites = models.PositiveIntegerField("sevimlilar", default=0)
    phone_reveals = models.PositiveIntegerField("telefon ochilishi", default=0)
    telegram_posts = models.PositiveIntegerField("Telegram postlar", default=0)
    reports = models.PositiveIntegerField("shikoyatlar", default=0)

    class Meta:
        verbose_name = "kunlik statistika"
        verbose_name_plural = "kunlik statistika"
        ordering = ["-date"]

    def __str__(self):
        return str(self.date)
