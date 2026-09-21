"""Moderatsiya navbati va qarorlar."""

import pytest

from apps.moderation.models import ModerationStatus, ModerationTask, RejectReasonCode
from apps.notifications.models import Notification
from apps.products.models import ProductStatus

pytestmark = pytest.mark.django_db

QUEUE_URL = "/api/v1/moderation/queue/"


@pytest.fixture
def pending_task(make_product, seller):
    product = make_product(seller, status=ProductStatus.PENDING)
    return ModerationTask.objects.create(product=product)


class TestQueue:
    def test_lists_pending_products(self, auth_client, moderator, pending_task):
        response = auth_client(moderator).get(QUEUE_URL)

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == pending_task.id

    def test_approved_products_leave_the_queue(self, auth_client, moderator, pending_task):
        auth_client(moderator).post(f"/api/v1/moderation/{pending_task.id}/approve/")

        response = auth_client(moderator).get(QUEUE_URL)

        assert response.data["count"] == 0

    def test_queue_is_fifo(self, auth_client, moderator, make_product, seller):
        first = ModerationTask.objects.create(
            product=make_product(seller, status=ProductStatus.PENDING, title="Birinchi kelgan")
        )
        ModerationTask.objects.create(
            product=make_product(seller, status=ProductStatus.PENDING, title="Ikkinchi kelgan")
        )

        response = auth_client(moderator).get(QUEUE_URL)

        assert response.data["results"][0]["id"] == first.id

    def test_waiting_hours_is_reported(self, auth_client, moderator, pending_task):
        response = auth_client(moderator).get(QUEUE_URL)

        assert response.data["results"][0]["waiting_hours"] is not None

    def test_preview_returns_full_product(self, auth_client, moderator, pending_task):
        response = auth_client(moderator).get(f"/api/v1/moderation/{pending_task.id}/preview/")

        assert response.status_code == 200
        assert "spec_rows" in response.data
        assert "seller" in response.data

    def test_stats_include_reject_reasons(self, auth_client, moderator, pending_task):
        response = auth_client(moderator).get("/api/v1/moderation/stats/")

        assert response.data["pending"] == 1
        codes = {row["value"] for row in response.data["reject_reasons"]}
        assert RejectReasonCode.BAD_PHOTOS in codes


class TestClaim:
    def test_claim_assigns_to_caller(self, auth_client, moderator, pending_task):
        response = auth_client(moderator).post(f"/api/v1/moderation/{pending_task.id}/claim/")

        assert response.status_code == 200
        pending_task.refresh_from_db()
        assert pending_task.assignee == moderator
        assert pending_task.status == ModerationStatus.IN_REVIEW

    def test_claiming_someone_elses_task_conflicts(
        self, auth_client, moderator, admin, pending_task
    ):
        auth_client(moderator).post(f"/api/v1/moderation/{pending_task.id}/claim/")

        response = auth_client(admin).post(f"/api/v1/moderation/{pending_task.id}/claim/")

        assert response.status_code == 409
        assert response.data["error"]["code"] == "already_claimed"

    def test_reclaiming_own_task_is_allowed(self, auth_client, moderator, pending_task):
        auth_client(moderator).post(f"/api/v1/moderation/{pending_task.id}/claim/")

        response = auth_client(moderator).post(f"/api/v1/moderation/{pending_task.id}/claim/")

        assert response.status_code == 200


class TestApproval:
    def test_approve_publishes_product(self, auth_client, moderator, pending_task):
        response = auth_client(moderator).post(f"/api/v1/moderation/{pending_task.id}/approve/")

        assert response.status_code == 200
        pending_task.product.refresh_from_db()
        assert pending_task.product.status == ProductStatus.APPROVED

    def test_approve_notifies_seller(self, auth_client, moderator, pending_task):
        auth_client(moderator).post(f"/api/v1/moderation/{pending_task.id}/approve/")

        notification = Notification.objects.filter(
            recipient=pending_task.product.seller, type="product_approved"
        ).first()
        assert notification is not None

    def test_approve_creates_telegram_post(self, auth_client, moderator, pending_task):
        from apps.telegrambot.models import TelegramPost

        auth_client(moderator).post(f"/api/v1/moderation/{pending_task.id}/approve/")

        assert TelegramPost.objects.filter(product=pending_task.product).exists()

    def test_approve_writes_audit_entry(self, auth_client, moderator, pending_task):
        from apps.analytics.models import AuditLog

        auth_client(moderator).post(f"/api/v1/moderation/{pending_task.id}/approve/")

        assert AuditLog.objects.filter(action="approve", actor=moderator).exists()

    def test_cannot_approve_twice(self, auth_client, moderator, pending_task):
        auth_client(moderator).post(f"/api/v1/moderation/{pending_task.id}/approve/")

        response = auth_client(moderator).post(f"/api/v1/moderation/{pending_task.id}/approve/")

        assert response.status_code == 400
        assert response.data["error"]["code"] == "invalid_state"

    def test_user_without_permission_cannot_approve(self, auth_client, user, pending_task):
        response = auth_client(user).post(f"/api/v1/moderation/{pending_task.id}/approve/")

        assert response.status_code == 403


class TestRejection:
    def test_reject_requires_reason_code(self, auth_client, moderator, pending_task):
        response = auth_client(moderator).post(
            f"/api/v1/moderation/{pending_task.id}/reject/", {}, format="json"
        )

        assert response.status_code == 400
        assert "reason_code" in response.data["error"]["details"]

    def test_other_reason_requires_comment(self, auth_client, moderator, pending_task):
        response = auth_client(moderator).post(
            f"/api/v1/moderation/{pending_task.id}/reject/",
            {"reason_code": RejectReasonCode.OTHER},
            format="json",
        )

        assert response.status_code == 400
        assert "comment" in response.data["error"]["details"]

    def test_reject_sets_status_and_reason(self, auth_client, moderator, pending_task):
        response = auth_client(moderator).post(
            f"/api/v1/moderation/{pending_task.id}/reject/",
            {"reason_code": RejectReasonCode.BAD_PHOTOS, "comment": "Rasmlar xira"},
            format="json",
        )

        assert response.status_code == 200
        pending_task.refresh_from_db()
        pending_task.product.refresh_from_db()
        assert pending_task.product.status == ProductStatus.REJECTED
        assert pending_task.reason_code == RejectReasonCode.BAD_PHOTOS

    def test_rejection_notification_links_to_edit_page(
        self, auth_client, moderator, pending_task
    ):
        auth_client(moderator).post(
            f"/api/v1/moderation/{pending_task.id}/reject/",
            {"reason_code": RejectReasonCode.INCOMPLETE},
            format="json",
        )

        notification = Notification.objects.get(
            recipient=pending_task.product.seller, type="product_rejected"
        )
        # Havola slug bilan bo'lishi kerak — UUID bilan sahifa topilmaydi.
        assert pending_task.product.slug in notification.link
        assert str(pending_task.product.id) not in notification.link

    def test_internal_note_is_not_sent_to_seller(self, auth_client, moderator, pending_task):
        auth_client(moderator).post(
            f"/api/v1/moderation/{pending_task.id}/reject/",
            {
                "reason_code": RejectReasonCode.SPAM,
                "comment": "Sotuvchiga ko'rinadi",
                "internal_note": "Ichki maxfiy izoh",
            },
            format="json",
        )

        notification = Notification.objects.get(type="product_rejected")
        assert "Ichki maxfiy izoh" not in notification.body

    def test_rejected_product_can_be_resubmitted(self, moderator, pending_task, image_file):
        from apps.mediafiles.models import ProductImage
        from apps.products.services import reject_product, submit_for_moderation

        product = pending_task.product
        ProductImage.objects.create(product=product, image=image_file())
        reject_product(product, actor=moderator, reason_code=RejectReasonCode.INCOMPLETE)

        submit_for_moderation(product, actor=product.seller)

        product.refresh_from_db()
        assert product.status == ProductStatus.PENDING
        latest = product.moderation_tasks.order_by("-created_at").first()
        assert latest.is_resubmission is True


class TestBulkApprove:
    def test_approves_several_at_once(self, auth_client, moderator, make_product, seller):
        tasks = [
            ModerationTask.objects.create(
                product=make_product(seller, status=ProductStatus.PENDING, title=f"E'lon {i}")
            )
            for i in range(3)
        ]

        response = auth_client(moderator).post(
            "/api/v1/moderation/bulk-approve/",
            {"task_ids": [task.id for task in tasks]},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["approved_count"] == 3

    def test_skips_products_not_pending(self, auth_client, moderator, make_product, seller):
        pending = ModerationTask.objects.create(
            product=make_product(seller, status=ProductStatus.PENDING)
        )
        already_live = ModerationTask.objects.create(
            product=make_product(seller, status=ProductStatus.APPROVED)
        )

        response = auth_client(moderator).post(
            "/api/v1/moderation/bulk-approve/",
            {"task_ids": [pending.id, already_live.id]},
            format="json",
        )

        assert response.data["approved_count"] == 1

    def test_empty_list_is_rejected(self, auth_client, moderator):
        response = auth_client(moderator).post(
            "/api/v1/moderation/bulk-approve/", {"task_ids": []}, format="json"
        )

        assert response.status_code == 400
