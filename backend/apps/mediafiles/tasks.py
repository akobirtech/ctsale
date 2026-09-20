"""Rasm optimizatsiyasi (Celery).

Yuklash so'rovi tez tugashi uchun og'ir ish shu yerga ko'chirilgan.
EAGER rejimda sinxron bajariladi — dev muhitida ham natija bir xil.
"""

import io
import logging

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

# WebP sifati: 82 — ko'z bilan farq sezilmaydigan, lekin hajmi
# JPEG'dan ~30% kichik bo'ladigan nuqta.
WEBP_QUALITY = 82


@shared_task
def process_product_image(image_id):
    from PIL import Image, ImageOps

    from .models import ProductImage

    instance = ProductImage.objects.filter(pk=image_id).select_related("product").first()
    if instance is None:
        return "not_found"

    try:
        instance.image.open("rb")
        source = Image.open(instance.image)

        # EXIF orientatsiyasini qo'llab, metama'lumotni tashlaymiz:
        # telefon rasmlarida GPS koordinatalari bo'lishi mumkin.
        source = ImageOps.exif_transpose(source)
        if source.mode in ("RGBA", "LA", "P"):
            source = source.convert("RGBA")
            background = Image.new("RGB", source.size, (255, 255, 255))
            background.paste(source, mask=source.split()[-1] if source.mode == "RGBA" else None)
            source = background
        else:
            source = source.convert("RGB")

        instance.width, instance.height = source.size

        base_name = _base_name(instance)
        for label, max_side in settings.IMAGE_SIZES.items():
            variant = _resize(source, max_side)
            buffer = io.BytesIO()
            variant.save(buffer, format="WEBP", quality=WEBP_QUALITY, method=4)
            buffer.seek(0)
            getattr(instance, label).save(
                f"{base_name}-{label}.webp", ContentFile(buffer.read()), save=False
            )

        instance.is_processed = True
        instance.processing_error = ""
        instance.save()
        return "processed"

    except Exception as exc:
        logger.exception("Rasmni qayta ishlab bo'lmadi (%s)", image_id)
        # Original rasm baribir ko'rsatiladi — foydalanuvchi uchun
        # e'lon ishlayveradi, faqat optimizatsiya bo'lmaydi.
        ProductImage.objects.filter(pk=image_id).update(
            processing_error=str(exc)[:255], is_processed=False
        )
        return "failed"
    finally:
        try:
            instance.image.close()
        except Exception:
            pass


def _base_name(instance):
    import os

    name = os.path.basename(instance.image.name)
    return os.path.splitext(name)[0]


def _resize(image, max_side):
    """Nisbatni saqlab kichraytiradi. Kattalashtirilmaydi."""
    from PIL import Image

    width, height = image.size
    if max(width, height) <= max_side:
        return image.copy()
    if width >= height:
        new_size = (max_side, round(height * max_side / width))
    else:
        new_size = (round(width * max_side / height), max_side)
    return image.resize(new_size, Image.LANCZOS)


@shared_task
def cleanup_product_media(paths):
    """O'chirilgan yozuvlarning fayllarini diskdan tozalaydi."""
    from django.core.files.storage import default_storage

    removed = 0
    for path in paths or []:
        try:
            if path and default_storage.exists(path):
                default_storage.delete(path)
                removed += 1
        except Exception:
            logger.warning("Faylni o'chirib bo'lmadi: %s", path, exc_info=True)
    return removed
