"""Profil (avatar), do'kon profili va sotuvchi statistikasi."""

import pytest

from apps.accounts.models import ShopProfile
from apps.products.models import ProductStatus

pytestmark = pytest.mark.django_db

ME_URL = "/api/v1/auth/me/"
SHOP_URL = "/api/v1/auth/shop/"
STATS_URL = "/api/v1/products/my-stats/"


class TestAvatarUpload:
    def test_uploads_a_real_image(self, auth_client, user, image_file):
        response = auth_client(user).patch(
            ME_URL, {"avatar": image_file()}, format="multipart"
        )

        user.refresh_from_db()
        assert response.status_code == 200
        assert user.avatar.name

    def test_rejects_a_disguised_file(self, auth_client, user, fake_image_file):
        """`.jpg` deb nomlangan matn fayli — magic bytes ushlaydi."""
        response = auth_client(user).patch(
            ME_URL, {"avatar": fake_image_file}, format="multipart"
        )

        user.refresh_from_db()
        assert response.status_code == 400
        assert "avatar" in response.data["error"]["details"]
        assert not user.avatar

    def test_can_be_removed(self, auth_client, user, image_file):
        client = auth_client(user)
        client.patch(ME_URL, {"avatar": image_file()}, format="multipart")

        response = client.patch(ME_URL, {"avatar": ""}, format="multipart")

        user.refresh_from_db()
        assert response.status_code == 200
        assert not user.avatar

    def test_anonymous_cannot_upload(self, api, image_file):
        response = api.patch(ME_URL, {"avatar": image_file()}, format="multipart")

        assert response.status_code == 401


class TestShopProfile:
    def test_missing_profile_returns_404(self, auth_client, seller):
        assert auth_client(seller).get(SHOP_URL).status_code == 404

    def test_first_put_creates_it(self, auth_client, seller):
        response = auth_client(seller).put(
            SHOP_URL,
            {"name": "CT Komputer", "address": "Toshkent, Chilonzor"},
            format="json",
        )

        assert response.status_code == 201
        assert response.data["slug"] == "ct-komputer"
        assert ShopProfile.objects.filter(user=seller).count() == 1

    def test_second_put_updates_instead_of_duplicating(self, auth_client, seller):
        client = auth_client(seller)
        client.put(SHOP_URL, {"name": "CT Komputer"}, format="json")

        response = client.put(SHOP_URL, {"name": "CT Komputer Plus"}, format="json")

        assert response.status_code == 200
        assert ShopProfile.objects.filter(user=seller).count() == 1

    def test_patch_keeps_other_fields(self, auth_client, seller):
        client = auth_client(seller)
        client.put(SHOP_URL, {"name": "CT Komputer", "address": "Chilonzor"}, format="json")

        response = client.patch(SHOP_URL, {"working_hours": "Du-Sha 9:00-18:00"}, format="json")

        assert response.data["address"] == "Chilonzor"
        assert response.data["working_hours"] == "Du-Sha 9:00-18:00"

    def test_short_name_is_rejected(self, auth_client, seller):
        response = auth_client(seller).put(SHOP_URL, {"name": "C"}, format="json")

        assert response.status_code == 400

    def test_slug_is_read_only(self, auth_client, seller):
        response = auth_client(seller).put(
            SHOP_URL, {"name": "CT Komputer", "slug": "men-tanladim"}, format="json"
        )

        assert response.data["slug"] == "ct-komputer"

    def test_logo_must_be_a_real_image(self, auth_client, seller, fake_image_file):
        response = auth_client(seller).put(
            SHOP_URL, {"name": "CT Komputer", "logo": fake_image_file}, format="multipart"
        )

        assert response.status_code == 400

    def test_delete_removes_it(self, auth_client, seller):
        client = auth_client(seller)
        client.put(SHOP_URL, {"name": "CT Komputer"}, format="json")

        response = client.delete(SHOP_URL)

        assert response.status_code == 204
        assert not ShopProfile.objects.filter(user=seller).exists()

    def test_profile_appears_in_me(self, auth_client, seller):
        client = auth_client(seller)
        client.put(SHOP_URL, {"name": "CT Komputer"}, format="json")

        response = client.get(ME_URL)

        assert response.data["shop"]["name"] == "CT Komputer"

    def test_one_seller_cannot_see_anothers_shop(self, auth_client, seller, other_seller):
        auth_client(seller).put(SHOP_URL, {"name": "CT Komputer"}, format="json")

        response = auth_client(other_seller).get(SHOP_URL)

        assert response.status_code == 404


class TestSellerStats:
    @pytest.fixture
    def listings(self, make_product, seller):
        approved = make_product(seller, title="Ko'rilgan e'lon")
        approved.views_count = 40
        approved.favorites_count = 5
        approved.phone_reveals_count = 3
        approved.save()
        make_product(seller, status=ProductStatus.DRAFT)
        return approved

    def test_requires_login(self, api):
        assert api.get(STATS_URL).status_code == 401

    def test_totals_sum_the_counters(self, auth_client, seller, listings):
        response = auth_client(seller).get(STATS_URL)

        totals = response.data["totals"]
        assert totals["total"] == 2
        assert totals["views"] == 40
        assert totals["phone_reveals"] == 3

    def test_breakdown_by_status(self, auth_client, seller, listings):
        response = auth_client(seller).get(STATS_URL)

        assert response.data["by_status"][ProductStatus.DRAFT] == 1

    def test_top_products_exclude_drafts(self, auth_client, seller, listings):
        response = auth_client(seller).get(STATS_URL)

        slugs = [row["slug"] for row in response.data["top_products"]]
        assert slugs == [listings.slug]

    def test_another_sellers_numbers_do_not_leak(
        self, auth_client, seller, other_seller, listings
    ):
        response = auth_client(other_seller).get(STATS_URL)

        assert response.data["totals"]["total"] == 0

    def test_daily_views_are_grouped(self, auth_client, seller, listings, api):
        api.get(f"/api/v1/products/{listings.slug}/")

        response = auth_client(seller).get(STATS_URL)

        daily = response.data["views_daily"]
        assert len(daily) == 1
        assert daily[0]["count"] == 1

    def test_days_parameter_is_clamped(self, auth_client, seller, listings):
        too_big = auth_client(seller).get(STATS_URL, {"days": 999})
        too_small = auth_client(seller).get(STATS_URL, {"days": 1})

        assert too_big.data["days"] == 90
        assert too_small.data["days"] == 7

    def test_deleted_listings_are_not_counted(self, auth_client, seller, listings):
        listings.delete()

        response = auth_client(seller).get(STATS_URL)

        assert response.data["totals"]["total"] == 1

