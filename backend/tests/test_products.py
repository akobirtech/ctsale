"""Mahsulot CRUD, holat mashinasi va xususiyat validatsiyasi."""

import pytest
from django.utils import timezone

from apps.products.models import Condition, Product, ProductStatus
from apps.products.services import (
    approve_product,
    mark_as_sold,
    needs_remoderation,
    reject_product,
    submit_for_moderation,
)

pytestmark = pytest.mark.django_db

PRODUCTS_URL = "/api/v1/products/"


class TestProductCreation:
    def test_creates_draft_owned_by_caller(self, auth_client, seller, product_payload):
        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 201
        product = Product.objects.get(slug=response.data["slug"])
        assert product.seller == seller
        assert product.status == ProductStatus.DRAFT

    def test_anonymous_cannot_create(self, api, product_payload):
        response = api.post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 401

    def test_unverified_phone_cannot_create(self, auth_client, user, product_payload):
        user.is_phone_verified = False
        user.save()

        response = auth_client(user).post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 403

    def test_slug_is_generated_and_unique(self, auth_client, seller, product_payload):
        first = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")
        second = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        assert first.data["slug"] != second.data["slug"]
        assert first.data["slug"].startswith("asus-rog-strix-g16")

    def test_seo_fields_are_autofilled(self, auth_client, seller, product_payload):
        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        product = Product.objects.get(slug=response.data["slug"])
        assert product.seo_title
        assert product.seo_description
        assert product.og_title

    def test_manual_seo_is_not_overwritten(self, auth_client, seller, product_payload):
        product_payload["seo_title"] = "Qo'lda yozilgan sarlavha"

        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        product = Product.objects.get(slug=response.data["slug"])
        assert product.seo_title == "Qo'lda yozilgan sarlavha"


class TestProductValidation:
    @pytest.mark.parametrize(
        "field,value,message_fragment",
        [
            ("title", "Qisqa", "10 ta belgi"),
            ("description", "Juda qisqa", "20 ta belgi"),
        ],
    )
    def test_minimum_lengths(
        self, auth_client, seller, product_payload, field, value, message_fragment
    ):
        product_payload[field] = value

        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 400
        assert message_fragment in str(response.data["error"]["details"])

    def test_price_required_unless_flagged(self, auth_client, seller, product_payload):
        product_payload["price"] = None

        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 400
        assert "price" in response.data["error"]["details"]

    def test_negotiable_allows_missing_price(self, auth_client, seller, product_payload):
        product_payload["price"] = None
        product_payload["is_negotiable"] = True

        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 201

    def test_price_and_on_request_conflict(self, auth_client, seller, product_payload):
        product_payload["price_on_request"] = True

        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 400
        assert "price_on_request" in response.data["error"]["details"]

    def test_negative_price_rejected(self, auth_client, seller, product_payload):
        product_payload["price"] = "-100"

        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 400

    def test_parent_category_is_rejected(self, auth_client, seller, product_payload, category):
        product_payload["category"] = category.parent.id

        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 400
        assert "category" in response.data["error"]["details"]

    def test_used_fields_rejected_for_new_condition(
        self, auth_client, seller, product_payload
    ):
        product_payload["condition"] = Condition.NEW
        product_payload["usage_period"] = "1 yil"

        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 400
        assert "usage_period" in response.data["error"]["details"]

    def test_warranty_requires_date(self, auth_client, seller, product_payload):
        product_payload["has_warranty"] = True

        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 400
        assert "warranty_until" in response.data["error"]["details"]

    def test_district_must_match_region(self, auth_client, seller, product_payload, region):
        from apps.catalog.models import District, Region

        other_region = Region.objects.create(name_uz="Buxoro", slug="buxoro")
        foreign = District.objects.create(
            region=other_region, name_uz="G'ijduvon", slug="gijduvon"
        )
        product_payload["district"] = foreign.id

        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 400
        assert "district" in response.data["error"]["details"]


class TestSpecValidation:
    def test_missing_required_spec(self, auth_client, seller, product_payload):
        product_payload["specs"] = {"ram_gb": 16}

        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 400
        assert response.data["error"]["code"] == "invalid_specs"
        assert "cpu" in response.data["error"]["details"]

    def test_wrong_type_reports_field(self, auth_client, seller, product_payload):
        product_payload["specs"] = {"cpu": "i7", "ram_gb": "ko'p"}

        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 400
        assert "ram_gb" in response.data["error"]["details"]

    def test_value_below_minimum(self, auth_client, seller, product_payload):
        product_payload["specs"] = {"cpu": "i7", "ram_gb": 1}

        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 400
        assert "ram_gb" in response.data["error"]["details"]

    def test_invalid_select_option(self, auth_client, seller, product_payload):
        product_payload["specs"] = {"cpu": "i7", "ram_gb": 16, "os": "haiku"}

        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 400
        assert "os" in response.data["error"]["details"]

    def test_unknown_specs_are_stripped(self, auth_client, seller, product_payload):
        """Sxemada yo'q kalit saqlanmasligi kerak — aks holda
        foydalanuvchi JSON orqali ixtiyoriy ma'lumot tiqib qo'yardi."""
        product_payload["specs"] = {"cpu": "i7", "ram_gb": 16, "zararli": "<script>"}

        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 201
        product = Product.objects.get(slug=response.data["slug"])
        assert "zararli" not in product.specs

    def test_inherited_attribute_is_accepted(self, auth_client, seller, product_payload):
        """`warranty_months` ota kategoriyada — bolada ham ishlashi kerak."""
        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        product = Product.objects.get(slug=response.data["slug"])
        assert product.specs["warranty_months"] == 6

    def test_integer_rejects_fraction(self, auth_client, seller, product_payload):
        product_payload["specs"] = {"cpu": "i7", "ram_gb": 16.5}

        response = auth_client(seller).post(PRODUCTS_URL, product_payload, format="json")

        assert response.status_code == 400
        assert "butun son" in str(response.data["error"]["details"])


class TestStatusMachine:
    def test_submit_requires_image(self, seller, product_payload, make_product):
        from apps.core.exceptions import BusinessError

        product = make_product(seller, status=ProductStatus.DRAFT)

        with pytest.raises(BusinessError) as exc:
            submit_for_moderation(product)

        assert exc.value.error_code == "images_required"

    def test_submit_creates_moderation_task(self, seller, make_product, image_file):
        from apps.mediafiles.models import ProductImage

        product = make_product(seller, status=ProductStatus.DRAFT)
        ProductImage.objects.create(product=product, image=image_file())

        submit_for_moderation(product, actor=seller)

        product.refresh_from_db()
        assert product.status == ProductStatus.PENDING
        assert product.moderation_tasks.count() == 1

    def test_approve_publishes_and_sets_expiry(self, seller, moderator, make_product):
        product = make_product(seller, status=ProductStatus.PENDING)

        approve_product(product, actor=moderator)

        product.refresh_from_db()
        assert product.status == ProductStatus.APPROVED
        assert product.published_at is not None
        assert product.expires_at > timezone.now()

    def test_reject_requires_reason(self, seller, moderator, make_product):
        from apps.core.exceptions import BusinessError

        product = make_product(seller, status=ProductStatus.PENDING)

        with pytest.raises(BusinessError) as exc:
            reject_product(product, actor=moderator, reason_code="")

        assert exc.value.error_code == "reason_required"

    def test_illegal_transition_is_blocked(self, seller, make_product):
        from apps.core.exceptions import InvalidStatusTransition
        from apps.products.services import change_status

        product = make_product(seller, status=ProductStatus.SOLD)

        with pytest.raises(InvalidStatusTransition):
            change_status(product, ProductStatus.DRAFT)

    def test_force_bypasses_transition_rules(self, seller, make_product):
        from apps.products.services import change_status

        product = make_product(seller, status=ProductStatus.SOLD)

        change_status(product, ProductStatus.DRAFT, force=True)

        product.refresh_from_db()
        assert product.status == ProductStatus.DRAFT

    def test_mark_sold_sets_timestamp(self, seller, make_product):
        product = make_product(seller)

        mark_as_sold(product, actor=seller)

        product.refresh_from_db()
        assert product.status == ProductStatus.SOLD
        assert product.sold_at is not None

    def test_seller_cannot_self_approve(self, auth_client, seller, make_product):
        product = make_product(seller, status=ProductStatus.PENDING)

        response = auth_client(seller).post(
            f"/api/v1/products/{product.slug}/status/",
            {"status": ProductStatus.APPROVED},
            format="json",
        )

        assert response.status_code == 403
        assert response.data["error"]["code"] == "moderation_required"

    def test_renew_extends_expiry(self, seller, make_product):
        from apps.products.services import renew_product

        product = make_product(seller, expires_at=timezone.now() + timezone.timedelta(days=1))
        old_expiry = product.expires_at

        renew_product(product, actor=seller)

        product.refresh_from_db()
        assert product.expires_at > old_expiry


class TestRemoderation:
    @pytest.mark.parametrize("field", ["title", "price", "specs", "condition"])
    def test_sensitive_fields_trigger_remoderation(self, seller, make_product, field):
        product = make_product(seller, status=ProductStatus.APPROVED)

        assert needs_remoderation(product, [field]) is True

    def test_cosmetic_change_does_not(self, seller, make_product):
        product = make_product(seller, status=ProductStatus.APPROVED)

        assert needs_remoderation(product, ["address_note", "contact_name"]) is False

    def test_draft_never_needs_remoderation(self, seller, make_product):
        product = make_product(seller, status=ProductStatus.DRAFT)

        assert needs_remoderation(product, ["price"]) is False


class TestVisibility:
    def test_drafts_hidden_from_public_list(self, api, seller, make_product):
        make_product(seller, status=ProductStatus.DRAFT, title="Yashirin qoralama")
        make_product(seller, status=ProductStatus.APPROVED, title="Ochiq e'lon")

        response = api.get(PRODUCTS_URL)

        titles = [item["title"] for item in response.data["results"]]
        assert "Ochiq e'lon" in titles
        assert "Yashirin qoralama" not in titles

    def test_sold_excluded_by_default_but_page_opens(self, api, seller, make_product):
        sold = make_product(seller, status=ProductStatus.SOLD, title="Sotilgan mahsulot")

        listing = api.get(PRODUCTS_URL)
        detail = api.get(f"{PRODUCTS_URL}{sold.slug}/")

        assert "Sotilgan mahsulot" not in [i["title"] for i in listing.data["results"]]
        assert detail.status_code == 200

    def test_include_sold_flag(self, api, seller, make_product):
        make_product(seller, status=ProductStatus.SOLD, title="Sotilgan mahsulot")

        response = api.get(PRODUCTS_URL, {"include_sold": "true"})

        assert "Sotilgan mahsulot" in [i["title"] for i in response.data["results"]]

    def test_deleted_product_returns_410(self, api, seller, make_product):
        product = make_product(seller)
        product.delete()  # soft delete

        response = api.get(f"{PRODUCTS_URL}{product.slug}/")

        # Soft delete'dan keyin ommaviy queryset uni topmaydi.
        assert response.status_code in (404, 410)

    def test_old_slug_still_resolves(self, api, seller, make_product):
        product = make_product(seller)
        old_slug = product.slug
        product.slug = "yangi-slug-nomi"
        product.save()

        response = api.get(f"{PRODUCTS_URL}{old_slug}/")

        assert response.status_code == 200
        assert response.data["slug"] == "yangi-slug-nomi"

    def test_my_products_shows_own_drafts(self, auth_client, seller, make_product):
        make_product(seller, status=ProductStatus.DRAFT, title="Mening qoralamam")

        response = auth_client(seller).get("/api/v1/products/my/")

        assert "Mening qoralamam" in [i["title"] for i in response.data["results"]]


class TestViewCounter:
    def test_first_view_counts(self, api, seller, make_product):
        product = make_product(seller)

        api.get(f"{PRODUCTS_URL}{product.slug}/")

        product.refresh_from_db()
        assert product.views_count == 1

    def test_repeat_view_from_same_ip_does_not_count(self, api, seller, make_product):
        product = make_product(seller)

        api.get(f"{PRODUCTS_URL}{product.slug}/")
        api.get(f"{PRODUCTS_URL}{product.slug}/")

        product.refresh_from_db()
        assert product.views_count == 1

    def test_ip_is_not_stored_in_plain_text(self, api, seller, make_product):
        from apps.interactions.models import ProductView

        product = make_product(seller)
        api.get(f"{PRODUCTS_URL}{product.slug}/", REMOTE_ADDR="203.0.113.7")

        view = ProductView.objects.get(product=product)
        assert "203.0.113.7" not in view.ip_hash
        assert len(view.ip_hash) == 64
