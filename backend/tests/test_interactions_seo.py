"""Sevimlilar, shikoyatlar, bildirishnomalar va SEO chiqishlari."""

import pytest

from apps.interactions.models import Favorite, Report, ReportReason, ReportStatus
from apps.products.models import ProductStatus

pytestmark = pytest.mark.django_db


class TestFavorites:
    def test_toggle_adds_then_removes(self, auth_client, user, product):
        client = auth_client(user)

        added = client.post("/api/v1/favorites/toggle/", {"slug": product.slug}, format="json")
        removed = client.post("/api/v1/favorites/toggle/", {"slug": product.slug}, format="json")

        assert added.data["is_favorited"] is True
        assert removed.data["is_favorited"] is False
        assert Favorite.objects.count() == 0

    def test_counter_is_kept_in_sync(self, auth_client, user, product):
        auth_client(user).post("/api/v1/favorites/toggle/", {"slug": product.slug}, format="json")

        product.refresh_from_db()
        assert product.favorites_count == 1

    def test_anonymous_cannot_favorite(self, api, product):
        response = api.post("/api/v1/favorites/toggle/", {"slug": product.slug}, format="json")

        assert response.status_code == 401

    def test_unknown_slug_returns_404(self, auth_client, user):
        response = auth_client(user).post(
            "/api/v1/favorites/toggle/", {"slug": "yoq-bunday"}, format="json"
        )

        assert response.status_code == 404

    def test_list_marks_everything_favorited(self, auth_client, user, product):
        client = auth_client(user)
        client.post("/api/v1/favorites/toggle/", {"slug": product.slug}, format="json")

        response = client.get("/api/v1/favorites/")

        assert response.data["count"] == 1
        assert response.data["results"][0]["is_favorited"] is True

    def test_ids_endpoint_is_lightweight(self, auth_client, user, product):
        client = auth_client(user)
        client.post("/api/v1/favorites/toggle/", {"slug": product.slug}, format="json")

        response = client.get("/api/v1/favorites/ids/")

        assert [str(item) for item in response.data["ids"]] == [str(product.id)]

    def test_catalog_marks_favorites_for_logged_in_user(self, auth_client, user, product):
        client = auth_client(user)
        client.post("/api/v1/favorites/toggle/", {"slug": product.slug}, format="json")

        response = client.get("/api/v1/products/")

        assert response.data["results"][0]["is_favorited"] is True


class TestReports:
    def test_report_is_created(self, auth_client, user, product):
        response = auth_client(user).post(
            "/api/v1/reports/",
            {"slug": product.slug, "reason": ReportReason.SCAM},
            format="json",
        )

        assert response.status_code == 201
        assert Report.objects.count() == 1

    def test_cannot_report_own_product(self, auth_client, seller, product):
        response = auth_client(seller).post(
            "/api/v1/reports/",
            {"slug": product.slug, "reason": ReportReason.SCAM},
            format="json",
        )

        assert response.status_code == 400
        assert response.data["error"]["code"] == "own_product"

    def test_other_reason_requires_comment(self, auth_client, user, product):
        response = auth_client(user).post(
            "/api/v1/reports/",
            {"slug": product.slug, "reason": ReportReason.OTHER},
            format="json",
        )

        assert response.status_code == 400
        assert "comment" in response.data["error"]["details"]

    def test_duplicate_report_conflicts(self, auth_client, user, product):
        client = auth_client(user)
        client.post(
            "/api/v1/reports/", {"slug": product.slug, "reason": ReportReason.SPAM}, format="json"
        )

        response = client.post(
            "/api/v1/reports/", {"slug": product.slug, "reason": ReportReason.FAKE}, format="json"
        )

        assert response.status_code == 409
        assert response.data["error"]["code"] == "already_reported"

    def test_staff_can_list_and_resolve(self, auth_client, user, moderator, product):
        auth_client(user).post(
            "/api/v1/reports/", {"slug": product.slug, "reason": ReportReason.SCAM}, format="json"
        )
        report = Report.objects.get()

        listing = auth_client(moderator).get("/api/v1/reports/")
        resolved = auth_client(moderator).post(
            f"/api/v1/reports/{report.id}/resolve/",
            {"status": ReportStatus.DISMISSED, "note": "Asossiz"},
            format="json",
        )

        assert listing.data["count"] == 1
        assert resolved.status_code == 200
        report.refresh_from_db()
        assert report.status == ReportStatus.DISMISSED
        assert report.resolved_by == moderator

    def test_regular_user_cannot_list_reports(self, auth_client, user):
        response = auth_client(user).get("/api/v1/reports/")

        assert response.status_code == 403


class TestPhoneReveal:
    def test_reveal_returns_number_and_counts(self, api, product):
        response = api.post(f"/api/v1/products/{product.slug}/reveal-phone/")

        assert response.status_code == 200
        assert response.data["phone"] == product.seller.phone
        product.refresh_from_db()
        assert product.phone_reveals_count == 1

    def test_phone_is_absent_from_listings(self, api, product):
        listing = api.get("/api/v1/products/")
        detail = api.get(f"/api/v1/products/{product.slug}/")

        assert product.seller.phone not in str(listing.data)
        assert product.seller.phone not in str(detail.data)

    def test_seller_card_shows_masked_phone_only(self, api, product):
        response = api.get(f"/api/v1/products/{product.slug}/")

        masked = response.data["seller"]["masked_phone"]
        assert "***" in masked
        assert masked != product.seller.phone

    def test_repeat_reveal_does_not_double_count(self, api, product):
        api.post(f"/api/v1/products/{product.slug}/reveal-phone/")
        api.post(f"/api/v1/products/{product.slug}/reveal-phone/")

        product.refresh_from_db()
        assert product.phone_reveals_count == 1


class TestNotifications:
    def test_unread_count(self, auth_client, seller, moderator, make_product):
        from apps.products.services import approve_product

        product = make_product(seller, status=ProductStatus.PENDING)
        approve_product(product, actor=moderator)

        response = auth_client(seller).get("/api/v1/notifications/unread-count/")

        assert response.data["count"] == 1

    def test_mark_all_read(self, auth_client, seller, moderator, make_product):
        from apps.products.services import approve_product

        approve_product(make_product(seller, status=ProductStatus.PENDING), actor=moderator)
        client = auth_client(seller)

        client.post("/api/v1/notifications/read-all/")

        assert client.get("/api/v1/notifications/unread-count/").data["count"] == 0

    def test_users_only_see_their_own(self, auth_client, seller, other_seller, moderator, make_product):
        from apps.products.services import approve_product

        approve_product(make_product(seller, status=ProductStatus.PENDING), actor=moderator)

        response = auth_client(other_seller).get("/api/v1/notifications/")

        assert response.data["count"] == 0

    def test_preferences_can_be_updated(self, auth_client, user):
        response = auth_client(user).patch(
            "/api/v1/notifications/preferences/", {"email_enabled": True}, format="json"
        )

        assert response.status_code == 200
        assert response.data["email_enabled"] is True


class TestProductSeoPayload:
    def test_detail_includes_full_seo_block(self, api, product):
        response = api.get(f"/api/v1/products/{product.slug}/")

        seo = response.data["seo"]
        assert seo["title"]
        assert seo["description"]
        assert seo["canonical"].endswith(f"/uz/product/{product.slug}")
        assert seo["robots"] == "index, follow"

    def test_hreflang_covers_all_languages(self, api, product):
        response = api.get(f"/api/v1/products/{product.slug}/")

        codes = {item["hreflang"] for item in response.data["seo"]["hreflang"]}
        assert codes == {"uz", "ru", "en", "x-default"}

    def test_product_jsonld_shape(self, api, product):
        response = api.get(f"/api/v1/products/{product.slug}/")

        product_schema = response.data["seo"]["jsonld"][0]
        assert product_schema["@type"] == "Product"
        assert product_schema["offers"]["availability"] == "https://schema.org/InStock"
        assert product_schema["offers"]["priceCurrency"] == "UZS"
        assert product_schema["sku"] == str(product.id)

    def test_breadcrumb_jsonld(self, api, product):
        response = api.get(f"/api/v1/products/{product.slug}/")

        breadcrumbs = response.data["seo"]["jsonld"][1]
        assert breadcrumbs["@type"] == "BreadcrumbList"
        names = [item["name"] for item in breadcrumbs["itemListElement"]]
        assert names[-1] == product.title

    def test_sold_product_is_still_indexable(self, api, seller, make_product):
        sold = make_product(seller, status=ProductStatus.SOLD)

        response = api.get(f"/api/v1/products/{sold.slug}/")

        seo = response.data["seo"]
        assert seo["robots"] == "index, follow"
        assert seo["jsonld"][0]["offers"]["availability"] == "https://schema.org/SoldOut"

    def test_sold_indexing_can_be_disabled(self, api, seller, make_product):
        from apps.seo.models import SeoSettings

        config = SeoSettings.load()
        config.index_sold_products = False
        config.save()
        sold = make_product(seller, status=ProductStatus.SOLD)

        response = api.get(f"/api/v1/products/{sold.slug}/")

        assert response.data["seo"]["robots"] == "noindex, follow"

    def test_draft_is_never_indexable(self, auth_client, seller, make_product):
        draft = make_product(seller, status=ProductStatus.DRAFT)

        response = auth_client(seller).get(f"/api/v1/products/{draft.slug}/")

        assert response.data["seo"]["robots"] == "noindex, follow"


class TestRobotsAndSitemap:
    def test_robots_lists_sitemaps_and_blocks_private_paths(self, api):
        response = api.get("/robots.txt")
        body = response.content.decode()

        assert response.status_code == 200
        assert "Sitemap:" in body
        assert "Disallow: /admin" in body
        assert "Disallow: /uz/profile" in body
        assert "User-agent: Yandex" in body

    def test_robots_blocks_everything_when_indexing_disabled(self, api, settings):
        settings.SEO_ALLOW_INDEXING = False

        body = api.get("/robots.txt").content.decode()

        assert "Disallow: /" in body
        assert "Sitemap:" not in body

    def test_sitemap_index_lists_languages(self, api):
        body = api.get("/sitemap.xml").content.decode()

        for lang in ("uz", "ru", "en"):
            assert f"sitemap-{lang}.xml" in body

    def test_product_sitemap_contains_hreflang(self, api, product):
        body = api.get("/sitemap-products-uz-1.xml").content.decode()

        assert f"/uz/product/{product.slug}" in body
        assert 'hreflang="x-default"' in body

    def test_draft_is_absent_from_sitemap(self, api, seller, make_product):
        draft = make_product(seller, status=ProductStatus.DRAFT, title="Yashirin qoralama")

        body = api.get("/sitemap-products-uz-1.xml").content.decode()

        assert draft.slug not in body

    def test_unknown_language_returns_404(self, api):
        assert api.get("/sitemap-de.xml").status_code == 404

    def test_empty_categories_are_skipped(self, api, category, product):
        """Mahsulotsiz kategoriya indeksga tushmasin — thin content."""
        from apps.catalog.models import Category

        Category.objects.create(name_uz="Bo'sh bo'lim", slug="bosh-bolim", is_active=True)

        body = api.get("/sitemap-categories-uz.xml").content.decode()

        assert "bosh-bolim" not in body

    def test_xml_is_well_formed(self, api, product):
        import xml.etree.ElementTree as ET

        for path in ("/sitemap.xml", "/sitemap-uz.xml", "/sitemap-products-uz-1.xml"):
            body = api.get(path).content
            ET.fromstring(body)  # xato bo'lsa istisno otadi


class TestSecurityHeaders:
    def test_security_headers_are_present(self, api):
        response = api.get("/api/v1/health/")

        assert response["X-Content-Type-Options"] == "nosniff"
        assert "Content-Security-Policy" in response
        assert response["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "frame-ancestors 'none'" in response["Content-Security-Policy"]

    def test_authenticated_api_responses_are_not_cached(self, auth_client, user):
        response = auth_client(user).get("/api/v1/auth/me/")

        assert "no-store" in response.get("Cache-Control", "")
