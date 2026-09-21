"""So'rovlar sonini qo'riqlaydigan testlar.

Bu testlar tezlikni emas, **SQL so'rovlar sonini** o'lchaydi. Sabab:
serializerga bitta `SerializerMethodField` qo'shish oson, lekin u
ro'yxatdagi har bir element uchun qo'shimcha so'rov yuborsa, katalog
jimgina 3 barobar sekinlashadi. Bunday regressiya kod ko'rigida
ko'rinmaydi — faqat o'lchov ushlaydi.

Chegaralar biroz bo'sh qo'yilgan: maqsad aniq raqamni qotirib qo'yish
emas, N+1 qaytganini sezish.
"""

import pytest
from django.test.utils import CaptureQueriesContext
from django.db import connection

from apps.products.models import Condition, ProductStatus

pytestmark = pytest.mark.django_db


@pytest.fixture
def many_products(make_product, seller, other_seller, category, brand):
    """Turli kategoriyadagi 20 ta e'lon.

    Bitta kategoriya bilan N+1 sezilmaydi — sxema bir marta o'qilib
    keshlanadi. Shuning uchun kategoriyalar xilma-xil bo'lishi kerak.
    """
    from apps.catalog.models import AttributeDefinition, AttributeType, Category

    categories = [category]
    for index in range(3):
        extra = Category.objects.create(
            name_uz=f"Bo'lim {index}",
            slug=f"bolim-{index}",
            parent=category.parent,
            is_active=True,
        )
        AttributeDefinition.objects.create(
            category=extra,
            code=f"attr_{index}",
            label_uz=f"Xususiyat {index}",
            data_type=AttributeType.TEXT,
            is_in_card=True,
        )
        categories.append(extra)

    products = []
    for index in range(20):
        target = categories[index % len(categories)]
        products.append(
            make_product(
                seller if index % 2 else other_seller,
                title=f"Mahsulot raqami {index}",
                category=target,
                price=1_000_000 + index * 500_000,
                specs={"cpu": f"CPU {index}", "ram_gb": 8 + index, f"attr_{index % 3}": "x"},
            )
        )
    return products


def count_queries(client, url):
    client.get(url)  # keshni isitish (xususiyat sxemasi)
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(url)
    return response, len(ctx)


class TestQueryBudget:
    """Har bir endpoint uchun so'rovlar soni chegarasi."""

    def test_catalog_does_not_scale_with_result_count(self, api, many_products):
        """Asosiy tekshiruv: 5 ta va 20 ta natija uchun so'rovlar soni
        deyarli bir xil bo'lishi kerak."""
        _, few = count_queries(api, "/api/v1/products/?page_size=5")
        _, many = count_queries(api, "/api/v1/products/?page_size=20")

        assert many - few <= 2, (
            f"Natija soni 4 barobar oshganda so'rovlar {few} dan {many} ga chiqdi — "
            "N+1 belgisi"
        )

    def test_catalog_query_budget(self, api, many_products):
        response, count = count_queries(api, "/api/v1/products/?page_size=20")

        assert response.status_code == 200
        assert count <= 12, f"Katalog {count} ta so'rov yubordi"

    def test_catalog_with_facets_budget(self, api, many_products):
        response, count = count_queries(
            api, "/api/v1/products/?page_size=20&facets=true"
        )

        assert response.status_code == 200
        assert count <= 20, f"Facetlar bilan {count} ta so'rov"

    def test_category_page_budget(self, api, many_products, category):
        response, count = count_queries(
            api, f"/api/v1/products/?category={category.parent.slug}&facets=true"
        )

        assert response.status_code == 200
        assert count <= 20, f"Kategoriya sahifasi {count} ta so'rov"

    def test_home_blocks_budget(self, api, many_products):
        """Bosh sahifa to'rtta blokni bitta so'rovda qaytaradi."""
        response, count = count_queries(api, "/api/v1/products/featured/?limit=8")

        assert response.status_code == 200
        assert count <= 15, f"Bosh sahifa {count} ta so'rov"

    def test_product_detail_budget(self, api, product):
        response, count = count_queries(api, f"/api/v1/products/{product.slug}/")

        assert response.status_code == 200
        assert count <= 12, f"Mahsulot sahifasi {count} ta so'rov"

    def test_search_budget(self, api, many_products):
        response, count = count_queries(api, "/api/v1/products/search/?q=Mahsulot")

        assert response.status_code == 200
        assert count <= 12, f"Qidiruv {count} ta so'rov"

    def test_category_tree_budget(self, api, many_products):
        """Butun daraxt bitta so'rovda o'qilishi kerak — rekursiv
        so'rovlar bo'lmasin."""
        response, count = count_queries(api, "/api/v1/categories/tree/")

        assert response.status_code == 200
        assert count <= 3, f"Kategoriya daraxti {count} ta so'rov"

    def test_sitemap_budget(self, api, many_products):
        response, count = count_queries(api, "/sitemap-products-uz-1.xml")

        assert response.status_code == 200
        assert count <= 5, f"Sitemap {count} ta so'rov"


class TestSimilarProducts:
    """`similar` endpointi uzoq vaqt umuman sinalmagan edi va
    `Decimal * float` xatosi tufayli 500 qaytarardi."""

    def test_returns_products_from_same_category(self, api, many_products, category):
        target = next(p for p in many_products if p.category_id == category.id)

        response = api.get(f"/api/v1/products/{target.slug}/similar/")

        assert response.status_code == 200
        assert all(item["category"] == category.id for item in response.data)

    def test_excludes_itself(self, api, product, make_product, seller):
        make_product(seller, title="Boshqa mahsulot")

        response = api.get(f"/api/v1/products/{product.slug}/similar/")

        assert str(product.id) not in [item["id"] for item in response.data]

    def test_works_for_product_without_price(self, api, make_product, seller):
        """Narxsiz e'londa narx oralig'i hisoblanmasligi kerak."""
        product = make_product(seller, price=None, is_negotiable=True)

        response = api.get(f"/api/v1/products/{product.slug}/similar/")

        assert response.status_code == 200

    def test_decimal_price_does_not_crash(self, api, make_product, seller):
        """Narx Decimal — float bilan ko'paytirilsa TypeError bo'lardi."""
        from decimal import Decimal

        product = make_product(seller, price=Decimal("12500000.50"))

        response = api.get(f"/api/v1/products/{product.slug}/similar/")

        assert response.status_code == 200

    def test_drafts_are_not_suggested(self, api, product, make_product, seller):
        make_product(seller, status=ProductStatus.DRAFT, title="Yashirin qoralama")

        response = api.get(f"/api/v1/products/{product.slug}/similar/")

        titles = [item["title"] for item in response.data]
        assert "Yashirin qoralama" not in titles

    def test_similar_budget(self, api, many_products, category):
        target = next(p for p in many_products if p.category_id == category.id)

        response, count = count_queries(api, f"/api/v1/products/{target.slug}/similar/")

        assert response.status_code == 200
        assert count <= 10, f"O'xshash mahsulotlar {count} ta so'rov"


class TestAttributeCache:
    def test_schema_is_read_once_per_category(self, category, django_assert_num_queries):
        """Ikkinchi chaqiruv keshdan kelishi kerak."""
        from django.core.cache import cache

        cache.clear()
        category.inherited_attributes()          # birinchisi bazadan

        with django_assert_num_queries(0):
            category.inherited_attributes()      # ikkinchisi keshdan

    def test_cache_is_invalidated_on_schema_change(self, category):
        from apps.catalog.models import AttributeDefinition, AttributeType

        before = len(category.inherited_attributes())

        AttributeDefinition.objects.create(
            category=category,
            code="yangi_xususiyat",
            label_uz="Yangi",
            data_type=AttributeType.TEXT,
        )

        after = len(category.inherited_attributes())
        assert after == before + 1, "Sxema o'zgarganda kesh yangilanmadi"

    def test_cache_is_invalidated_on_category_move(self, category):
        """Kategoriya boshqa otaga ko'chirilsa meros o'zgaradi."""
        from apps.catalog.models import Category

        before = len(category.inherited_attributes())

        orphan = Category.objects.create(name_uz="Ildiz", slug="ildiz", is_active=True)
        category.parent = orphan
        category.save()

        after = len(category.inherited_attributes())
        # Eski otadagi `warranty_months` endi meros olinmaydi.
        assert after < before

    def test_descendants_are_cached(self, category, django_assert_num_queries):
        from django.core.cache import cache

        cache.clear()
        category.parent.descendant_ids()

        with django_assert_num_queries(0):
            category.parent.descendant_ids()


class TestFeaturedCache:
    """Bosh sahifa keshi mehmonlar uchun yoqilgan.

    Eng katta xavf: javobda `is_favorited` bor va u foydalanuvchiga
    bog'liq. Kesh noto'g'ri qo'llansa bir foydalanuvchining sevimlilari
    boshqasiga ko'rinib qolardi.
    """

    def test_anonymous_response_is_cached(self, api, product):
        from django.core.cache import cache

        cache.clear()
        api.get("/api/v1/products/featured/")

        with CaptureQueriesContext(connection) as ctx:
            response = api.get("/api/v1/products/featured/")

        assert response.status_code == 200
        assert len(ctx) == 0, "Ikkinchi so'rov keshdan kelishi kerak edi"

    def test_logged_in_user_never_gets_cached_response(
        self, api, auth_client, user, product
    ):
        """Mehmon javobi keshlangandan keyin ham kirgan foydalanuvchi
        o'z sevimlilarini ko'rishi kerak."""
        from apps.interactions.models import Favorite
        from django.core.cache import cache

        cache.clear()
        api.get("/api/v1/products/featured/")          # keshni to'ldiramiz
        Favorite.objects.create(user=user, product=product)

        response = auth_client(user).get("/api/v1/products/featured/")

        item = next(p for p in response.data["newest"] if p["id"] == str(product.id))
        assert item["is_favorited"] is True, "Kirgan foydalanuvchiga kesh berildi"

    def test_one_users_favorites_do_not_leak_to_another(
        self, auth_client, user, other_seller, product
    ):
        from apps.interactions.models import Favorite
        from django.core.cache import cache

        cache.clear()
        Favorite.objects.create(user=user, product=product)

        mine = auth_client(user).get("/api/v1/products/featured/")
        theirs = auth_client(other_seller).get("/api/v1/products/featured/")

        def favorited(response):
            item = next(p for p in response.data["newest"] if p["id"] == str(product.id))
            return item["is_favorited"]

        assert favorited(mine) is True
        assert favorited(theirs) is False

    def test_cache_is_separate_per_language(self, api, product):
        from django.core.cache import cache

        cache.clear()
        uz = api.get("/api/v1/products/featured/?lang=uz")
        ru = api.get("/api/v1/products/featured/?lang=ru")

        assert uz.status_code == ru.status_code == 200
        # Ikkalasi ham to'ldirilgan bo'lishi kerak, kesh aralashmasligi
        assert len(uz.data["newest"]) == len(ru.data["newest"])

    def test_limit_is_clamped(self, api, product):
        too_big = api.get("/api/v1/products/featured/?limit=999")
        invalid = api.get("/api/v1/products/featured/?limit=abc")

        assert too_big.status_code == 200
        assert invalid.status_code == 200
        assert len(too_big.data["newest"]) <= 24
