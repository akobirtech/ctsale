"""Admin paneldagi e'lonlar jadvali: filtr, VIP, arxiv, ommaviy amallar."""

import pytest

from apps.analytics.models import AuditLog
from apps.products.models import Product, ProductStatus

pytestmark = pytest.mark.django_db

URL = "/api/v1/admin/products/"


@pytest.fixture
def listings(make_product, seller, other_seller):
    """Har xil holatdagi e'lonlar — filtrlarni tekshirish uchun."""
    return {
        "approved": make_product(seller, title="Lenovo ThinkPad T14"),
        "draft": make_product(seller, status=ProductStatus.DRAFT, title="Qoralama e'lon"),
        "pending": make_product(
            other_seller, status=ProductStatus.PENDING, title="MSI Katana GF66"
        ),
    }


class TestAccess:
    def test_anonymous_is_rejected(self, api):
        assert api.get(URL).status_code == 401

    def test_plain_user_is_rejected(self, auth_client, user, listings):
        assert auth_client(user).get(URL).status_code == 403

    def test_moderator_can_view(self, auth_client, moderator, listings):
        assert auth_client(moderator).get(URL).status_code == 200


class TestListing:
    def test_drafts_are_visible_to_admin(self, auth_client, admin, listings):
        """Ommaviy API qoralamani ko'rsatmaydi, admin jadvali ko'rsatadi."""
        response = auth_client(admin).get(URL)

        slugs = [row["slug"] for row in response.data["results"]]
        assert listings["draft"].slug in slugs

    def test_status_counts_are_included(self, auth_client, admin, listings):
        response = auth_client(admin).get(URL)

        counts = response.data["status_counts"]
        assert counts[ProductStatus.DRAFT] == 1
        assert counts[ProductStatus.PENDING] == 1

    def test_filter_by_status(self, auth_client, admin, listings):
        response = auth_client(admin).get(URL, {"status": ProductStatus.PENDING})

        assert [row["slug"] for row in response.data["results"]] == [
            listings["pending"].slug
        ]

    def test_filter_by_several_statuses(self, auth_client, admin, listings):
        response = auth_client(admin).get(
            URL, {"status": f"{ProductStatus.DRAFT},{ProductStatus.PENDING}"}
        )

        assert response.data["count"] == 2

    def test_search_by_seller_phone(self, auth_client, admin, listings, other_seller):
        response = auth_client(admin).get(URL, {"search": other_seller.phone[-7:]})

        assert [row["slug"] for row in response.data["results"]] == [
            listings["pending"].slug
        ]

    def test_search_by_title(self, auth_client, admin, listings):
        response = auth_client(admin).get(URL, {"search": "katana"})

        assert response.data["count"] == 1

    def test_deleted_are_hidden_by_default(self, auth_client, admin, listings):
        listings["draft"].delete()

        response = auth_client(admin).get(URL)

        assert listings["draft"].slug not in [r["slug"] for r in response.data["results"]]

    def test_deleted_can_be_requested(self, auth_client, admin, listings):
        listings["draft"].delete()

        response = auth_client(admin).get(URL, {"deleted": "true"})

        assert [r["slug"] for r in response.data["results"]] == [listings["draft"].slug]

    def test_row_carries_seller_and_category(self, auth_client, admin, listings, seller):
        response = auth_client(admin).get(URL, {"search": "thinkpad"})

        row = response.data["results"][0]
        assert row["seller_phone"] == seller.phone
        assert row["category_name"]


class TestFeature:
    def test_toggles_on_and_off(self, auth_client, admin, listings):
        product = listings["approved"]
        client = auth_client(admin)

        first = client.post(f"{URL}{product.id}/feature/", {"days": 7}, format="json")
        assert first.data["is_featured"] is True
        assert first.data["featured_until"] is not None

        second = client.post(f"{URL}{product.id}/feature/", {}, format="json")
        assert second.data["is_featured"] is False
        assert second.data["featured_until"] is None

    def test_moderator_cannot_feature(self, auth_client, moderator, listings):
        response = auth_client(moderator).post(
            f"{URL}{listings['approved'].id}/feature/", {}, format="json"
        )

        assert response.status_code == 403

    def test_is_audited(self, auth_client, admin, listings):
        auth_client(admin).post(f"{URL}{listings['approved'].id}/feature/", {}, format="json")

        assert AuditLog.objects.filter(action="feature").exists()


class TestForceStatus:
    """Bu ruxsat faqat bosh administratorda — holat mashinasini buzadi."""

    def test_bypasses_state_machine(self, auth_client, superadmin, listings):
        """Arxivdan sotilganga o'tish taqiqlangan — bu amal uni chetlab o'tadi."""
        product = listings["draft"]
        product.status = ProductStatus.ARCHIVED
        product.save(update_fields=["status"])
        assert not product.can_transition_to(ProductStatus.SOLD)

        response = auth_client(superadmin).post(
            f"{URL}{product.id}/force-status/",
            {"status": ProductStatus.SOLD, "reason": "Qo'lda tuzatish"},
            format="json",
        )

        product.refresh_from_db()
        assert response.status_code == 200
        assert product.status == ProductStatus.SOLD

    def test_unknown_status_is_rejected(self, auth_client, superadmin, listings):
        response = auth_client(superadmin).post(
            f"{URL}{listings['draft'].id}/force-status/", {"status": "yoq"}, format="json"
        )

        assert response.status_code == 400
        assert response.data["error"]["code"] == "invalid_status"

    def test_same_status_changes_nothing(self, auth_client, superadmin, listings):
        response = auth_client(superadmin).post(
            f"{URL}{listings['draft'].id}/force-status/",
            {"status": ProductStatus.DRAFT},
            format="json",
        )

        assert response.data["changed"] is False

    def test_old_and_new_status_are_audited(self, auth_client, superadmin, listings):
        auth_client(superadmin).post(
            f"{URL}{listings['draft'].id}/force-status/",
            {"status": ProductStatus.ARCHIVED},
            format="json",
        )

        entry = AuditLog.objects.get(action="force_status")
        assert entry.changes["status"] == [ProductStatus.DRAFT, ProductStatus.ARCHIVED]

    def test_admin_without_the_permission_is_rejected(self, auth_client, admin, listings):
        response = auth_client(admin).post(
            f"{URL}{listings['draft'].id}/force-status/",
            {"status": ProductStatus.SOLD},
            format="json",
        )

        assert response.status_code == 403


class TestDeleteAndRestore:
    def test_delete_is_soft(self, auth_client, admin, listings):
        product = listings["approved"]

        response = auth_client(admin).delete(f"{URL}{product.id}/")

        product.refresh_from_db()
        assert response.status_code == 204
        assert product.is_deleted is True

    def test_restore_brings_it_back(self, auth_client, admin, listings):
        product = listings["approved"]
        product.delete()

        response = auth_client(admin).post(f"{URL}{product.id}/restore/", {}, format="json")

        product.refresh_from_db()
        assert response.data["restored"] is True
        assert product.is_deleted is False

    def test_restore_of_live_listing_is_a_no_op(self, auth_client, admin, listings):
        response = auth_client(admin).post(
            f"{URL}{listings['approved'].id}/restore/", {}, format="json"
        )

        assert response.data["restored"] is False

    def test_missing_listing_returns_404(self, auth_client, admin):
        import uuid

        response = auth_client(admin).delete(f"{URL}{uuid.uuid4()}/")

        assert response.status_code == 404


class TestBulk:
    def test_archive_several(self, auth_client, admin, listings):
        ids = [str(listings["draft"].id), str(listings["pending"].id)]

        response = auth_client(admin).post(
            f"{URL}bulk/", {"action": "archive", "ids": ids}, format="json"
        )

        assert response.data["affected"] == 2
        assert (
            Product.objects.filter(id__in=ids, status=ProductStatus.ARCHIVED).count() == 2
        )

    def test_delete_several(self, auth_client, admin, listings):
        ids = [str(listings["draft"].id)]

        auth_client(admin).post(
            f"{URL}bulk/", {"action": "delete", "ids": ids}, format="json"
        )

        assert Product.all_objects.get(id=ids[0]).is_deleted is True

    def test_empty_selection_is_rejected(self, auth_client, admin):
        response = auth_client(admin).post(
            f"{URL}bulk/", {"action": "archive", "ids": []}, format="json"
        )

        assert response.status_code == 400
        assert response.data["error"]["code"] == "ids_required"

    def test_too_many_is_rejected(self, auth_client, admin):
        import uuid

        response = auth_client(admin).post(
            f"{URL}bulk/",
            {"action": "archive", "ids": [str(uuid.uuid4()) for _ in range(101)]},
            format="json",
        )

        assert response.data["error"]["code"] == "too_many"

    def test_unknown_action_is_rejected(self, auth_client, admin, listings):
        response = auth_client(admin).post(
            f"{URL}bulk/",
            {"action": "yoq", "ids": [str(listings["draft"].id)]},
            format="json",
        )

        assert response.data["error"]["code"] == "invalid_action"

    def test_view_permission_alone_does_not_allow_deleting(
        self, auth_client, moderator, listings
    ):
        """Moderator jadvalni ko'radi, lekin o'chira olmaydi."""
        response = auth_client(moderator).post(
            f"{URL}bulk/",
            {"action": "delete", "ids": [str(listings["draft"].id)]},
            format="json",
        )

        assert response.status_code == 403
        listings["draft"].refresh_from_db()
        assert listings["draft"].is_deleted is False

    def test_already_deleted_are_skipped(self, auth_client, admin, listings):
        listings["draft"].delete()

        response = auth_client(admin).post(
            f"{URL}bulk/",
            {"action": "archive", "ids": [str(listings["draft"].id)]},
            format="json",
        )

        assert response.data["affected"] == 0


class TestAttributeVisibility:
    """Xususiyat sxemasi: kim nimani ko'radi va qanday filtrlaydi."""

    @pytest.fixture
    def attributes(self, category):
        from apps.catalog.models import AttributeDefinition, AttributeType

        active = AttributeDefinition.objects.get(category=category, code="cpu")
        hidden = AttributeDefinition.objects.create(
            category=category,
            code="eskirgan",
            label_uz="Eskirgan xususiyat",
            data_type=AttributeType.TEXT,
            is_active=False,
        )
        return {"active": active, "hidden": hidden}

    def _codes(self, response):
        return [row["code"] for row in response.data]

    def test_filter_by_category_id(self, auth_client, admin, category, attributes):
        response = auth_client(admin).get(f"/api/v1/attributes/?category={category.id}")

        assert response.status_code == 200
        assert attributes["active"].code in self._codes(response)

    def test_filter_by_category_slug(self, api, category, attributes):
        response = api.get(f"/api/v1/attributes/?category={category.slug}")

        assert attributes["active"].code in self._codes(response)

    def test_guests_never_see_inactive(self, api, category, attributes):
        response = api.get(f"/api/v1/attributes/?category={category.slug}")

        assert "eskirgan" not in self._codes(response)

    def test_manager_sees_inactive_to_re_enable_it(
        self, auth_client, admin, category, attributes
    ):
        response = auth_client(admin).get(f"/api/v1/attributes/?category={category.id}")

        assert "eskirgan" in self._codes(response)

    def test_moderator_without_the_permission_does_not(
        self, auth_client, moderator, category, attributes
    ):
        response = auth_client(moderator).get(f"/api/v1/attributes/?category={category.id}")

        assert "eskirgan" not in self._codes(response)
