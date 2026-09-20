"""Mahsulot biznes logikasi: holat o'tishlari, spec validatsiyasi, SEO.

Views bu yerni chaqiradi. Holat o'zgarishi faqat shu funksiyalar
orqali bo'ladi — shunda audit, bildirishnoma va Telegram hech qachon
o'tkazib yuborilmaydi.
"""

import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib.postgres.search import SearchVector
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import AttributeType
from apps.core.exceptions import BusinessError, InvalidStatusTransition

from .models import Product, ProductStatus

logger = logging.getLogger(__name__)

# Shu maydonlar o'zgarsa e'lon qayta moderatsiyaga tushadi: ular
# xaridorning qaroriga bevosita ta'sir qiladi.
MODERATION_SENSITIVE_FIELDS = {
    "title",
    "description",
    "price",
    "currency",
    "condition",
    "category_id",
    "brand_id",
    "specs",
}


# --------------------------------------------------------------------------
# Xususiyat validatsiyasi
# --------------------------------------------------------------------------
def validate_specs(category, specs):
    """`specs` ni kategoriya sxemasiga solishtiradi va tozalaydi.

    Sxemada yo'q kalitlar tashlab yuboriladi — shunda foydalanuvchi
    JSON orqali ixtiyoriy ma'lumot tiqib qo'ya olmaydi.
    """
    specs = specs or {}
    if not isinstance(specs, dict):
        raise BusinessError(
            "Xususiyatlar noto'g'ri formatda yuborildi.", code="invalid_specs"
        )

    definitions = {a.code: a for a in category.inherited_attributes()}
    errors = {}
    cleaned = {}

    for code, definition in definitions.items():
        raw = specs.get(code)
        is_empty = raw is None or raw == "" or raw == []

        if is_empty:
            if definition.is_required:
                errors[code] = f"«{definition.label_uz}» to'ldirilishi shart."
            continue

        try:
            cleaned[code] = _coerce_spec_value(definition, raw)
        except ValueError as exc:
            errors[code] = str(exc)

    unknown = set(specs) - set(definitions)
    if unknown:
        logger.info(
            "Noma'lum xususiyatlar e'tiborsiz qoldirildi (%s): %s",
            category.slug,
            ", ".join(sorted(unknown)),
        )

    if errors:
        raise BusinessError(
            "Xususiyatlarda xatolik bor.", code="invalid_specs", details=errors
        )
    return cleaned


def _coerce_spec_value(definition, raw):
    label = definition.label_uz
    data_type = definition.data_type

    if data_type == AttributeType.BOOLEAN:
        if isinstance(raw, bool):
            return raw
        if str(raw).lower() in ("true", "1", "ha", "yes"):
            return True
        if str(raw).lower() in ("false", "0", "yo'q", "no"):
            return False
        raise ValueError(f"«{label}» uchun ha/yo'q qiymatini tanlang.")

    if data_type in (AttributeType.INTEGER, AttributeType.DECIMAL):
        try:
            value = Decimal(str(raw))
        except (InvalidOperation, ValueError):
            raise ValueError(f"«{label}» uchun son kiriting.") from None
        if data_type == AttributeType.INTEGER:
            if value != value.to_integral_value():
                raise ValueError(f"«{label}» butun son bo'lishi kerak.")
            value = int(value)
        else:
            value = float(value)
        if definition.min_value is not None and Decimal(str(value)) < definition.min_value:
            raise ValueError(f"«{label}» {definition.min_value} dan kam bo'lmasligi kerak.")
        if definition.max_value is not None and Decimal(str(value)) > definition.max_value:
            raise ValueError(f"«{label}» {definition.max_value} dan oshmasligi kerak.")
        return value

    if data_type == AttributeType.SELECT:
        allowed = set(definition.options.values_list("value", flat=True))
        if str(raw) not in allowed:
            raise ValueError(f"«{label}» uchun ro'yxatdagi variantni tanlang.")
        return str(raw)

    if data_type == AttributeType.MULTISELECT:
        if not isinstance(raw, (list, tuple)):
            raise ValueError(f"«{label}» uchun variantlar ro'yxatini yuboring.")
        allowed = set(definition.options.values_list("value", flat=True))
        values = [str(v) for v in raw]
        invalid = set(values) - allowed
        if invalid:
            raise ValueError(f"«{label}» uchun noto'g'ri variant: {', '.join(sorted(invalid))}")
        return values

    text = str(raw).strip()
    if len(text) > 300:
        raise ValueError(f"«{label}» 300 ta belgidan oshmasligi kerak.")
    return text


# --------------------------------------------------------------------------
# SEO
# --------------------------------------------------------------------------
def build_seo_metadata(product):
    """Bo'sh SEO maydonlarini avtomatik to'ldiradi.

    Admin/sotuvchi qo'lda yozgan qiymatlar hech qachon qayta
    yozilmaydi — faqat bo'sh joylar to'ldiriladi.
    """
    site = settings.SITE_NAME
    changed = []

    if not product.seo_title:
        title = f"{product.title} — {site}"
        product.seo_title = title[:200]
        changed.append("seo_title")

    if not product.seo_description:
        condition = product.get_condition_display()
        location = product.region.name_uz if product.region_id else ""
        price = (
            f"{int(product.price):,}".replace(",", " ") + " so'm"
            if product.price
            else "Narxi kelishiladi"
        )
        description = (
            f"{product.title}. {condition}. {price}. {location}. "
            f"Yangi va ishlatilgan kompyuter texnikasini {site} orqali sotib oling."
        )
        product.seo_description = description[:300]
        changed.append("seo_description")

    if not product.og_title:
        product.og_title = product.seo_title[:200]
        changed.append("og_title")

    if not product.og_description:
        product.og_description = product.seo_description[:300]
        changed.append("og_description")

    if not product.seo_keywords:
        parts = [product.title, product.category.name_uz]
        if product.brand_id:
            parts.append(product.brand.name)
        if product.model_name:
            parts.append(product.model_name)
        product.seo_keywords = ", ".join(dict.fromkeys(parts))[:300]
        changed.append("seo_keywords")

    return changed


def update_search_vector(product):
    """Full-text qidiruv vektorini yangilaydi.

    Vazn: A — sarlavha (eng muhim), B — brend/model, C — tavsif.
    """
    Product.all_objects.filter(pk=product.pk).update(
        search_vector=(
            SearchVector("title", weight="A")
            + SearchVector("model_name", weight="B")
            + SearchVector("description", weight="C")
        )
    )


# --------------------------------------------------------------------------
# Holat o'tishlari
# --------------------------------------------------------------------------
def _assert_transition(product, new_status, force=False):
    if force:
        return
    if not product.can_transition_to(new_status):
        current = product.get_status_display()
        target = dict(ProductStatus.choices)[new_status]
        raise InvalidStatusTransition(
            f"E'lonni «{current}» holatidan «{target}» holatiga o'tkazib bo'lmaydi."
        )


@transaction.atomic
def submit_for_moderation(product, actor=None):
    """Sotuvchi e'lonni moderatsiyaga yuboradi."""
    if not product.images.exists():
        raise BusinessError(
            "E'lonni yuborishdan oldin kamida bitta rasm qo'shing.",
            code="images_required",
        )

    _assert_transition(product, ProductStatus.PENDING)
    is_resubmission = product.moderation_tasks.exists()

    product.status = ProductStatus.PENDING
    product.save(update_fields=["status", "updated_at"])

    from apps.moderation.models import ModerationTask

    ModerationTask.objects.create(product=product, is_resubmission=is_resubmission)

    _audit(actor, "update", product, note="Moderatsiyaga yuborildi")
    return product


@transaction.atomic
def approve_product(product, actor, note=""):
    _assert_transition(product, ProductStatus.APPROVED)

    now = timezone.now()
    product.status = ProductStatus.APPROVED
    if product.published_at is None:
        product.published_at = now
    product.expires_at = now + timedelta(days=settings.PRODUCT_EXPIRY_DAYS)
    product.bumped_at = now
    build_seo_metadata(product)
    product.save()
    update_search_vector(product)

    _close_moderation_task(product, actor, approved=True, comment=note)
    _recount_category_and_brand(product)

    from apps.notifications.services import notify

    notify(
        product.seller,
        "product_approved",
        title="E'loningiz tasdiqlandi",
        body=f"«{product.title}» e'loni saytda va Telegram kanalda e'lon qilindi.",
        link=f"/product/{product.slug}",
        payload={"product_id": str(product.id)},
    )

    from apps.telegrambot.tasks import publish_product_to_telegram

    publish_product_to_telegram.delay(str(product.id))

    _audit(actor, "approve", product, note=note)
    return product


@transaction.atomic
def reject_product(product, actor, reason_code, comment="", internal_note=""):
    if not reason_code:
        raise BusinessError(
            "Rad etish sababini ko'rsating.", code="reason_required"
        )
    _assert_transition(product, ProductStatus.REJECTED)

    product.status = ProductStatus.REJECTED
    product.save(update_fields=["status", "updated_at"])

    task = _close_moderation_task(
        product, actor, approved=False, reason_code=reason_code,
        comment=comment, internal_note=internal_note,
    )

    from apps.notifications.services import notify

    notify(
        product.seller,
        "product_rejected",
        title="E'loningiz rad etildi",
        body=f"«{product.title}»: {task.reject_message}",
        link=f"/seller/products/{product.id}/edit",
        payload={"product_id": str(product.id), "reason": reason_code},
    )

    _audit(actor, "reject", product, note=f"{reason_code}: {comment}")
    return product


@transaction.atomic
def mark_as_sold(product, actor=None):
    _assert_transition(product, ProductStatus.SOLD)

    product.status = ProductStatus.SOLD
    product.sold_at = timezone.now()
    product.save(update_fields=["status", "sold_at", "updated_at"])
    _recount_category_and_brand(product)

    # Kanaldagi post "SOTILDI" deb belgilanadi — e'lon o'chirilmaydi,
    # chunki uning SEO va tarixiy qiymati saqlanadi.
    from apps.telegrambot.tasks import mark_telegram_post_sold

    mark_telegram_post_sold.delay(str(product.id))

    _audit(actor, "update", product, note="Sotilgan deb belgilandi")
    return product


@transaction.atomic
def change_status(product, new_status, actor=None, force=False):
    """Umumiy holat o'zgartirish (reserve / archive / restore)."""
    _assert_transition(product, new_status, force=force)

    product.status = new_status
    if new_status == ProductStatus.SOLD and product.sold_at is None:
        product.sold_at = timezone.now()
    product.save(update_fields=["status", "sold_at", "updated_at"])
    _recount_category_and_brand(product)

    _audit(actor, "update", product, note=f"Status: {new_status}")
    return product


@transaction.atomic
def renew_product(product, actor=None):
    """E'lon muddatini uzaytiradi va ro'yxatda yuqoriga ko'taradi."""
    if product.status not in (ProductStatus.APPROVED, ProductStatus.EXPIRED):
        raise BusinessError(
            "Faqat faol yoki muddati tugagan e'lonni uzaytirish mumkin.",
            code="cannot_renew",
        )

    now = timezone.now()
    product.status = ProductStatus.APPROVED
    product.expires_at = now + timedelta(days=settings.PRODUCT_EXPIRY_DAYS)
    product.bumped_at = now
    product.save(update_fields=["status", "expires_at", "bumped_at", "updated_at"])

    _audit(actor, "update", product, note="E'lon uzaytirildi")
    return product


def needs_remoderation(product, changed_fields):
    """Tahrirlash qayta moderatsiya talab qiladimi?"""
    if product.status != ProductStatus.APPROVED:
        return False
    return bool(MODERATION_SENSITIVE_FIELDS & set(changed_fields))


# --------------------------------------------------------------------------
# Yordamchilar
# --------------------------------------------------------------------------
def _close_moderation_task(
    product, actor, approved, reason_code="", comment="", internal_note=""
):
    from apps.moderation.models import ModerationStatus, ModerationTask

    task = (
        ModerationTask.objects.filter(product=product)
        .exclude(status__in=[ModerationStatus.APPROVED, ModerationStatus.REJECTED])
        .order_by("-created_at")
        .first()
    )
    if task is None:
        task = ModerationTask.objects.create(product=product)

    task.status = ModerationStatus.APPROVED if approved else ModerationStatus.REJECTED
    task.assignee = actor
    task.reason_code = reason_code
    task.comment = comment
    task.internal_note = internal_note
    task.reviewed_at = timezone.now()
    task.save()
    return task


def _recount_category_and_brand(product):
    """Denormalizatsiya qilingan hisoblagichlarni yangilaydi."""
    from django.db.models import Count

    from apps.catalog.models import Brand, Category

    category_ids = [c.pk for c in product.category.ancestors(include_self=True)]
    for category_id in category_ids:
        category = Category.objects.filter(pk=category_id).first()
        if category is None:
            continue
        count = Product.objects.filter(
            category_id__in=category.descendant_ids(), status=ProductStatus.APPROVED
        ).count()
        Category.objects.filter(pk=category_id).update(products_count=count)

    if product.brand_id:
        count = Product.objects.filter(
            brand_id=product.brand_id, status=ProductStatus.APPROVED
        ).count()
        Brand.objects.filter(pk=product.brand_id).update(products_count=count)


def _audit(actor, action, product, note=""):
    from apps.analytics.services import log_action

    log_action(
        actor=actor,
        action=action,
        target=product,
        target_label=product.title,
        note=note,
    )
