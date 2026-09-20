"""Telegram bot va kanal integratsiyasi.

Bot token hech qachon bu modellarda saqlanmaydi — faqat .env da.
Bu yerda boshqariladigan narsa: kanal, shablon va publikatsiya tarixi.
"""

from django.db import models

from apps.core.models import TimeStampedModel

DEFAULT_POST_TEMPLATE = """🔥 <b>YANGI MAHSULOT</b>

💻 <b>{title}</b>

💰 Narxi: <b>{price}</b>
📦 Holati: {condition}
{specs_line}📍 {location}

🔗 <a href="{url}">Saytda ko'rish</a>"""


class TelegramSettings(TimeStampedModel):
    """Yagona (singleton) sozlamalar yozuvi.

    Token .env dan o'qiladi; bu yerda faqat undan foydalanish qoidalari.
    """

    channel_id = models.CharField(
        "kanal ID",
        max_length=64,
        blank=True,
        help_text="@kanal_nomi yoki -100xxxxxxxxxx. Bo'sh bo'lsa .env dagi qiymat ishlatiladi.",
    )
    channel_url = models.URLField("kanal havolasi", blank=True)

    auto_publish = models.BooleanField(
        "avtomatik joylash",
        default=True,
        help_text="E'lon tasdiqlangan zahoti kanalga yuborilsin.",
    )
    publish_media = models.BooleanField("media bilan yuborish", default=True)
    publish_video = models.BooleanField("video ham yuborilsin", default=True)
    update_on_sold = models.BooleanField(
        "sotilganda postni yangilash",
        default=True,
        help_text="E'lon sotilgan deb belgilansa, kanaldagi post tahrirlanadi.",
    )

    post_template = models.TextField(
        "post shabloni",
        default=DEFAULT_POST_TEMPLATE,
        help_text=(
            "Mavjud o'zgaruvchilar: {title} {price} {condition} {category} {brand} "
            "{specs_line} {location} {url} {seller} {description}"
        ),
    )
    sold_suffix = models.CharField(
        "sotilgan belgisi", max_length=100, default="\n\n❌ <b>SOTILDI</b>"
    )
    button_text = models.CharField("tugma matni", max_length=64, default="Saytda ko'rish")

    max_specs_in_post = models.PositiveSmallIntegerField("postdagi xususiyatlar soni", default=4)
    is_enabled = models.BooleanField("integratsiya yoqilgan", default=True)

    class Meta:
        verbose_name = "Telegram sozlamasi"
        verbose_name_plural = "Telegram sozlamalari"

    def __str__(self):
        return f"Telegram: {self.channel_id or 'sozlanmagan'}"

    def save(self, *args, **kwargs):
        # Singleton: har doim bitta yozuv.
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class TelegramPostStatus(models.TextChoices):
    PENDING = "pending", "Navbatda"
    PUBLISHED = "published", "Joylandi"
    FAILED = "failed", "Xatolik"
    DELETED = "deleted", "O'chirilgan"
    SKIPPED = "skipped", "O'tkazib yuborilgan"


class TelegramPost(TimeStampedModel):
    """Kanalga yuborilgan (yoki yuborilmoqchi bo'lgan) har bir post."""

    product = models.ForeignKey(
        "products.Product",
        verbose_name="mahsulot",
        on_delete=models.CASCADE,
        related_name="telegram_posts",
    )
    channel_id = models.CharField("kanal", max_length=64, blank=True)
    message_id = models.BigIntegerField("xabar ID", null=True, blank=True)
    # sendMediaGroup bir nechta xabar qaytaradi — barchasini saqlaymiz,
    # aks holda keyinchalik postni o'chirib bo'lmaydi.
    message_ids = models.JSONField("xabar IDlari", default=list, blank=True)

    status = models.CharField(
        "status",
        max_length=20,
        choices=TelegramPostStatus.choices,
        default=TelegramPostStatus.PENDING,
        db_index=True,
    )
    method = models.CharField(
        "usul", max_length=30, blank=True, help_text="sendPhoto / sendMediaGroup / sendVideo"
    )

    rendered_text = models.TextField("yuborilgan matn", blank=True)
    rendered_payload = models.JSONField("so'rov tarkibi", default=dict, blank=True)
    response_payload = models.JSONField("javob", default=dict, blank=True)

    error_message = models.TextField("xato matni", blank=True)
    retry_count = models.PositiveSmallIntegerField("urinishlar", default=0)

    published_at = models.DateTimeField("joylangan vaqt", null=True, blank=True)
    is_mock = models.BooleanField(
        "mock rejim", default=False, help_text="Haqiqatda yuborilmagan (token yo'q edi)."
    )

    class Meta:
        verbose_name = "Telegram post"
        verbose_name_plural = "Telegram postlar"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"], name="tgpost_status_idx"),
            models.Index(fields=["product", "-created_at"], name="tgpost_product_idx"),
        ]

    def __str__(self):
        return f"{self.product_id} — {self.get_status_display()}"

    @property
    def message_url(self):
        """t.me havolasi (faqat public kanal uchun)."""
        if not self.message_id or not self.channel_id.startswith("@"):
            return ""
        return f"https://t.me/{self.channel_id.lstrip('@')}/{self.message_id}"


class TelegramBotUser(TimeStampedModel):
    """Bot bilan muloqot qilgan foydalanuvchilar (bildirishnoma yuborish uchun)."""

    telegram_id = models.BigIntegerField("Telegram ID", unique=True)
    username = models.CharField("username", max_length=64, blank=True)
    first_name = models.CharField("ism", max_length=120, blank=True)
    language_code = models.CharField("til", max_length=8, blank=True)

    user = models.ForeignKey(
        "accounts.User",
        verbose_name="sayt hisobi",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="telegram_accounts",
    )
    link_token = models.CharField(
        "bog'lash kodi", max_length=40, blank=True, help_text="Saytdagi hisobga ulash uchun"
    )

    is_blocked = models.BooleanField("botni bloklagan", default=False)
    last_interaction_at = models.DateTimeField("oxirgi muloqot", null=True, blank=True)
    state = models.JSONField("dialog holati", default=dict, blank=True)

    class Meta:
        verbose_name = "Telegram foydalanuvchisi"
        verbose_name_plural = "Telegram foydalanuvchilari"
        ordering = ["-created_at"]

    def __str__(self):
        return self.username or str(self.telegram_id)
