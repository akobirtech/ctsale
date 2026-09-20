"""Fayl yuklash validatsiyasi.

Uch qatlamli tekshiruv, chunki har biri alohida aldanishi mumkin:
  1. Kengaytma  — foydalanuvchi o'zgartira oladi
  2. MIME turi  — brauzer yuboradi, soxtalashtirish oson
  3. Magic bytes — faylning haqiqiy mazmuni, eng ishonchli qatlam
"""

from django.conf import settings
from django.core.exceptions import ValidationError

# Fayl boshidagi imzolar (magic bytes)
IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
}
# WebP va AVIF imzosi offset bilan tekshiriladi (RIFF....WEBP / ....ftyp)
RIFF_PREFIX = b"RIFF"
WEBP_MARKER = b"WEBP"
FTYP_MARKER = b"ftyp"

VIDEO_FTYP_BRANDS = {b"isom", b"iso2", b"mp41", b"mp42", b"avc1", b"M4V ", b"mmp4"}
WEBM_SIGNATURE = b"\x1a\x45\xdf\xa3"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".webm"}


def _extension(filename):
    import os

    return os.path.splitext(str(filename or ""))[1].lower()


def _human_size(megabytes):
    return f"{megabytes} MB"


def detect_image_type(header):
    """Fayl boshidan haqiqiy rasm turini aniqlaydi."""
    for signature, mime in IMAGE_SIGNATURES.items():
        if header.startswith(signature):
            return mime
    if header[:4] == RIFF_PREFIX and header[8:12] == WEBP_MARKER:
        return "image/webp"
    if header[4:8] == FTYP_MARKER and b"avif" in header[8:20]:
        return "image/avif"
    return None


def detect_video_type(header):
    if header.startswith(WEBM_SIGNATURE):
        return "video/webm"
    if header[4:8] == FTYP_MARKER:
        brand = header[8:12]
        if brand in VIDEO_FTYP_BRANDS or brand.startswith(b"mp4"):
            return "video/mp4"
    return None


def validate_image(uploaded_file):
    """Rasmni tekshiradi. Xato bo'lsa nima qilish kerakligini aytadi."""
    max_mb = settings.MAX_IMAGE_SIZE_MB

    extension = _extension(uploaded_file.name)
    if extension not in IMAGE_EXTENSIONS:
        raise ValidationError(
            f"«{extension or 'noma\'lum'}» turidagi fayl qabul qilinmaydi. "
            f"JPG, PNG yoki WebP formatidagi rasm yuklang."
        )

    if uploaded_file.size > max_mb * 1024 * 1024:
        actual = uploaded_file.size / (1024 * 1024)
        raise ValidationError(
            f"Rasm hajmi {_human_size(max_mb)} dan oshmasligi kerak "
            f"(yuborilgan fayl: {actual:.1f} MB). Rasmni siqib qaytadan urinib ko'ring."
        )

    if uploaded_file.size == 0:
        raise ValidationError("Yuborilgan fayl bo'sh.")

    header = uploaded_file.read(32)
    uploaded_file.seek(0)

    detected = detect_image_type(header)
    if detected is None:
        raise ValidationError(
            "Fayl haqiqiy rasm emas yoki buzilgan. Boshqa fayl tanlang."
        )
    if detected not in settings.ALLOWED_IMAGE_TYPES:
        raise ValidationError(
            f"«{detected}» formati qo'llab-quvvatlanmaydi. JPG, PNG yoki WebP yuklang."
        )

    # Pillow bilan ochib ko'ramiz: "rasm ko'rinishidagi" buzuq
    # fayllar shu bosqichda aniqlanadi.
    try:
        from PIL import Image

        image = Image.open(uploaded_file)
        image.verify()
        uploaded_file.seek(0)
        width, height = Image.open(uploaded_file).size
        uploaded_file.seek(0)
    except Exception as exc:
        raise ValidationError(
            "Rasmni o'qib bo'lmadi — fayl buzilgan bo'lishi mumkin."
        ) from exc

    if width < 200 or height < 200:
        raise ValidationError(
            f"Rasm juda kichik ({width}x{height}). Kamida 200x200 piksel bo'lsin."
        )
    if width > 12000 or height > 12000:
        raise ValidationError(
            f"Rasm juda katta ({width}x{height}). Eng ko'pi 12000 piksel."
        )

    return {"mime": detected, "width": width, "height": height}


def validate_video(uploaded_file):
    max_mb = settings.MAX_VIDEO_SIZE_MB

    extension = _extension(uploaded_file.name)
    if extension not in VIDEO_EXTENSIONS:
        raise ValidationError(
            f"«{extension or 'noma\'lum'}» turidagi fayl qabul qilinmaydi. "
            f"MP4 yoki WebM formatidagi video yuklang."
        )

    if uploaded_file.size > max_mb * 1024 * 1024:
        actual = uploaded_file.size / (1024 * 1024)
        raise ValidationError(
            f"Video hajmi {_human_size(max_mb)} dan oshmasligi kerak "
            f"(yuborilgan fayl: {actual:.1f} MB). Videoni qisqartiring yoki sifatini pasaytiring."
        )

    if uploaded_file.size == 0:
        raise ValidationError("Yuborilgan fayl bo'sh.")

    header = uploaded_file.read(32)
    uploaded_file.seek(0)

    detected = detect_video_type(header)
    if detected is None:
        raise ValidationError(
            "Fayl haqiqiy video emas yoki buzilgan. MP4 yoki WebM fayl tanlang."
        )
    if detected not in settings.ALLOWED_VIDEO_TYPES:
        raise ValidationError(f"«{detected}» formati qo'llab-quvvatlanmaydi.")

    return {"mime": detected}


def check_image_limit(product):
    limit = settings.MAX_IMAGES_PER_PRODUCT
    current = product.images.count()
    if current >= limit:
        raise ValidationError(
            f"Bitta e'longa eng ko'pi {limit} ta rasm yuklash mumkin. "
            f"Yangi rasm qo'shish uchun avval eskilaridan birini o'chiring."
        )
    return limit - current


def check_video_limit(product):
    limit = settings.MAX_VIDEOS_PER_PRODUCT
    current = product.videos.count()
    if current >= limit:
        raise ValidationError(
            f"Bitta e'longa eng ko'pi {limit} ta video yuklash mumkin."
        )
    return limit - current
