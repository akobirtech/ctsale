"""Mahsulot media fayllari.

Original fayl saqlanadi, optimallashtirilgan variantlar Celery orqali
fonda yaratiladi (apps/mediafiles/tasks.py). Shu sababli yuklash
so'rovi tez tugaydi va foydalanuvchi kutib qolmaydi.
"""

from django.db import models

from apps.core.models import TimeStampedModel
from apps.core.utils import build_media_path


def _product_slug(instance):
    """Fayl nomi uchun mahsulot slug'i — rasm SEO talabi (#17).

    Natija: gigabyte-rtx-5060-ti-16gb-a7f3c1.webp
    """
    product = getattr(instance, "product", None)
    return getattr(product, "slug", None) or "product"


def product_image_path(instance, filename):
    return build_media_path(
        "products", instance.product_id, "images", filename, _product_slug(instance)
    )


def product_video_path(instance, filename):
    return build_media_path(
        "products", instance.product_id, "videos", filename, _product_slug(instance)
    )


def product_poster_path(instance, filename):
    return build_media_path(
        "products",
        instance.product_id,
        "posters",
        filename,
        f"{_product_slug(instance)}-poster",
    )


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(
        "products.Product", verbose_name="mahsulot", on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField("rasm", upload_to=product_image_path)

    # Optimallashtirilgan variantlar (Celery yaratadi)
    thumb = models.ImageField("kichik (300px)", upload_to=product_image_path, blank=True)
    medium = models.ImageField("o'rta (800px)", upload_to=product_image_path, blank=True)
    large = models.ImageField("katta (1600px)", upload_to=product_image_path, blank=True)

    alt_text = models.CharField("alt matn", max_length=200, blank=True)
    is_primary = models.BooleanField("asosiy rasm", default=False)
    order = models.PositiveSmallIntegerField("tartib", default=0)

    width = models.PositiveIntegerField("eni", null=True, blank=True)
    height = models.PositiveIntegerField("bo'yi", null=True, blank=True)
    file_size = models.PositiveIntegerField("hajmi (bayt)", default=0)
    is_processed = models.BooleanField("qayta ishlangan", default=False)
    processing_error = models.CharField("qayta ishlash xatosi", max_length=255, blank=True)

    class Meta:
        verbose_name = "mahsulot rasmi"
        verbose_name_plural = "mahsulot rasmlari"
        ordering = ["order", "created_at"]
        indexes = [models.Index(fields=["product", "order"])]
        constraints = [
            # Bitta mahsulotda faqat bitta asosiy rasm bo'lishi mumkin.
            models.UniqueConstraint(
                fields=["product"],
                condition=models.Q(is_primary=True),
                name="uniq_primary_image_per_product",
            )
        ]

    def __str__(self):
        return f"{self.product_id} / rasm #{self.order}"

    @property
    def display_url(self):
        """Ro'yxatlarda medium, bo'lmasa original."""
        target = self.medium or self.image
        return target.url if target else ""

    @property
    def thumb_url(self):
        target = self.thumb or self.medium or self.image
        return target.url if target else ""


class ProductVideo(TimeStampedModel):
    product = models.ForeignKey(
        "products.Product", verbose_name="mahsulot", on_delete=models.CASCADE, related_name="videos"
    )
    video = models.FileField("video", upload_to=product_video_path)
    poster = models.ImageField("poster", upload_to=product_poster_path, blank=True)

    title = models.CharField("sarlavha", max_length=150, blank=True)
    order = models.PositiveSmallIntegerField("tartib", default=0)

    duration_seconds = models.PositiveIntegerField("davomiylik (sek)", null=True, blank=True)
    file_size = models.PositiveIntegerField("hajmi (bayt)", default=0)
    mime_type = models.CharField("MIME turi", max_length=60, blank=True)
    is_processed = models.BooleanField("qayta ishlangan", default=False)
    processing_error = models.CharField("qayta ishlash xatosi", max_length=255, blank=True)

    class Meta:
        verbose_name = "mahsulot videosi"
        verbose_name_plural = "mahsulot videolari"
        ordering = ["order", "created_at"]
        indexes = [models.Index(fields=["product", "order"])]

    def __str__(self):
        return f"{self.product_id} / video #{self.order}"
