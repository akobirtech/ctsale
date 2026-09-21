"""SEO konfiguratsiyasi, redirectlar va indeksatsiya nazorati.

robots.txt va sitemap.xml statik fayl emas — shu modellar va bazadagi
mahsulotlar asosida dinamik generatsiya qilinadi (apps/seo/views.py).
"""

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel

DEFAULT_DISALLOW = """/admin
/api
/auth
/login
/register
/user
/profile
/favorites
/compare
/notifications
/seller
/search?
"""


class SeoSettings(TimeStampedModel):
    """Admin panelidan boshqariladigan sayt darajasidagi SEO sozlamalari."""

    site_name = models.CharField("sayt nomi", max_length=80, default="CT Sale")
    default_title_template = models.CharField(
        "title shabloni", max_length=160, default="{title} — {site_name}"
    )
    default_description = models.CharField(
        "standart tavsif",
        max_length=300,
        default=(
            "Yangi va ishlatilgan kompyuter texnikasi: noutbuk, videokarta, "
            "protsessor, monitor va komplektuvchilar. CT Sale — IT texnika marketplace."
        ),
    )
    default_og_image = models.ImageField(
        "standart OG rasm", upload_to="seo/", null=True, blank=True
    )

    # Qidiruv tizimlari tasdiqlash kodlari — .env yoki shu yerdan.
    google_site_verification = models.CharField(
        "Google verification", max_length=120, blank=True
    )
    yandex_verification = models.CharField("Yandex verification", max_length=120, blank=True)
    bing_verification = models.CharField("Bing verification", max_length=120, blank=True)

    # Analitika
    google_analytics_id = models.CharField("Google Analytics ID", max_length=40, blank=True)
    yandex_metrika_id = models.CharField("Yandex Metrika ID", max_length=40, blank=True)

    robots_extra_disallow = models.TextField(
        "qo'shimcha Disallow",
        blank=True,
        default=DEFAULT_DISALLOW,
        help_text="Har bir qator — bitta yo'l. robots.txt ga qo'shiladi.",
    )
    robots_allow_indexing = models.BooleanField(
        "indekslashga ruxsat",
        default=True,
        help_text="O'chirilsa butun sayt uchun Disallow: / qaytariladi (staging uchun).",
    )
    sitemap_products_limit = models.PositiveIntegerField(
        "sitemapdagi mahsulotlar chegarasi", default=40000
    )
    index_sold_products = models.BooleanField(
        "sotilgan e'lonlar indekslansin",
        default=True,
        help_text=(
            "Google tavsiyasi: sotilgan mahsulot sahifasini noindex qilmang — "
            "u narx tadqiqoti uchun qimmatli va JSON-LD da SoldOut ko'rsatiladi. "
            "Agar sotilgan e'lonlar juda ko'payib ketsa o'chirib qo'yish mumkin."
        ),
    )

    organization_logo = models.ImageField(
        "tashkilot logotipi", upload_to="seo/", null=True, blank=True
    )
    organization_phone = models.CharField("tashkilot telefoni", max_length=20, blank=True)
    organization_email = models.EmailField("tashkilot emaili", blank=True)
    social_links = models.JSONField(
        "ijtimoiy tarmoqlar", default=list, blank=True, help_text="URL ro'yxati (sameAs)"
    )

    class Meta:
        verbose_name = "SEO sozlamasi"
        verbose_name_plural = "SEO sozlamalari"

    def __str__(self):
        return "SEO sozlamalari"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class RedirectType(models.IntegerChoices):
    PERMANENT = 301, "301 — doimiy"
    TEMPORARY = 302, "302 — vaqtinchalik"
    GONE = 410, "410 — butunlay o'chirilgan"


class SeoRedirect(TimeStampedModel):
    """Eski URL -> yangi URL. Slug o'zgarganda SEO vaznini yo'qotmaslik uchun."""

    old_path = models.CharField(
        "eski yo'l",
        max_length=300,
        unique=True,
        help_text="Til prefiksisiz, masalan: /product/eski-slug",
    )
    new_path = models.CharField(
        "yangi yo'l", max_length=300, blank=True, help_text="410 uchun bo'sh qoldiring"
    )
    status_code = models.PositiveSmallIntegerField(
        "status", choices=RedirectType.choices, default=RedirectType.PERMANENT
    )
    is_active = models.BooleanField("faol", default=True)
    hits = models.PositiveIntegerField("ishlatilgan", default=0)
    note = models.CharField("izoh", max_length=255, blank=True)

    class Meta:
        verbose_name = "redirect"
        verbose_name_plural = "redirectlar"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["old_path", "is_active"])]

    def __str__(self):
        return f"{self.old_path} -> {self.new_path or '410'}"

    def clean(self):
        if self.status_code != RedirectType.GONE and not self.new_path:
            raise ValidationError({"new_path": "301/302 uchun yangi yo'l ko'rsatilishi kerak."})
        if self.new_path and self.new_path == self.old_path:
            raise ValidationError({"new_path": "Yangi yo'l eskisi bilan bir xil bo'lmasligi kerak."})


class StaticPageSeo(TimeStampedModel):
    """Statik sahifalar (bosh sahifa, yordam, shartlar) uchun meta ma'lumot."""

    path = models.CharField(
        "yo'l", max_length=200, unique=True, help_text="Til prefiksisiz, masalan: / yoki /about"
    )

    title_uz = models.CharField("title (uz)", max_length=200, blank=True)
    title_ru = models.CharField("title (ru)", max_length=200, blank=True)
    title_en = models.CharField("title (en)", max_length=200, blank=True)

    description_uz = models.CharField("description (uz)", max_length=300, blank=True)
    description_ru = models.CharField("description (ru)", max_length=300, blank=True)
    description_en = models.CharField("description (en)", max_length=300, blank=True)

    og_image = models.ImageField("OG rasm", upload_to="seo/", null=True, blank=True)
    is_indexable = models.BooleanField("indekslansin", default=True)
    sitemap_priority = models.DecimalField(
        "sitemap ustuvorligi", max_digits=2, decimal_places=1, default=0.5
    )
    changefreq = models.CharField("yangilanish chastotasi", max_length=20, default="weekly")

    class Meta:
        verbose_name = "sahifa SEO"
        verbose_name_plural = "sahifalar SEO"
        ordering = ["path"]

    def __str__(self):
        return self.path
