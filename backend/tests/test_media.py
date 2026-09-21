"""Media yuklash: validatsiya, limitlar va optimizatsiya."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.mediafiles.models import ProductImage
from apps.mediafiles.tasks import process_product_image
from tests.conftest import build_image_bytes

pytestmark = pytest.mark.django_db


def images_url(product):
    return f"/api/v1/products/{product.slug}/images/"


class TestImageValidation:
    def test_valid_image_is_accepted(self, auth_client, seller, product, image_file):
        response = auth_client(seller).post(
            images_url(product), {"images": image_file()}, format="multipart"
        )

        assert response.status_code == 201
        assert ProductImage.objects.filter(product=product).count() == 1

    def test_fake_image_is_rejected_by_magic_bytes(
        self, auth_client, seller, product, fake_image_file
    ):
        """Kengaytma va Content-Type to'g'ri, lekin ichi rasm emas."""
        response = auth_client(seller).post(
            images_url(product), {"images": fake_image_file}, format="multipart"
        )

        assert response.status_code == 400
        assert response.data["error"]["code"] == "invalid_image"
        assert "haqiqiy rasm emas" in response.data["error"]["message"]

    def test_disallowed_extension_is_rejected(self, auth_client, seller, product):
        uploaded = SimpleUploadedFile("virus.exe", b"MZ\x90\x00", content_type="image/jpeg")

        response = auth_client(seller).post(
            images_url(product), {"images": uploaded}, format="multipart"
        )

        assert response.status_code == 400
        assert "qabul qilinmaydi" in response.data["error"]["message"]

    def test_oversized_image_is_rejected(self, auth_client, seller, product, settings):
        settings.MAX_IMAGE_SIZE_MB = 1
        big = SimpleUploadedFile(
            "katta.jpg", build_image_bytes(4000, 4000) + b"\x00" * (2 * 1024 * 1024),
            content_type="image/jpeg",
        )

        response = auth_client(seller).post(
            images_url(product), {"images": big}, format="multipart"
        )

        assert response.status_code == 400
        assert "MB" in response.data["error"]["message"]

    def test_tiny_image_is_rejected(self, auth_client, seller, product, image_file):
        response = auth_client(seller).post(
            images_url(product), {"images": image_file(width=50, height=50)}, format="multipart"
        )

        assert response.status_code == 400
        assert "kichik" in response.data["error"]["message"]

    def test_empty_request_is_rejected(self, auth_client, seller, product):
        response = auth_client(seller).post(images_url(product), {}, format="multipart")

        assert response.status_code == 400
        assert response.data["error"]["code"] == "no_file"

    def test_error_names_the_problem_file(self, auth_client, seller, product, image_file):
        """Bir nechta fayldan bittasi xato bo'lsa, qaysi biri ekani
        aytilishi kerak."""
        bad = SimpleUploadedFile("buzuq.jpg", b"emas" * 100, content_type="image/jpeg")

        response = auth_client(seller).post(
            images_url(product), {"images": [image_file(), bad]}, format="multipart"
        )

        assert response.status_code == 400
        assert "buzuq.jpg" in response.data["error"]["message"]


class TestImageLimits:
    def test_limit_is_enforced(self, auth_client, seller, product, image_file, settings):
        settings.MAX_IMAGES_PER_PRODUCT = 2
        client = auth_client(seller)
        client.post(images_url(product), {"images": image_file()}, format="multipart")
        client.post(images_url(product), {"images": image_file()}, format="multipart")

        response = client.post(images_url(product), {"images": image_file()}, format="multipart")

        assert response.status_code == 400
        assert response.data["error"]["code"] == "limit_exceeded"

    def test_batch_exceeding_remaining_is_rejected(
        self, auth_client, seller, product, image_file, settings
    ):
        settings.MAX_IMAGES_PER_PRODUCT = 2

        response = auth_client(seller).post(
            images_url(product),
            {"images": [image_file(), image_file(), image_file()]},
            format="multipart",
        )

        assert response.status_code == 400
        assert response.data["error"]["code"] == "limit_exceeded"


class TestImageOrdering:
    def test_first_image_becomes_primary(self, auth_client, seller, product, image_file):
        response = auth_client(seller).post(
            images_url(product), {"images": image_file()}, format="multipart"
        )

        assert response.data[0]["is_primary"] is True

    def test_only_one_primary_at_a_time(self, auth_client, seller, product, image_file):
        client = auth_client(seller)
        first = client.post(images_url(product), {"images": image_file()}, format="multipart")
        second = client.post(images_url(product), {"images": image_file()}, format="multipart")

        client.post(f"{images_url(product)}{second.data[0]['id']}/set-primary/")

        primaries = ProductImage.objects.filter(product=product, is_primary=True)
        assert primaries.count() == 1
        assert primaries.first().id == second.data[0]["id"]
        assert first.data[0]["id"] != primaries.first().id

    def test_deleting_primary_promotes_next(self, auth_client, seller, product, image_file):
        client = auth_client(seller)
        first = client.post(images_url(product), {"images": image_file()}, format="multipart")
        client.post(images_url(product), {"images": image_file()}, format="multipart")

        client.delete(f"{images_url(product)}{first.data[0]['id']}/")

        assert ProductImage.objects.filter(product=product, is_primary=True).count() == 1

    def test_reorder(self, auth_client, seller, product, image_file):
        client = auth_client(seller)
        first = client.post(images_url(product), {"images": image_file()}, format="multipart")
        second = client.post(images_url(product), {"images": image_file()}, format="multipart")

        response = client.post(
            f"{images_url(product)}reorder/",
            {
                "items": [
                    {"id": second.data[0]["id"], "order": 0},
                    {"id": first.data[0]["id"], "order": 1},
                ]
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data[0]["id"] == second.data[0]["id"]


class TestImageProcessing:
    def test_webp_variants_are_created(self, seller, product, image_file):
        image = ProductImage.objects.create(product=product, image=image_file())

        result = process_product_image(image.id)

        image.refresh_from_db()
        assert result == "processed"
        assert image.is_processed is True
        for variant in ("thumb", "medium", "large"):
            assert getattr(image, variant).name.endswith(".webp")

    def test_dimensions_are_recorded(self, seller, product, image_file):
        image = ProductImage.objects.create(product=product, image=image_file(width=1200, height=900))

        process_product_image(image.id)

        image.refresh_from_db()
        assert (image.width, image.height) == (1200, 900)

    def test_filename_is_seo_friendly(self, auth_client, seller, product, image_file):
        """Rasm nomi mahsulot slug'idan yasalishi kerak (talab #17)."""
        response = auth_client(seller).post(
            images_url(product), {"images": image_file(name="IMG_9931.jpg")}, format="multipart"
        )

        image = ProductImage.objects.get(id=response.data[0]["id"])
        filename = image.image.name.rsplit("/", 1)[-1]
        assert filename.startswith(product.slug[:40])
        assert "IMG_9931" not in filename

    def test_path_traversal_attempt_is_neutralised(
        self, auth_client, seller, product, image_file
    ):
        malicious = SimpleUploadedFile(
            "../../../etc/passwd.jpg", build_image_bytes(), content_type="image/jpeg"
        )

        response = auth_client(seller).post(
            images_url(product), {"images": malicious}, format="multipart"
        )

        assert response.status_code == 201
        image = ProductImage.objects.get(id=response.data[0]["id"])
        assert ".." not in image.image.name
        assert image.image.name.startswith(f"products/{product.id}/images/")


class TestMediaPermissions:
    def test_foreign_seller_cannot_upload(self, auth_client, other_seller, product, image_file):
        response = auth_client(other_seller).post(
            images_url(product), {"images": image_file()}, format="multipart"
        )

        assert response.status_code == 403

    def test_anonymous_cannot_upload(self, api, product, image_file):
        response = api.post(images_url(product), {"images": image_file()}, format="multipart")

        assert response.status_code == 401

    def test_admin_can_upload_to_any_product(self, auth_client, admin, product, image_file):
        response = auth_client(admin).post(
            images_url(product), {"images": image_file()}, format="multipart"
        )

        assert response.status_code == 201


class TestVideo:
    def test_non_video_is_rejected(self, auth_client, seller, product):
        uploaded = SimpleUploadedFile("film.mp4", b"bu video emas", content_type="video/mp4")

        response = auth_client(seller).post(
            f"/api/v1/products/{product.slug}/videos/", {"video": uploaded}, format="multipart"
        )

        assert response.status_code == 400
        assert response.data["error"]["code"] == "invalid_video"

    def test_valid_mp4_header_is_accepted(self, auth_client, seller, product):
        # Minimal MP4 imzosi: ....ftypisom
        payload = b"\x00\x00\x00\x20ftypisom" + b"\x00" * 512
        uploaded = SimpleUploadedFile("film.mp4", payload, content_type="video/mp4")

        response = auth_client(seller).post(
            f"/api/v1/products/{product.slug}/videos/", {"video": uploaded}, format="multipart"
        )

        assert response.status_code == 201
        assert response.data["mime_type"] == "video/mp4"
