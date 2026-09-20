"""Umumiy yordamchi funksiyalar."""

import random
import string

from django.utils.text import slugify as django_slugify
from slugify import slugify as unicode_slugify


def make_unique_slug(model_cls, value, instance=None, field="slug", max_length=255):
    """Kirill/lotin matndan takrorlanmas slug yasaydi.

    python-slugify kirillchani transliteratsiya qiladi, shuning uchun
    "Ноутбук ASUS" -> "noutbuk-asus" bo'ladi (bo'sh slug muammosi yo'q).
    """
    base = unicode_slugify(value or "") or django_slugify(value or "") or "item"
    base = base[:max_length - 8].strip("-") or "item"

    queryset = model_cls._default_manager.all()
    if hasattr(model_cls, "all_objects"):
        queryset = model_cls.all_objects.all()
    if instance is not None and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    slug = base
    if not queryset.filter(**{field: slug}).exists():
        return slug

    # Ketma-ket sanash o'rniga qisqa tasodifiy qo'shimcha: raqobatda
    # ikki so'rov bir xil raqamni olib qolmaydi.
    for _ in range(10):
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
        slug = f"{base}-{suffix}"
        if not queryset.filter(**{field: slug}).exists():
            return slug
    raise RuntimeError("Takrorlanmas slug yaratib bo'lmadi")


def get_client_ip(request):
    """Nginx orqasida ham to'g'ri IP."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def normalize_phone(value):
    """+998 XX XXX XX XX -> +998XXXXXXXXX"""
    if not value:
        return value
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if digits.startswith("998"):
        digits = digits[3:]
    digits = digits[-9:]
    return f"+998{digits}"


def format_price(amount, currency="UZS"):
    """12500000 -> '12 500 000 so'm'"""
    if amount is None:
        return "Kelishiladi"
    formatted = f"{int(amount):,}".replace(",", " ")
    suffix = {"UZS": "so'm", "USD": "$"}.get(currency, currency)
    return f"{formatted} {suffix}" if currency != "USD" else f"${formatted}"


def generate_otp_code(length=6):
    return "".join(random.choices(string.digits, k=length))


# --- Fayl nomlari xavfsizligi ---------------------------------------------

# Faqat shu kengaytmalarga ruxsat. Foydalanuvchi yuborgan kengaytma
# ishonchsiz, shuning uchun oq ro'yxatdan tashqarisi qabul qilinmaydi.
SAFE_EXTENSIONS = {
    ".jpg": ".jpg",
    ".jpeg": ".jpg",
    ".png": ".png",
    ".webp": ".webp",
    ".avif": ".avif",
    ".mp4": ".mp4",
    ".webm": ".webm",
}


def safe_media_filename(original_name, base_slug="file", max_base_length=60):
    """Xavfsiz va SEO uchun mazmunli fayl nomi yasaydi.

    "../../etc/passwd.jpg" kabi nom butunlay tashlab yuboriladi: natija
    faqat slug + tasodifiy qism + oq ro'yxatdagi kengaytmadan iborat
    bo'ladi, shuning uchun path traversal imkoni qolmaydi.

        ("IMG_9931.JPEG", "gigabyte-rtx-5060-ti-16gb")
        -> "gigabyte-rtx-5060-ti-16gb-a7f3c1.jpg"
    """
    import os
    import uuid as _uuid

    _, extension = os.path.splitext(str(original_name or ""))
    extension = SAFE_EXTENSIONS.get(extension.lower())
    if extension is None:
        raise ValueError("Bu fayl turi qabul qilinmaydi.")

    base = unicode_slugify(base_slug or "file")[:max_base_length].strip("-") or "file"
    return f"{base}-{_uuid.uuid4().hex[:6]}{extension}"


def build_media_path(folder, owner_id, subfolder, original_name, base_slug):
    """products/<uuid>/images/<xavfsiz-nom> ko'rinishidagi yo'l.

    owner_id UUID bo'lgani uchun ham taxmin qilib bo'lmaydi, ham
    yo'l ichiga foydalanuvchi matni tushmaydi.
    """
    filename = safe_media_filename(original_name, base_slug)
    return f"{folder}/{owner_id}/{subfolder}/{filename}"
