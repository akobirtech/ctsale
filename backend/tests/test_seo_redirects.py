"""301 / 302 / 410 — eski manzillar SEO vaznini yo'qotmasligi uchun."""

import pytest

from apps.seo.models import RedirectType, SeoRedirect

pytestmark = pytest.mark.django_db

RESOLVE_URL = "/api/v1/seo/resolve/"


@pytest.fixture
def published(make_product, seller):
    return make_product(seller)


class TestRedirectTable:
    def test_permanent_redirect(self, api):
        SeoRedirect.objects.create(old_path="/eski", new_path="/yangi")

        response = api.get("/uz/eski")

        assert response.status_code == 301
        assert response["Location"] == "/uz/yangi"

    def test_temporary_redirect(self, api):
        SeoRedirect.objects.create(
            old_path="/aksiya", new_path="/catalog", status_code=RedirectType.TEMPORARY
        )

        response = api.get("/uz/aksiya")

        assert response.status_code == 302

    def test_gone_row_returns_410(self, api):
        SeoRedirect.objects.create(old_path="/yopilgan", status_code=RedirectType.GONE)

        response = api.get("/uz/yopilgan")

        assert response.status_code == 410

    def test_inactive_row_is_ignored(self, api):
        SeoRedirect.objects.create(old_path="/eski", new_path="/yangi", is_active=False)

        response = api.get("/uz/eski")

        assert response.status_code == 404

    def test_query_string_is_preserved(self, api):
        SeoRedirect.objects.create(old_path="/eski", new_path="/catalog")

        response = api.get("/uz/eski", {"sort": "price"})

        assert response["Location"] == "/uz/catalog?sort=price"

    def test_hits_are_counted(self, api):
        row = SeoRedirect.objects.create(old_path="/eski", new_path="/yangi")

        api.get("/uz/eski")
        row.refresh_from_db()

        assert row.hits == 1

    def test_language_prefix_is_kept(self, api):
        SeoRedirect.objects.create(old_path="/eski", new_path="/yangi")

        assert api.get("/ru/eski")["Location"] == "/ru/yangi"
        assert api.get("/en/eski")["Location"] == "/en/yangi"

    def test_api_paths_are_never_redirected(self, api):
        """API mijozlari redirect kutmaydi — ular uchun to'siq bor."""
        SeoRedirect.objects.create(old_path="/api/v1/products/", new_path="/yangi")

        response = api.get("/api/v1/products/")

        assert response.status_code == 200


class TestProductSlugChange:
    def test_old_slug_redirects_to_new(self, api, published):
        old_slug = published.slug
        published.title = "Butunlay boshqa sarlavha bo'ldi"
        published.slug = ""
        published.save()
        published.refresh_from_db()

        response = api.get(f"/uz/product/{old_slug}")

        assert response.status_code == 301
        assert response["Location"] == f"/uz/product/{published.slug}"
        assert published.slug != old_slug

    def test_deleted_product_page_returns_410(self, api, published):
        slug = published.slug
        published.delete()  # soft delete

        response = api.get(f"/uz/product/{slug}")

        assert response.status_code == 410

    def test_unknown_slug_still_404(self, api):
        response = api.get("/uz/product/hech-qachon-bolmagan")

        assert response.status_code == 404


class TestResolveEndpoint:
    """SSR server 404 chiqqanda shu endpointdan so'raydi."""

    def test_returns_target(self, api):
        SeoRedirect.objects.create(old_path="/eski", new_path="/yangi")

        response = api.get(RESOLVE_URL, {"path": "/uz/eski"})

        assert response.json() == {"redirect": "/uz/yangi", "status": 301}

    def test_returns_410_without_target(self, api, published):
        slug = published.slug
        published.delete()

        body = api.get(RESOLVE_URL, {"path": f"/uz/product/{slug}"}).json()

        assert body == {"redirect": None, "status": 410}

    def test_missing_redirect(self, api):
        body = api.get(RESOLVE_URL, {"path": "/uz/yoq"}).json()

        assert body == {"redirect": None, "status": 404}

    def test_rejects_non_path_input(self, api):
        body = api.get(RESOLVE_URL, {"path": "https://boshqa-sayt.uz/"}).json()

        assert body["redirect"] is None
