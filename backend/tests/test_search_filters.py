"""Qidiruv, filtrlash va saralash."""

import pytest

from apps.products.models import Condition, ProductStatus

pytestmark = pytest.mark.django_db

LIST_URL = "/api/v1/products/"
SEARCH_URL = "/api/v1/products/search/"


@pytest.fixture
def catalog_data(make_product, seller, other_seller, category, brand):
    """Turli narx, holat va xususiyatga ega bir nechta e'lon."""
    from apps.catalog.models import Brand

    msi = Brand.objects.create(name="MSI", slug="msi")

    return {
        "cheap": make_product(
            seller,
            title="Acer Aspire byudjet noutbuk",
            price=4_000_000,
            condition=Condition.FAIR,
            specs={"cpu": "Intel i3", "ram_gb": 8, "os": "linux"},
        ),
        "mid": make_product(
            seller,
            title="ASUS ROG Strix gaming noutbuk",
            price=12_000_000,
            condition=Condition.GOOD,
            specs={"cpu": "Intel Core i7", "ram_gb": 16, "os": "win11"},
        ),
        "expensive": make_product(
            other_seller,
            title="MSI Titan kuchli noutbuk",
            price=30_000_000,
            condition=Condition.NEW,
            brand=msi,
            specs={"cpu": "Intel Core i9", "ram_gb": 64, "os": "win11"},
        ),
    }


class TestFullTextSearch:
    def test_finds_by_title_words(self, api, catalog_data):
        response = api.get(SEARCH_URL, {"q": "ROG Strix"})

        titles = [item["title"] for item in response.data["results"]]
        assert any("ROG Strix" in title for title in titles)

    def test_short_query_is_rejected(self, api, catalog_data):
        response = api.get(SEARCH_URL, {"q": "a"})

        assert response.status_code == 400
        assert response.data["error"]["code"] == "query_too_short"

    def test_typo_falls_back_to_trigram(self, api, catalog_data):
        """`noutbukk` full-text bilan topilmaydi, trigram bilan topiladi."""
        response = api.get(SEARCH_URL, {"q": "noutbukk"})

        assert response.status_code == 200
        assert response.data["count"] > 0

    def test_no_results_returns_suggestions(self, api, catalog_data):
        response = api.get(SEARCH_URL, {"q": "xolodilnik"})

        assert response.data["count"] == 0
        assert "suggestions" in response.data

    def test_search_is_logged(self, api, catalog_data):
        from apps.products.models import SearchQueryLog

        api.get(SEARCH_URL, {"q": "gaming"})

        log = SearchQueryLog.objects.latest("created_at")
        assert log.query == "gaming"

    def test_drafts_are_not_searchable(self, api, make_product, seller):
        make_product(seller, status=ProductStatus.DRAFT, title="Maxfiy qoralama noutbuk")

        response = api.get(SEARCH_URL, {"q": "Maxfiy qoralama"})

        assert response.data["count"] == 0

    def test_autocomplete_returns_products_and_categories(self, api, catalog_data):
        response = api.get("/api/v1/products/autocomplete/", {"q": "nou"})

        assert response.status_code == 200
        assert "products" in response.data
        assert "categories" in response.data


class TestPriceFilters:
    def test_min_price(self, api, catalog_data):
        response = api.get(LIST_URL, {"price_min": 10_000_000})

        prices = [float(item["price"]) for item in response.data["results"]]
        assert all(price >= 10_000_000 for price in prices)
        assert len(prices) == 2

    def test_max_price(self, api, catalog_data):
        response = api.get(LIST_URL, {"price_max": 5_000_000})

        assert response.data["count"] == 1

    def test_range(self, api, catalog_data):
        response = api.get(LIST_URL, {"price_min": 5_000_000, "price_max": 20_000_000})

        assert response.data["count"] == 1


class TestAttributeFilters:
    def test_condition_filter(self, api, catalog_data):
        response = api.get(LIST_URL, {"condition": Condition.NEW})

        assert response.data["count"] == 1
        assert response.data["results"][0]["condition"] == Condition.NEW

    def test_multiple_conditions(self, api, catalog_data):
        response = api.get(LIST_URL, {"condition": f"{Condition.NEW},{Condition.GOOD}"})

        assert response.data["count"] == 2

    def test_is_new_shortcut(self, api, catalog_data):
        used = api.get(LIST_URL, {"is_new": "false"})
        new = api.get(LIST_URL, {"is_new": "true"})

        assert used.data["count"] == 2
        assert new.data["count"] == 1

    def test_brand_filter(self, api, catalog_data):
        response = api.get(LIST_URL, {"brand": "msi"})

        assert response.data["count"] == 1

    def test_category_includes_descendants(self, api, catalog_data, category):
        """Ota kategoriya tanlansa ichkilari ham chiqishi kerak."""
        response = api.get(LIST_URL, {"category": category.parent.slug})

        assert response.data["count"] == 3

    def test_unknown_category_returns_empty(self, api, catalog_data):
        response = api.get(LIST_URL, {"category": "yoq-bunday"})

        assert response.data["count"] == 0


class TestSpecFilters:
    def test_numeric_minimum(self, api, catalog_data, category):
        response = api.get(LIST_URL, {"category": category.slug, "spec_ram_gb_min": 16})

        assert response.data["count"] == 2

    def test_numeric_range(self, api, catalog_data, category):
        response = api.get(
            LIST_URL,
            {"category": category.slug, "spec_ram_gb_min": 16, "spec_ram_gb_max": 32},
        )

        assert response.data["count"] == 1

    def test_select_filter(self, api, catalog_data, category):
        response = api.get(LIST_URL, {"category": category.slug, "spec_os": "win11"})

        assert response.data["count"] == 2

    def test_multiple_select_values(self, api, catalog_data, category):
        response = api.get(LIST_URL, {"category": category.slug, "spec_os": "win11,linux"})

        assert response.data["count"] == 3

    def test_spec_filter_ignored_without_category(self, api, catalog_data):
        """Kategoriyasiz sxema noma'lum — filtr e'tiborsiz qoldiriladi,
        aks holda ixtiyoriy JSONB yo'li bo'ylab so'rov yuborish mumkin bo'lardi."""
        response = api.get(LIST_URL, {"spec_ram_gb_min": 999})

        assert response.data["count"] == 3

    def test_unknown_spec_code_is_ignored(self, api, catalog_data, category):
        response = api.get(LIST_URL, {"category": category.slug, "spec_hech_narsa": "x"})

        assert response.data["count"] == 3

    def test_invalid_numeric_value_is_ignored(self, api, catalog_data, category):
        response = api.get(LIST_URL, {"category": category.slug, "spec_ram_gb_min": "ko'p"})

        assert response.status_code == 200
        assert response.data["count"] == 3


class TestSorting:
    def test_price_ascending(self, api, catalog_data):
        response = api.get(LIST_URL, {"sort": "price_asc"})

        prices = [float(item["price"]) for item in response.data["results"]]
        assert prices == sorted(prices)

    def test_price_descending(self, api, catalog_data):
        response = api.get(LIST_URL, {"sort": "price_desc"})

        prices = [float(item["price"]) for item in response.data["results"]]
        assert prices == sorted(prices, reverse=True)

    def test_featured_stay_on_top(self, api, catalog_data):
        cheap = catalog_data["cheap"]
        cheap.is_featured = True
        cheap.save()

        response = api.get(LIST_URL, {"sort": "price_desc"})

        assert response.data["results"][0]["id"] == str(cheap.id)

    def test_priceless_excluded_from_price_sort(self, api, catalog_data, make_product, seller):
        make_product(seller, price=None, is_negotiable=True, title="Kelishiladigan e'lon")

        response = api.get(LIST_URL, {"sort": "price_asc"})

        titles = [item["title"] for item in response.data["results"]]
        assert "Kelishiladigan e'lon" not in titles

    def test_default_sort_is_newest(self, api, catalog_data):
        response = api.get(LIST_URL)

        assert response.data["applied_sort"] == "newest"


class TestFacets:
    def test_facets_are_returned_on_request(self, api, catalog_data, category):
        response = api.get(LIST_URL, {"category": category.slug, "facets": "true"})

        facets = response.data["facets"]
        assert "condition" in facets
        assert "brand" in facets
        assert "price" in facets
        assert "specs" in facets

    def test_facet_counts_match(self, api, catalog_data):
        response = api.get(LIST_URL, {"facets": "true"})

        conditions = {row["value"]: row["count"] for row in response.data["facets"]["condition"]}
        assert conditions[Condition.NEW] == 1

    def test_price_range_reflects_data(self, api, catalog_data):
        response = api.get(LIST_URL, {"facets": "true"})

        price = response.data["facets"]["price"]
        assert price["min"] == 4_000_000
        assert price["max"] == 30_000_000

    def test_spec_facets_use_readable_labels(self, api, catalog_data, category):
        response = api.get(LIST_URL, {"category": category.slug, "facets": "true"})

        os_facet = next(s for s in response.data["facets"]["specs"] if s["code"] == "os")
        labels = {option["label"] for option in os_facet["options"]}
        assert "Windows 11" in labels

    def test_facets_omitted_by_default(self, api, catalog_data):
        response = api.get(LIST_URL)

        assert "facets" not in response.data


class TestPagination:
    def test_page_size_is_respected(self, api, catalog_data):
        response = api.get(LIST_URL, {"page_size": 2})

        assert len(response.data["results"]) == 2
        assert response.data["pages"] == 2

    def test_second_page(self, api, catalog_data):
        response = api.get(LIST_URL, {"page_size": 2, "page": 2})

        assert response.data["page"] == 2
        assert response.data["previous"] is not None
