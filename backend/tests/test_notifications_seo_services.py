"""Bildirishnoma yetkazish kanallari va SEO servis funksiyalari.

Bular API orqali emas, to'g'ridan-to'g'ri chaqiriladi: tashqi kanallar
(Telegram, email) va SEO yig'uvchilar shu darajada tekshirilgani
aniqroq va tezroq.
"""

import pytest
from django.core import mail

from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.services import absolute_link, notify
from apps.seo.models import SeoSettings
from apps.seo.services import (
    category_seo_payload,
    hreflang_links,
    organization_jsonld,
    site_allows_indexing,
    verification_tags,
    website_jsonld,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def public_site(settings):
    settings.FRONTEND_URL = "https://ctsale.uz"
    return settings


class TestNotificationDelivery:
    def test_in_app_is_always_created(self, user):
        notification = notify(user, "system", title="Salom", body="Matn")

        assert notification is not None
        assert "in_app" in notification.sent_channels

    def test_none_recipient_is_ignored(self):
        assert notify(None, "system", title="Salom") is None

    def test_email_is_sent_when_enabled(self, user):
        user.email = "test@example.com"
        user.save()
        NotificationPreference.objects.update_or_create(
            user=user, defaults={"email_enabled": True}
        )

        notify(user, "system", title="Email sarlavhasi", body="Matn")

        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "Email sarlavhasi"

    def test_email_is_skipped_without_address(self, user):
        NotificationPreference.objects.update_or_create(
            user=user, defaults={"email_enabled": True}
        )

        notify(user, "system", title="Salom")

        assert len(mail.outbox) == 0

    def test_telegram_is_skipped_without_linked_account(self, user):
        NotificationPreference.objects.update_or_create(
            user=user, defaults={"telegram_enabled": True}
        )

        notification = notify(user, "system", title="Salom")

        assert "telegram" not in notification.sent_channels

    def test_telegram_delivery_is_recorded(self, user, monkeypatch, public_site):
        sent = []
        monkeypatch.setattr(
            "apps.telegrambot.services.send_direct_message",
            lambda chat_id, text: sent.append((chat_id, text)) or True,
        )
        user.telegram_id = 12345
        user.save()
        NotificationPreference.objects.update_or_create(
            user=user, defaults={"telegram_enabled": True}
        )

        notification = notify(
            user, "system", title="Sarlavha", body="Matn", link="/product/x"
        )

        assert "telegram" in notification.sent_channels
        assert sent[0][0] == 12345
        assert "https://ctsale.uz/uz/product/x" in sent[0][1]

    def test_channel_failure_does_not_break_in_app(self, user, monkeypatch):
        """Tashqi kanal uzilsa ham foydalanuvchi xabarni saytda ko'rishi kerak."""

        def boom(*args, **kwargs):
            raise RuntimeError("Telegram uzildi")

        monkeypatch.setattr("apps.telegrambot.services.send_direct_message", boom)
        user.telegram_id = 12345
        user.save()
        NotificationPreference.objects.update_or_create(
            user=user, defaults={"telegram_enabled": True}
        )

        notification = notify(user, "system", title="Salom")

        assert Notification.objects.filter(pk=notification.pk).exists()
        assert "telegram" not in notification.sent_channels

    @pytest.mark.parametrize(
        "path,expected",
        [
            ("/product/x", "https://ctsale.uz/uz/product/x"),
            ("", "https://ctsale.uz"),
            ("https://boshqa.uz/x", "https://boshqa.uz/x"),
        ],
    )
    def test_absolute_link(self, public_site, path, expected):
        assert absolute_link(path) == expected


class TestSeoHelpers:
    def test_hreflang_covers_all_languages(self, public_site):
        links = hreflang_links("/product/x")

        codes = {item["hreflang"] for item in links}
        assert codes == {"uz", "ru", "en", "x-default"}
        assert links[0]["href"] == "https://ctsale.uz/uz/product/x"

    def test_hreflang_for_root(self, public_site):
        links = hreflang_links("/")

        assert links[0]["href"] == "https://ctsale.uz/uz"

    def test_x_default_points_to_default_language(self, public_site):
        links = hreflang_links("/catalog")

        default = next(item for item in links if item["hreflang"] == "x-default")
        assert "/uz/catalog" in default["href"]

    def test_verification_tags_prefer_database(self, settings):
        settings.GOOGLE_SITE_VERIFICATION = "env-qiymat"
        config = SeoSettings.load()
        config.google_site_verification = "db-qiymat"
        config.yandex_verification = "yandex-kod"
        config.save()

        tags = verification_tags()

        assert tags["google-site-verification"] == "db-qiymat"
        assert tags["yandex-verification"] == "yandex-kod"

    def test_verification_falls_back_to_env(self, settings):
        settings.GOOGLE_SITE_VERIFICATION = "env-qiymat"

        assert verification_tags()["google-site-verification"] == "env-qiymat"

    def test_empty_verification_is_omitted(self, settings):
        settings.GOOGLE_SITE_VERIFICATION = ""
        settings.YANDEX_VERIFICATION = ""
        settings.BING_VERIFICATION = ""

        assert verification_tags() == {}

    def test_indexing_can_be_disabled_by_env(self, settings):
        settings.SEO_ALLOW_INDEXING = False

        assert site_allows_indexing() is False

    def test_indexing_can_be_disabled_in_admin(self, settings):
        settings.SEO_ALLOW_INDEXING = True
        config = SeoSettings.load()
        config.robots_allow_indexing = False
        config.save()

        assert site_allows_indexing() is False


class TestSiteJsonLd:
    def test_organization_schema(self, public_site):
        config = SeoSettings.load()
        config.organization_phone = "+998901234567"
        config.social_links = ["https://t.me/notbuk_sot"]
        config.save()

        data = organization_jsonld()

        assert data["@type"] == "Organization"
        assert data["url"] == "https://ctsale.uz"
        assert data["sameAs"] == ["https://t.me/notbuk_sot"]
        assert data["contactPoint"][0]["telephone"] == "+998901234567"

    def test_website_schema_has_search_action(self, public_site):
        data = website_jsonld("ru")

        assert data["@type"] == "WebSite"
        assert data["inLanguage"] == "ru"
        target = data["potentialAction"]["target"]["urlTemplate"]
        assert target == "https://ctsale.uz/ru/search?q={search_term_string}"


class TestCategorySeo:
    def test_first_page_is_indexable(self, category, public_site):
        payload = category_seo_payload(category, lang="uz", page=1)

        assert payload["robots"] == "index, follow"
        assert payload["canonical"] == f"https://ctsale.uz/uz/category/{category.slug}"

    def test_later_pages_are_not_indexed(self, category, public_site):
        """2-sahifadan boshlab kontent deyarli bir xil — duplicate
        content sifatida indeksga tushmasligi kerak."""
        payload = category_seo_payload(category, lang="uz", page=3)

        assert payload["robots"] == "noindex, follow"
        assert payload["canonical"].endswith("?page=3")

    def test_custom_meta_is_used(self, category, public_site):
        category.meta_title = "Maxsus sarlavha"
        category.meta_description = "Maxsus tavsif"
        category.save()

        payload = category_seo_payload(category, lang="uz")

        assert payload["title"] == "Maxsus sarlavha"
        assert payload["description"] == "Maxsus tavsif"

    def test_translated_name_is_used(self, category, public_site):
        category.name_ru = "Игровые ноутбуки"
        category.save()

        payload = category_seo_payload(category, lang="ru")

        assert "Игровые ноутбуки" in payload["title"]

    def test_unknown_language_falls_back(self, category, public_site):
        payload = category_seo_payload(category, lang="de")

        assert "/uz/category/" in payload["canonical"]
