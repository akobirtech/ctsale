"""Telegram Celery tasklari.

Redis bo'lmasa CELERY_TASK_ALWAYS_EAGER=True bilan bular sinxron
bajariladi — bunda `retry` ishlamaydi, shuning uchun xato yutib
yuboriladi va TelegramPost `failed` holatida qoladi. Admin panelidan
qayta yuborish mumkin.
"""

import logging

from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)

# 1 daqiqa -> 5 daqiqa -> 15 daqiqa
RETRY_DELAYS = [60, 300, 900]


@shared_task(bind=True, max_retries=len(RETRY_DELAYS))
def publish_product_to_telegram(self, product_id):
    from apps.products.models import Product, ProductStatus

    from .client import TelegramError
    from .models import TelegramSettings
    from .services import publish_product

    product = (
        Product.objects.filter(pk=product_id)
        .select_related("seller", "category", "brand", "region", "district")
        .prefetch_related("images", "videos")
        .first()
    )
    if product is None:
        logger.warning("Telegram: mahsulot topilmadi (%s)", product_id)
        return "not_found"

    if product.status != ProductStatus.APPROVED:
        logger.info("Telegram: %s tasdiqlangan holatda emas, o'tkazib yuborildi", product_id)
        return "skipped_status"

    config = TelegramSettings.load()
    if not config.auto_publish:
        logger.info("Telegram: avtomatik joylash o'chirilgan")
        return "skipped_auto"

    try:
        post = publish_product(product, config=config)
    except TelegramError as exc:
        if settings.CELERY_TASK_ALWAYS_EAGER:
            logger.error("Telegram posti yuborilmadi (EAGER rejim): %s", exc)
            return "failed"
        countdown = RETRY_DELAYS[min(self.request.retries, len(RETRY_DELAYS) - 1)]
        _bump_retry_count(product_id)
        raise self.retry(exc=exc, countdown=countdown) from exc

    return post.status


def _bump_retry_count(product_id):
    from django.db.models import F

    from .models import TelegramPost

    latest = TelegramPost.objects.filter(product_id=product_id).order_by("-created_at").first()
    if latest:
        TelegramPost.objects.filter(pk=latest.pk).update(retry_count=F("retry_count") + 1)


@shared_task
def mark_telegram_post_sold(product_id):
    from apps.products.models import Product

    from .services import mark_post_sold

    product = Product.all_objects.filter(pk=product_id).first()
    if product is None:
        return "not_found"
    post = mark_post_sold(product)
    return "updated" if post else "no_post"


@shared_task
def republish_product(post_id):
    """Admin panelidan qayta yuborish."""
    from .models import TelegramPost

    post = TelegramPost.objects.filter(pk=post_id).select_related("product").first()
    if post is None:
        return "not_found"
    return publish_product_to_telegram(str(post.product_id))
