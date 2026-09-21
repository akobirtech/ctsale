"""Bot suhbati: /start, qidiruv, sahifalash, hisobni ulash.

Tarmoq yo'q — soxta klient yuborilgan xabarlarni yig'adi, testlar esa
matn va tugmalarni tekshiradi.
"""

import json

import pytest

from apps.products.models import ProductStatus
from apps.telegrambot import bot
from apps.telegrambot.models import TelegramBotUser, TelegramLinkToken

pytestmark = pytest.mark.django_db

CHAT_ID = 555_000_111
WEBHOOK_URL = "/telegram/webhook/"


class FakeClient:
    """Yuborilgan xabarlarni eslab qoladigan klient."""

    def __init__(self):
        self.messages = []
        self.calls = []

    def send_message(self, chat_id, text, reply_markup=None, disable_preview=False):
        self.messages.append({"chat_id": chat_id, "text": text, "markup": reply_markup})
        return {"ok": True, "result": {"message_id": len(self.messages)}}

    def call(self, method, payload=None, files=None):
        self.calls.append((method, payload))
        return {"ok": True, "result": {}}

    @property
    def last(self):
        return self.messages[-1]["text"]


@pytest.fixture
def client():
    return FakeClient()


def message(text, chat_id=CHAT_ID, sender_id=None):
    return {
        "message": {
            "message_id": 1,
            "chat": {"id": chat_id, "type": "private"},
            "from": {
                "id": sender_id or chat_id,
                "first_name": "Akobir",
                "username": "akobir",
            },
            "text": text,
        }
    }


class TestStart:
    def test_greets_and_shows_keyboard(self, client):
        bot.handle_update(message("/start"), client=client)

        assert "Akobir" in client.last
        buttons = client.messages[-1]["markup"]["keyboard"]
        assert [b["text"] for b in buttons[0]] == [bot.BUTTON_SEARCH, bot.BUTTON_MY]

    def test_records_the_telegram_user(self, client):
        bot.handle_update(message("/start"), client=client)

        saved = TelegramBotUser.objects.get(telegram_id=CHAT_ID)
        assert saved.username == "akobir"
        assert saved.last_interaction_at is not None

    def test_second_message_does_not_duplicate_the_user(self, client):
        bot.handle_update(message("/start"), client=client)
        bot.handle_update(message("/help"), client=client)

        assert TelegramBotUser.objects.filter(telegram_id=CHAT_ID).count() == 1

    def test_unknown_command(self, client):
        bot.handle_update(message("/yoq"), client=client)

        assert "/help" in client.last

    def test_group_chats_are_ignored(self, client):
        update = message("/start")
        update["message"]["chat"]["type"] = "supergroup"

        bot.handle_update(update, client=client)

        assert client.messages == []


class TestSearch:
    def test_plain_text_searches(self, client, product):
        bot.handle_update(message(product.title[:12]), client=client)

        assert product.slug in client.last

    def test_price_is_shown(self, client, product):
        bot.handle_update(message(product.title[:12]), client=client)

        assert product.currency in client.last

    def test_too_short_query(self, client, product):
        bot.handle_update(message("a"), client=client)

        assert "qisqa" in client.last.lower()

    def test_nothing_found(self, client, product):
        bot.handle_update(message("zzzqwertyuiop"), client=client)

        assert "topilmadi" in client.last

    def test_unpublished_listings_never_appear(self, client, make_product, seller):
        draft = make_product(seller, status=ProductStatus.DRAFT, title="Maxfiy qoralama")

        bot.handle_update(message("Maxfiy qoralama"), client=client)

        assert draft.slug not in client.last

    def test_search_command_without_argument(self, client):
        bot.handle_update(message("/search"), client=client)

        assert "/search" in client.last

    def test_html_in_query_is_escaped(self, client):
        bot.handle_update(message("<b>zzzqwerty</b>"), client=client)

        assert "&lt;b&gt;" in client.last


class TestPagination:
    @pytest.fixture
    def many(self, make_product, seller):
        return [
            make_product(seller, title=f"Lenovo ThinkPad nomer {i}") for i in range(7)
        ]

    def test_first_page_offers_next(self, client, many):
        bot.handle_update(message("ThinkPad"), client=client)

        buttons = client.messages[-1]["markup"]["inline_keyboard"][0]
        assert [b["text"] for b in buttons] == ["Keyingi ➡️"]

    def test_page_size_is_respected(self, client, many):
        bot.handle_update(message("ThinkPad"), client=client)

        assert client.last.count("🔗") == bot.PAGE_SIZE

    def test_callback_opens_the_next_page(self, client, many):
        bot.handle_update(message("ThinkPad"), client=client)
        data = client.messages[-1]["markup"]["inline_keyboard"][0][0]["callback_data"]

        bot.handle_update(
            {
                "callback_query": {
                    "id": "1",
                    "data": data,
                    "from": {"id": CHAT_ID},
                    "message": {"chat": {"id": CHAT_ID}},
                }
            },
            client=client,
        )

        assert "6–7" in client.last
        # Oxirgi sahifada faqat "Oldingi" qoladi.
        buttons = client.messages[-1]["markup"]["inline_keyboard"][0]
        assert [b["text"] for b in buttons] == ["⬅️ Oldingi"]

    def test_callback_is_acknowledged(self, client, many):
        bot.handle_update(message("ThinkPad"), client=client)
        data = client.messages[-1]["markup"]["inline_keyboard"][0][0]["callback_data"]

        bot.handle_update(
            {
                "callback_query": {
                    "id": "42",
                    "data": data,
                    "from": {"id": CHAT_ID},
                    "message": {"chat": {"id": CHAT_ID}},
                }
            },
            client=client,
        )

        assert ("answerCallbackQuery", {"callback_query_id": "42"}) in client.calls

    def test_callback_data_fits_telegram_limit(self):
        long_query = "x" * 200

        data = bot._callback(long_query, 3)

        assert len(data.encode("utf-8")) <= 64


class TestMyProducts:
    def test_requires_a_linked_account(self, client):
        bot.handle_update(message(bot.BUTTON_MY), client=client)

        assert "/link" in client.last

    def test_shows_statuses_including_drafts(self, client, make_product, seller):
        TelegramBotUser.objects.create(telegram_id=CHAT_ID, user=seller)
        draft = make_product(seller, status=ProductStatus.DRAFT, title="Qoralama e'lon")

        bot.handle_update(message(bot.BUTTON_MY), client=client)

        assert draft.title in client.last
        assert bot.STATUS_LABELS[ProductStatus.DRAFT] in client.last

    def test_other_sellers_listings_are_not_shown(
        self, client, make_product, seller, other_seller
    ):
        TelegramBotUser.objects.create(telegram_id=CHAT_ID, user=seller)
        theirs = make_product(other_seller, title="Begona e'lon")

        bot.handle_update(message("/my"), client=client)

        assert theirs.title not in client.last

    def test_empty_seller_gets_a_link(self, client, seller):
        TelegramBotUser.objects.create(telegram_id=CHAT_ID, user=seller)

        bot.handle_update(message("/my"), client=client)

        assert "seller/products/new" in client.last


class TestAccountLinking:
    def test_deep_link_connects_the_account(self, client, seller):
        token = bot.issue_link_token(seller)

        bot.handle_update(message(f"/start {token}"), client=client)

        seller.refresh_from_db()
        bot_user = TelegramBotUser.objects.get(telegram_id=CHAT_ID)
        assert bot_user.user_id == seller.id
        assert seller.telegram_id == CHAT_ID

    def test_token_works_only_once(self, client, seller):
        token = bot.issue_link_token(seller)
        bot.handle_update(message(f"/start {token}"), client=client)

        bot.handle_update(message(f"/start {token}"), client=client)

        assert "eskirgan yoki noto'g'ri" in client.last

    def test_expired_token_is_rejected(self, client, seller):
        from datetime import timedelta

        from django.utils import timezone

        token = bot.issue_link_token(seller)
        TelegramLinkToken.objects.filter(token=token).update(
            created_at=timezone.now() - timedelta(minutes=bot.LINK_TOKEN_TTL_MINUTES + 1)
        )

        bot.handle_update(message(f"/start {token}"), client=client)

        assert TelegramBotUser.objects.get(telegram_id=CHAT_ID).user_id is None

    def test_unknown_token_does_not_link(self, client, seller):
        bot.handle_update(message("/start soxta-kod"), client=client)

        assert TelegramBotUser.objects.get(telegram_id=CHAT_ID).user_id is None

    def test_a_new_token_replaces_the_previous_one(self, seller):
        first = bot.issue_link_token(seller)
        second = bot.issue_link_token(seller)

        assert first != second
        assert not TelegramLinkToken.objects.filter(token=first).exists()


class TestStopAndBlocking:
    def test_stop_marks_the_user(self, client):
        bot.handle_update(message("/start"), client=client)

        bot.handle_update(message("/stop"), client=client)

        assert TelegramBotUser.objects.get(telegram_id=CHAT_ID).is_blocked is True

    def test_blocking_the_bot_is_recorded(self, client):
        bot.handle_update(message("/start"), client=client)

        bot.handle_update(
            {
                "my_chat_member": {
                    "from": {"id": CHAT_ID},
                    "new_chat_member": {"status": "kicked"},
                }
            },
            client=client,
        )

        assert TelegramBotUser.objects.get(telegram_id=CHAT_ID).is_blocked is True

    def test_linking_unblocks(self, client, seller):
        bot.handle_update(message("/stop"), client=client)
        token = bot.issue_link_token(seller)

        bot.handle_update(message(f"/start {token}"), client=client)

        assert TelegramBotUser.objects.get(telegram_id=CHAT_ID).is_blocked is False


class TestResilience:
    def test_unknown_update_type_is_ignored(self, client):
        assert bot.handle_update({"edited_message": {}}, client=client) is None

    def test_empty_message_asks_for_text(self, client):
        update = message("")
        bot.handle_update(update, client=client)

        assert "Matn" in client.last

    def test_telegram_failure_does_not_raise(self, client, monkeypatch):
        from apps.telegrambot.client import TelegramError

        def explode(*args, **kwargs):
            raise TelegramError("Telegram yiqildi")

        monkeypatch.setattr(client, "send_message", explode)

        assert bot.handle_update(message("/start"), client=client) is None


class TestWebhook:
    def test_rejects_wrong_secret(self, api, settings):
        settings.TELEGRAM_WEBHOOK_SECRET = "haqiqiy-sir"

        response = api.post(
            WEBHOOK_URL,
            data=json.dumps(message("/start")),
            content_type="application/json",
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="soxta",
        )

        assert response.status_code == 403
        assert not TelegramBotUser.objects.exists()

    def test_rejects_when_secret_is_not_configured(self, api, settings):
        """Sirsiz webhook — istalgan odam bot nomidan gapira olardi."""
        settings.TELEGRAM_WEBHOOK_SECRET = ""

        response = api.post(
            WEBHOOK_URL,
            data=json.dumps(message("/start")),
            content_type="application/json",
        )

        assert response.status_code == 403

    def test_accepts_valid_update(self, api, settings):
        settings.TELEGRAM_WEBHOOK_SECRET = "haqiqiy-sir"
        settings.TELEGRAM_MOCK = True

        response = api.post(
            WEBHOOK_URL,
            data=json.dumps(message("/start")),
            content_type="application/json",
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="haqiqiy-sir",
        )

        assert response.status_code == 200
        assert TelegramBotUser.objects.filter(telegram_id=CHAT_ID).exists()

    def test_broken_json_returns_400(self, api, settings):
        settings.TELEGRAM_WEBHOOK_SECRET = "haqiqiy-sir"

        response = api.post(
            WEBHOOK_URL,
            data="{buzilgan",
            content_type="application/json",
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="haqiqiy-sir",
        )

        assert response.status_code == 400

    def test_get_is_not_allowed(self, api):
        assert api.get(WEBHOOK_URL).status_code == 405


class TestLinkTokenEndpoint:
    URL = "/api/v1/telegram/link-token/"

    def test_requires_login(self, api):
        assert api.post(self.URL).status_code == 401

    def test_returns_a_deep_link(self, auth_client, seller, settings):
        settings.TELEGRAM_BOT_USERNAME = "ctsale_bot"

        response = auth_client(seller).post(self.URL)

        assert response.status_code == 200
        assert response.data["url"].startswith("https://t.me/ctsale_bot?start=")
        assert TelegramLinkToken.objects.filter(user=seller).exists()
