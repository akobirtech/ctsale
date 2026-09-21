"""Bot bilan suhbat: /start, qidiruv, mening e'lonlarim.

Bu modulda tarmoq yo'q — `handle_update()` tayyor `update` lug'atini
oladi va javobni `client` orqali yuboradi. Shuning uchun uni testda
soxta klient bilan to'liq tekshirib bo'ladi: webhook ham, long polling
ham bitta shu funksiyani chaqiradi.

Nima uchun kanal emas, shaxsiy bot: e'lon kanalga avtomatik tushadi,
lekin xaridor "16 GB RAM li noutbuk" deb qidira olishi kerak, sotuvchi
esa e'loni qaysi bosqichda ekanini ko'rishi kerak.
"""

import logging
import secrets

from django.conf import settings
from django.utils import timezone

from apps.products.models import Product, ProductStatus
from apps.products.search import MIN_SEARCH_LENGTH, search_products, search_suggestions

from .client import TelegramError, get_client
from .models import TelegramBotUser
from .services import escape_html as _escape

logger = logging.getLogger(__name__)

# Bitta javobda nechta e'lon ko'rsatiladi. Telegram xabarida 4096 belgi
# chegarasi bor, 5 ta karta undan xavfsiz uzoqda turadi.
PAGE_SIZE = 5

# Bog'lash kodi bir martalik va qisqa umrli bo'lishi kerak.
LINK_TOKEN_TTL_MINUTES = 30

BUTTON_SEARCH = "🔍 Qidirish"
BUTTON_MY = "📋 Mening e'lonlarim"
BUTTON_NEW = "➕ E'lon berish"
BUTTON_HELP = "❓ Yordam"

MAIN_KEYBOARD = {
    "keyboard": [
        [{"text": BUTTON_SEARCH}, {"text": BUTTON_MY}],
        [{"text": BUTTON_NEW}, {"text": BUTTON_HELP}],
    ],
    "resize_keyboard": True,
}

HELP_TEXT = (
    "<b>Nima qila olaman:</b>\n\n"
    "• Shunchaki qidiruv so'zini yozing — masalan <i>ThinkPad 16 GB</i>\n"
    "• {my} — e'lonlaringiz va ularning holati\n"
    "• /link — saytdagi hisobingizni ulash\n"
    "• /stop — bildirishnomalarni to'xtatish\n\n"
    "E'lon berish sayt orqali: {site}"
).format(my=BUTTON_MY, site="{site}")

STATUS_LABELS = {
    ProductStatus.DRAFT: "📝 Qoralama",
    ProductStatus.PENDING: "⏳ Moderatsiyada",
    ProductStatus.APPROVED: "✅ Chop etilgan",
    ProductStatus.REJECTED: "❌ Rad etilgan",
    ProductStatus.RESERVED: "🤝 Band",
    ProductStatus.SOLD: "💰 Sotilgan",
    ProductStatus.EXPIRED: "🕒 Muddati tugagan",
    ProductStatus.ARCHIVED: "📦 Arxivda",
}


def site_url():
    return settings.FRONTEND_URL.rstrip("/")


def product_url(product, lang=None):
    return f"{site_url()}/{lang or settings.DEFAULT_LANGUAGE}/product/{product.slug}"


# --------------------------------------------------------------------------
# Kirish nuqtasi
# --------------------------------------------------------------------------


def handle_update(update, client=None):
    """Telegram yuborgan bitta `update` ni qayta ishlaydi.

    Hech qachon istisno otmaydi: webhook 200 qaytarmasa Telegram
    xuddi shu update'ni qayta-qayta yuboraveradi.
    """
    client = client or get_client()
    try:
        if "message" in update:
            return _handle_message(update["message"], client)
        if "callback_query" in update:
            return _handle_callback(update["callback_query"], client)
        if "my_chat_member" in update:
            return _handle_membership(update["my_chat_member"])
    except TelegramError as exc:
        logger.info("Telegram javob bermadi: %s", exc)
    except Exception:  # pragma: no cover — kutilmagan xato
        logger.exception("Bot update'ni qayta ishlay olmadi")
    return None


def _handle_message(message, client):
    chat = message.get("chat") or {}
    if chat.get("type") != "private":
        # Guruhlarda bot javob bermaydi — u shaxsiy yordamchi.
        return None

    bot_user = _upsert_user(message.get("from") or {})
    text = (message.get("text") or "").strip()

    if not text:
        return _reply(client, chat["id"], "Matn yuboring — men shu bo'yicha qidiraman.")

    if text.startswith("/"):
        return _handle_command(text, bot_user, chat["id"], client)

    if text == BUTTON_SEARCH:
        return _reply(client, chat["id"], "Nimani qidiramiz? Masalan: <i>RTX 4060</i>")
    if text == BUTTON_MY:
        return _send_my_products(bot_user, chat["id"], client)
    if text == BUTTON_NEW:
        return _reply(
            client,
            chat["id"],
            f"E'lon berish sahifasi:\n{site_url()}/{settings.DEFAULT_LANGUAGE}/seller/products/new",
        )
    if text == BUTTON_HELP:
        return _send_help(chat["id"], client)

    return _send_search_results(text, chat["id"], client, page=0)


def _handle_command(text, bot_user, chat_id, client):
    command, _, argument = text.partition(" ")
    command = command.split("@")[0].lower()
    argument = argument.strip()

    if command == "/start":
        return _handle_start(argument, bot_user, chat_id, client)
    if command == "/help":
        return _send_help(chat_id, client)
    if command == "/search":
        if not argument:
            return _reply(client, chat_id, "Qidiruv so'zini yozing: <code>/search RTX 4060</code>")
        return _send_search_results(argument, chat_id, client, page=0)
    if command in ("/my", "/myads"):
        return _send_my_products(bot_user, chat_id, client)
    if command == "/link":
        return _send_link_instructions(bot_user, chat_id, client)
    if command == "/stop":
        return _handle_stop(bot_user, chat_id, client)

    return _reply(client, chat_id, "Bunday buyruq yo'q. /help ni bosing.")


# --------------------------------------------------------------------------
# Buyruqlar
# --------------------------------------------------------------------------


def _handle_start(token, bot_user, chat_id, client):
    """`/start` va `t.me/bot?start=<token>` orqali hisobni ulash."""
    if token:
        linked = link_account(bot_user, token)
        if linked is not None:
            return _reply(
                client,
                chat_id,
                f"✅ <b>{_escape(linked.get_full_name() or linked.phone)}</b> hisobi ulandi.\n"
                "Endi e'lonlaringiz holati shu yerga keladi.",
                keyboard=MAIN_KEYBOARD,
            )
        return _reply(
            client,
            chat_id,
            "Bog'lash kodi eskirgan yoki noto'g'ri. Saytdagi profilingizdan "
            "yangi havola oling.",
            keyboard=MAIN_KEYBOARD,
        )

    name = _escape(bot_user.first_name or "")
    greeting = f"Assalomu alaykum{', ' + name if name else ''}! 👋"
    return _reply(
        client,
        chat_id,
        f"{greeting}\n\nMen <b>{_escape(settings.SITE_NAME)}</b> yordamchisiman.\n"
        "Kompyuter texnikasi e'lonlarini qidirib beraman.\n\n"
        "Qidiruv so'zini yozing yoki pastdagi tugmalardan foydalaning.",
        keyboard=MAIN_KEYBOARD,
    )


def _send_help(chat_id, client):
    return _reply(client, chat_id, HELP_TEXT.format(site=site_url()), keyboard=MAIN_KEYBOARD)


def _handle_stop(bot_user, chat_id, client):
    bot_user.is_blocked = True
    bot_user.save(update_fields=["is_blocked", "updated_at"])
    return _reply(
        client,
        chat_id,
        "Bildirishnomalar to'xtatildi. Qayta yoqish uchun /start ni bosing.",
    )


def _send_link_instructions(bot_user, chat_id, client):
    if bot_user.user_id:
        return _reply(
            client,
            chat_id,
            "Hisobingiz allaqachon ulangan. Uzish uchun saytdagi profilga kiring.",
        )
    return _reply(
        client,
        chat_id,
        "Hisobni ulash uchun saytdagi profilingizda "
        "<b>Telegramni ulash</b> tugmasini bosing — u sizni shu yerga "
        "bir martalik havola bilan qaytaradi.\n\n"
        f"{site_url()}/{settings.DEFAULT_LANGUAGE}/profile",
    )


# --------------------------------------------------------------------------
# Qidiruv
# --------------------------------------------------------------------------


def _send_search_results(query, chat_id, client, page=0):
    if len(query) < MIN_SEARCH_LENGTH:
        return _reply(client, chat_id, "Qidiruv so'zi juda qisqa.")

    queryset = search_products(Product.objects.public().with_relations(), query)
    total = queryset.count()

    if total == 0:
        suggestions = search_suggestions(query)
        text = f"<b>{_escape(query)}</b> bo'yicha hech narsa topilmadi."
        if suggestions:
            text += "\n\nBalki shulardandir:\n" + "\n".join(
                f"• {_escape(title)}" for title in suggestions
            )
        return _reply(client, chat_id, text)

    offset = page * PAGE_SIZE
    rows = list(queryset[offset : offset + PAGE_SIZE])
    if not rows:
        return _reply(client, chat_id, "Boshqa natija qolmadi.")

    header = f"🔍 <b>{_escape(query)}</b> — {total} ta e'lon"
    if page:
        header += f" ({offset + 1}–{offset + len(rows)})"

    body = "\n\n".join(_format_card(product) for product in rows)
    markup = _pagination_markup(query, page, total)
    return _reply(client, chat_id, f"{header}\n\n{body}", markup=markup)


def _format_card(product):
    price = (
        f"{int(product.price):,}".replace(",", " ") + f" {product.currency}"
        if product.price
        else "Kelishilgan"
    )
    return (
        f"<b>{_escape(product.title)}</b>\n"
        f"💰 {price}\n"
        f"🔗 {product_url(product)}"
    )


def _pagination_markup(query, page, total):
    """Sahifalash tugmalari. Qidiruv so'zi callback ichida saqlanadi.

    Telegram `callback_data` uchun 64 baytdan ko'pini qabul qilmaydi,
    shuning uchun so'rov qisqartiriladi.
    """
    buttons = []
    if page > 0:
        buttons.append({"text": "⬅️ Oldingi", "callback_data": _callback(query, page - 1)})
    if (page + 1) * PAGE_SIZE < total:
        buttons.append({"text": "Keyingi ➡️", "callback_data": _callback(query, page + 1)})

    if not buttons:
        return None
    return {"inline_keyboard": [buttons]}


def _callback(query, page):
    # 64 bayt chegarasi: "s:<page>:" prefiksi uchun joy qoldiramiz.
    return f"s:{page}:{query}"[:64]


def _handle_callback(callback, client):
    data = callback.get("data") or ""
    chat_id = ((callback.get("message") or {}).get("chat") or {}).get("id")
    _upsert_user(callback.get("from") or {})

    try:
        client.call("answerCallbackQuery", {"callback_query_id": callback["id"]})
    except TelegramError:
        # Javob bermaslik faqat tugmada "soat" qoldiradi — natijani
        # yuborishga to'sqinlik qilmaydi.
        pass

    if not chat_id or not data.startswith("s:"):
        return None

    _, _, rest = data.partition(":")
    page, _, query = rest.partition(":")
    return _send_search_results(query, chat_id, client, page=int(page or 0))


# --------------------------------------------------------------------------
# Mening e'lonlarim
# --------------------------------------------------------------------------


def _send_my_products(bot_user, chat_id, client):
    if not bot_user.user_id:
        return _reply(
            client,
            chat_id,
            "Buning uchun sayt hisobingizni ulash kerak. /link ni bosing.",
        )

    products = list(
        Product.objects.filter(seller_id=bot_user.user_id, is_deleted=False)
        .only("title", "slug", "status", "views_count", "price", "currency")
        .order_by("-created_at")[:10]
    )
    if not products:
        return _reply(
            client,
            chat_id,
            f"Hali e'lon bermabsiz.\n{site_url()}/{settings.DEFAULT_LANGUAGE}/seller/products/new",
        )

    lines = []
    for product in products:
        label = STATUS_LABELS.get(product.status, product.status)
        lines.append(
            f"{label}\n<b>{_escape(product.title)}</b>\n"
            f"👁 {product.views_count} · 🔗 {product_url(product)}"
        )
    return _reply(client, chat_id, "📋 <b>E'lonlaringiz</b>\n\n" + "\n\n".join(lines))


# --------------------------------------------------------------------------
# Hisobni ulash
# --------------------------------------------------------------------------


def issue_link_token(user):
    """Sayt profilidan chaqiriladi: bir martalik bog'lash kodi.

    Kod `TelegramBotUser` da emas, foydalanuvchi uchun alohida
    yozuvda saqlanadi — bot bilan hali gaplashmagan odam ham havolani
    ola bilishi kerak.
    """
    from .models import TelegramLinkToken

    TelegramLinkToken.objects.filter(user=user).delete()
    token = secrets.token_urlsafe(16)
    TelegramLinkToken.objects.create(user=user, token=token)
    return token


def link_account(bot_user, token):
    """Kod bo'yicha sayt hisobini botga bog'laydi. Muvaffaqiyatsizda None."""
    from .models import TelegramLinkToken

    deadline = timezone.now() - timezone.timedelta(minutes=LINK_TOKEN_TTL_MINUTES)
    row = (
        TelegramLinkToken.objects.select_related("user")
        .filter(token=token, created_at__gte=deadline)
        .first()
    )
    if row is None:
        return None

    user = row.user
    bot_user.user = user
    bot_user.link_token = ""
    bot_user.is_blocked = False
    bot_user.save(update_fields=["user", "link_token", "is_blocked", "updated_at"])

    # Bildirishnomalar `User.telegram_id` orqali yuboriladi.
    if user.telegram_id != bot_user.telegram_id:
        user.telegram_id = bot_user.telegram_id
        user.save(update_fields=["telegram_id", "updated_at"])

    row.delete()  # bir martalik
    return user


# --------------------------------------------------------------------------
# Yordamchilar
# --------------------------------------------------------------------------


def _upsert_user(sender):
    """Telegram foydalanuvchisini yozib qo'yadi yoki yangilaydi."""
    telegram_id = sender.get("id")
    bot_user, _ = TelegramBotUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            "username": sender.get("username") or "",
            "first_name": sender.get("first_name") or "",
            "language_code": sender.get("language_code") or "",
        },
    )
    bot_user.last_interaction_at = timezone.now()
    bot_user.username = sender.get("username") or bot_user.username
    bot_user.first_name = sender.get("first_name") or bot_user.first_name
    bot_user.save(update_fields=["last_interaction_at", "username", "first_name", "updated_at"])
    return bot_user


def _handle_membership(event):
    """Foydalanuvchi botni bloklagani/ochgani haqidagi xabar."""
    status = ((event.get("new_chat_member") or {}).get("status")) or ""
    sender = event.get("from") or {}
    if not sender.get("id"):
        return None

    TelegramBotUser.objects.filter(telegram_id=sender["id"]).update(
        is_blocked=status in ("kicked", "left"), updated_at=timezone.now()
    )
    return None


def _reply(client, chat_id, text, keyboard=None, markup=None):
    return client.send_message(
        chat_id, text, reply_markup=markup or keyboard, disable_preview=True
    )
