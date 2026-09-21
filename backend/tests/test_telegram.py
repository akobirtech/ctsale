"""Telegram integratsiyasi.

Tashqi tarmoqqa hech qachon chiqilmaydi: klient soxtalashtiriladi
yoki mock rejimda ishlatiladi. Tekshiriladigan narsa — qaysi usul
tanlanishi, matn qanday shakllanishi va xato qanday qayd etilishi.
"""

import pytest
from django.test import override_settings

from apps.products.models import ProductStatus
from apps.telegrambot.client import TelegramClient, TelegramError
from apps.telegrambot.models import TelegramPost, TelegramPostStatus, TelegramSettings
from apps.telegrambot.services import (
    _strip_links,
    is_public_url,
    mark_post_sold,
    publish_product,
    render_post,
)

pytestmark = pytest.mark.django_db


class FakeClient(TelegramClient):
    """Chaqiruvlarni yozib boradigan, tarmoqqa chiqmaydigan klient."""

    def __init__(self, fail_with=None):
        super().__init__(token="fake-token")
        self.calls = []
        self.fail_with = fail_with

    @property
    def is_mock(self):
        return False

    def call(self, method, payload=None, files=None):
        self.calls.append((method, payload))
        if self.fail_with:
            raise self.fail_with
        return {"ok": True, "result": {"message_id": 777}}


@pytest.fixture
def config(db):
    settings_row = TelegramSettings.load()
    settings_row.channel_id = "@test_channel"
    settings_row.save()
    return settings_row


@pytest.fixture
def public_site(settings):
    """Telegram localhost havolasini rad etadi — testda ochiq domen."""
    settings.FRONTEND_URL = "https://ctsale.uz"
    return settings


class TestUrlGuards:
    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://ctsale.uz/uz/product/x", True),
            ("http://localhost:5173/uz/product/x", False),
            ("http://127.0.0.1:8000/x", False),
            ("http://192.168.1.10/x", False),
            ("ftp://ctsale.uz/x", False),
            ("", False),
        ],
    )
    def test_is_public_url(self, url, expected):
        assert is_public_url(url) is expected

    def test_strip_links_keeps_text(self):
        html = 'Boshi <a href="http://localhost/x">Saytda ko\'rish</a> oxiri'

        assert _strip_links(html) == "Boshi Saytda ko'rish oxiri"


class TestRendering:
    def test_template_variables_are_filled(self, product, config, public_site):
        text = render_post(product, config)

        assert product.title in text
        assert "12 500 000" in text
        assert product.get_condition_display() in text
        assert product.absolute_url in text

    def test_apostrophes_are_not_escaped(self, product, config, public_site):
        """`html.escape` apostrofni &#x27; ga aylantirardi — o'zbekcha
        matnda bu juda ko'p uchraydi va o'qishni buzardi."""
        text = render_post(product, config)

        assert "&#x27;" not in text
        assert "so'm" in text

    def test_html_special_chars_are_escaped(self, make_product, seller, config, public_site):
        product = make_product(seller, title="Noutbuk <script>alert(1)</script>")

        text = render_post(product, config)

        assert "<script>" not in text
        assert "&lt;script&gt;" in text

    def test_card_specs_appear_in_post(self, make_product, seller, config, public_site):
        product = make_product(seller, specs={"cpu": "Intel Core i7", "ram_gb": 16})

        text = render_post(product, config)

        assert "Intel Core i7" in text
        assert "16 GB" in text

    def test_broken_template_falls_back(self, product, config, public_site):
        config.post_template = "{mavjud_emas} {title}"
        config.save()

        text = render_post(product, config)

        # Post butunlay yo'qolmasligi kerak.
        assert product.title in text

    def test_negotiable_price_is_marked(self, make_product, seller, config, public_site):
        product = make_product(seller, is_negotiable=True)

        assert "kelishiladi" in render_post(product, config)

    def test_price_on_request(self, make_product, seller, config, public_site):
        product = make_product(seller, price=None, price_on_request=True)

        assert "So'rov bo'yicha" in render_post(product, config)


class TestPublishing:
    def test_text_only_when_no_images(self, product, config, public_site):
        client = FakeClient()

        post = publish_product(product, client=client, config=config)

        assert post.status == TelegramPostStatus.PUBLISHED
        assert post.method == "sendMessage"
        assert post.message_id == 777

    def test_single_image_uses_send_photo(
        self, product, config, public_site, image_file
    ):
        from apps.mediafiles.models import ProductImage

        ProductImage.objects.create(product=product, image=image_file(), is_primary=True)
        client = FakeClient()

        post = publish_product(product, client=client, config=config)

        assert post.method == "sendPhoto"

    def test_multiple_images_use_media_group(self, product, config, public_site, image_file):
        from apps.mediafiles.models import ProductImage

        ProductImage.objects.create(product=product, image=image_file(), is_primary=True)
        ProductImage.objects.create(product=product, image=image_file(), order=1)
        client = FakeClient()

        post = publish_product(product, client=client, config=config)

        assert post.method == "sendMediaGroup"

    def test_inline_button_present_for_public_site(self, product, config, public_site):
        client = FakeClient()

        publish_product(product, client=client, config=config)

        _, payload = client.calls[0]
        assert "reply_markup" in payload
        assert payload["reply_markup"]["inline_keyboard"][0][0]["url"].startswith("https://")

    def test_local_url_drops_button_and_anchor(self, product, config, settings):
        """Telegram localhost havolasini rad etadi ("Wrong HTTP URL") —
        lokal muhitda post havolasiz yuborilishi kerak."""
        settings.FRONTEND_URL = "http://localhost:5173"
        client = FakeClient()

        post = publish_product(product, client=client, config=config)

        _, payload = client.calls[0]
        assert "reply_markup" not in payload
        assert "<a href=" not in post.rendered_text

    def test_disabled_integration_skips(self, product, config, public_site):
        config.is_enabled = False
        config.save()
        client = FakeClient()

        post = publish_product(product, client=client, config=config)

        assert post.status == TelegramPostStatus.SKIPPED
        assert client.calls == []

    def test_missing_channel_skips_with_clear_reason(self, product, public_site):
        config = TelegramSettings.load()
        config.channel_id = ""
        config.save()
        client = FakeClient()

        with override_settings(TELEGRAM_CHANNEL_ID=""):
            post = publish_product(product, client=client, config=config)

        assert post.status == TelegramPostStatus.SKIPPED
        assert "Kanal ID" in post.error_message

    def test_api_error_is_recorded(self, product, config, public_site):
        client = FakeClient(fail_with=TelegramError("Bad Request: chat not found", retryable=False))

        post = publish_product(product, client=client, config=config)

        assert post.status == TelegramPostStatus.FAILED
        assert "chat not found" in post.error_message

    def test_retryable_error_propagates(self, product, config, public_site):
        client = FakeClient(fail_with=TelegramError("Too Many Requests", retryable=True))

        with pytest.raises(TelegramError):
            publish_product(product, client=client, config=config)

        post = TelegramPost.objects.latest("created_at")
        assert post.status == TelegramPostStatus.FAILED


class TestMockMode:
    def test_missing_token_enables_mock(self, settings):
        settings.TELEGRAM_BOT_TOKEN = ""

        assert TelegramClient().is_mock is True

    def test_mock_publishes_without_network(self, product, config, public_site, settings):
        settings.TELEGRAM_BOT_TOKEN = ""

        post = publish_product(product, client=TelegramClient(), config=config)

        assert post.status == TelegramPostStatus.PUBLISHED
        assert post.is_mock is True


class TestSoldUpdate:
    def test_sold_edits_existing_post(self, product, config, public_site):
        client = FakeClient()
        publish_product(product, client=client, config=config)
        client.calls.clear()

        product.status = ProductStatus.SOLD
        product.save()
        mark_post_sold(product, client=client, config=config)

        method, payload = client.calls[0]
        assert method in ("editMessageText", "editMessageCaption")
        assert "SOTILDI" in payload["text" if method == "editMessageText" else "caption"]

    def test_sold_update_can_be_disabled(self, product, config, public_site):
        client = FakeClient()
        publish_product(product, client=client, config=config)
        config.update_on_sold = False
        config.save()
        client.calls.clear()

        mark_post_sold(product, client=client, config=config)

        assert client.calls == []

    def test_edit_failure_does_not_raise(self, product, config, public_site):
        """Post o'chirilgan bo'lishi mumkin — sotuvchining amali
        shu sababli bekor bo'lmasligi kerak."""
        client = FakeClient()
        publish_product(product, client=client, config=config)
        failing = FakeClient(fail_with=TelegramError("message to edit not found"))

        assert mark_post_sold(product, client=failing, config=config) is None


class TestTemplateValidation:
    def test_unknown_variable_is_rejected(self, auth_client, admin):
        response = auth_client(admin).patch(
            "/api/v1/admin/telegram/settings/",
            {"post_template": "{title} {yoq_bunday}"},
            format="json",
        )

        assert response.status_code == 400
        assert "post_template" in response.data["error"]["details"]

    def test_valid_template_is_saved(self, auth_client, admin):
        response = auth_client(admin).patch(
            "/api/v1/admin/telegram/settings/",
            {"post_template": "{title} — {price}"},
            format="json",
        )

        assert response.status_code == 200
        assert TelegramSettings.load().post_template == "{title} — {price}"

    def test_bot_token_never_leaks(self, auth_client, admin, settings):
        settings.TELEGRAM_BOT_TOKEN = "123456:SUPER-MAXFIY"

        response = auth_client(admin).get("/api/v1/admin/telegram/settings/")

        assert "SUPER-MAXFIY" not in str(response.data)
        assert "is_configured" in response.data
