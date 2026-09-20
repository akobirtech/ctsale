"""Telegram kanalga post joylash va postni yangilash."""

import html
import logging

from django.conf import settings
from django.utils import timezone

from apps.core.utils import format_price

from .client import MAX_MEDIA_GROUP, TelegramClient, TelegramError, get_client
from .models import TelegramPost, TelegramPostStatus, TelegramSettings

logger = logging.getLogger(__name__)


def _escape(text):
    """Telegram HTML rejimi uchun ekranlash.

    Telegram faqat `<`, `>` va `&` belgilarini talab qiladi.
    `html.escape` standart holatda apostrofni ham `&#x27;` ga
    aylantiradi — o'zbekcha matnda bu juda ko'p uchraydi va
    o'qilishini buzadi.
    """
    return html.escape(str(text or ""), quote=False)


def resolve_channel_id(config=None):
    """Kanal ID: avval admin panelidagi qiymat, keyin `.env`."""
    config = config or TelegramSettings.load()
    return (config.channel_id or settings.TELEGRAM_CHANNEL_ID or "").strip()


def _absolute_media_url(file_field):
    """Telegram uchun tashqaridan ochiladigan to'liq URL.

    Telegram localhost'ga kira olmaydi, shuning uchun dev muhitda
    rasm yuborilmaydi — faqat matn ketadi.
    """
    if not file_field:
        return None
    url = file_field.url
    if url.startswith("http"):
        return url
    base = settings.FRONTEND_URL
    if "localhost" in base or "127.0.0.1" in base:
        return None
    return f"{base}{url}"


def render_post(product, config=None):
    """Shablonni mahsulot ma'lumotlari bilan to'ldiradi."""
    config = config or TelegramSettings.load()

    if product.price_on_request:
        price = "So'rov bo'yicha"
    elif product.price is None:
        price = "Kelishiladi"
    else:
        price = format_price(product.price, product.currency)
        if product.is_negotiable:
            price += " (kelishiladi)"

    location = product.region.name_uz if product.region_id else ""
    if product.district_id:
        location = f"{location}, {product.district.name_uz}"

    specs_line = _render_specs(product, config.max_specs_in_post)

    values = {
        "title": _escape(product.title),
        "price": _escape(price),
        "condition": _escape(product.get_condition_display()),
        "category": _escape(product.category.name_uz if product.category_id else ""),
        "brand": _escape(product.brand.name if product.brand_id else ""),
        "model": _escape(product.model_name or ""),
        "specs_line": specs_line,
        "location": _escape(location),
        "url": product.absolute_url,
        "seller": _escape(product.seller.get_full_name() or "Sotuvchi"),
        "description": _escape((product.description or "")[:300]),
    }

    try:
        return config.post_template.format(**values)
    except KeyError as exc:
        # Admin shablonga noma'lum o'zgaruvchi yozib qo'ygan — post
        # butunlay yo'qolmasligi uchun zaxira shablonga o'tamiz.
        logger.warning("Telegram shablonida noma'lum o'zgaruvchi: %s", exc)
        return (
            f"<b>{values['title']}</b>\n\n"
            f"Narxi: {values['price']}\n"
            f"Holati: {values['condition']}\n"
            f"{values['location']}\n\n"
            f"{values['url']}"
        )


def _render_specs(product, limit):
    """Kartada ko'rsatiladigan xususiyatlardan qisqa qator yasaydi."""
    if not product.specs or not product.category_id:
        return ""

    definitions = [
        a for a in product.category.inherited_attributes() if a.is_in_card
    ][:limit]

    parts = []
    for definition in definitions:
        value = product.specs.get(definition.code)
        if value in (None, "", []):
            continue
        if isinstance(value, bool):
            value = "Ha" if value else "Yo'q"
        elif isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        text = f"{value} {definition.unit}".strip() if definition.unit else str(value)
        parts.append(_escape(text))

    return f"⚙️ {' / '.join(parts)}\n" if parts else ""


def _reply_markup(product, config):
    return {
        "inline_keyboard": [
            [{"text": config.button_text, "url": product.absolute_url}]
        ]
    }


def publish_product(product, client=None, config=None):
    """Mahsulotni kanalga joylaydi va TelegramPost yozuvini qaytaradi."""
    config = config or TelegramSettings.load()
    client = client or get_client()
    channel_id = resolve_channel_id(config)

    post = TelegramPost.objects.create(
        product=product, channel_id=channel_id, status=TelegramPostStatus.PENDING
    )

    if not config.is_enabled:
        post.status = TelegramPostStatus.SKIPPED
        post.error_message = "Telegram integratsiyasi o'chirilgan."
        post.save(update_fields=["status", "error_message"])
        return post

    if not channel_id and not client.is_mock:
        post.status = TelegramPostStatus.SKIPPED
        post.error_message = (
            "Kanal ID ko'rsatilmagan. Admin panelida yoki .env da TELEGRAM_CHANNEL_ID ni to'ldiring."
        )
        post.save(update_fields=["status", "error_message"])
        logger.warning("Telegram kanal ID sozlanmagan — post yuborilmadi.")
        return post

    caption = render_post(product, config)
    markup = _reply_markup(product, config)

    images, video = [], None
    if config.publish_media:
        images = [
            url
            for url in (
                _absolute_media_url(image.large or image.image)
                for image in product.images.all()[:MAX_MEDIA_GROUP]
            )
            if url
        ]
        if config.publish_video:
            first_video = product.videos.first()
            if first_video:
                video = _absolute_media_url(first_video.video)

    post.rendered_text = caption
    post.rendered_payload = {
        "caption": caption,
        "images": images,
        "video": video,
        "channel_id": channel_id,
    }

    try:
        response, method, message_ids = _send(
            client, channel_id, caption, images, video, markup
        )
    except TelegramError as exc:
        post.status = TelegramPostStatus.FAILED
        post.error_message = str(exc)
        post.response_payload = exc.response
        post.save()
        # Qayta urinish mantiqiy bo'lsa task qayta chaqiradi.
        if exc.retryable:
            raise
        return post

    post.status = TelegramPostStatus.PUBLISHED
    post.method = method
    post.message_id = message_ids[0] if message_ids else None
    post.message_ids = message_ids
    post.response_payload = response
    post.published_at = timezone.now()
    post.is_mock = client.is_mock
    post.save()
    return post


def _send(client, channel_id, caption, images, video, markup):
    """Media miqdoriga qarab mos usulni tanlaydi."""
    if video:
        response = client.send_video(channel_id, video, caption, markup)
        return response, "sendVideo", _message_ids(response)

    if len(images) > 1:
        # sendMediaGroup inline tugmani qo'llab-quvvatlamaydi, shuning
        # uchun havola caption ichida qoladi.
        media = [{"type": "photo", "media": url} for url in images]
        media[0]["caption"] = caption
        media[0]["parse_mode"] = "HTML"
        response = client.send_media_group(channel_id, media)
        return response, "sendMediaGroup", _message_ids(response)

    if images:
        response = client.send_photo(channel_id, images[0], caption, markup)
        return response, "sendPhoto", _message_ids(response)

    response = client.send_message(channel_id, caption, markup)
    return response, "sendMessage", _message_ids(response)


def _message_ids(response):
    result = response.get("result")
    if isinstance(result, list):
        return [item.get("message_id") for item in result if item.get("message_id")]
    if isinstance(result, dict) and result.get("message_id") is not None:
        return [result["message_id"]]
    return []


def mark_post_sold(product, client=None, config=None):
    """Kanaldagi postga «SOTILDI» belgisini qo'shadi."""
    config = config or TelegramSettings.load()
    if not config.update_on_sold:
        return None

    post = (
        TelegramPost.objects.filter(
            product=product, status=TelegramPostStatus.PUBLISHED
        )
        .order_by("-created_at")
        .first()
    )
    if post is None or not post.message_id:
        return None

    client = client or get_client()
    caption = f"{post.rendered_text}{config.sold_suffix}"

    try:
        if post.method in ("sendPhoto", "sendVideo", "sendMediaGroup"):
            client.edit_message_caption(post.channel_id, post.message_id, caption)
        else:
            client.edit_message_text(post.channel_id, post.message_id, caption)
    except TelegramError as exc:
        # Post o'chirilgan yoki juda eski bo'lishi mumkin — bu
        # sotuvchining amalini bekor qilmasligi kerak.
        logger.warning("Telegram postini yangilab bo'lmadi: %s", exc)
        return None

    post.rendered_text = caption
    post.save(update_fields=["rendered_text", "updated_at"])
    return post


def delete_post(post, client=None):
    client = client or get_client()
    for message_id in post.message_ids or ([post.message_id] if post.message_id else []):
        try:
            client.delete_message(post.channel_id, message_id)
        except TelegramError as exc:
            logger.warning("Telegram xabarini o'chirib bo'lmadi: %s", exc)
    post.status = TelegramPostStatus.DELETED
    post.save(update_fields=["status", "updated_at"])
    return post


def send_direct_message(telegram_id, text):
    """Foydalanuvchiga botdan shaxsiy xabar."""
    if not telegram_id:
        return False
    client = get_client()
    try:
        client.send_message(telegram_id, text, disable_preview=True)
        return True
    except TelegramError as exc:
        logger.info("Botdan xabar yuborib bo'lmadi (%s): %s", telegram_id, exc)
        return False
