"""Admin API: statistika, foydalanuvchilar, audit, Telegram."""

import pytest

from apps.accounts.models import User
from apps.analytics.models import AuditLog
from apps.products.models import ProductStatus

pytestmark = pytest.mark.django_db

STATS_URL = "/api/v1/admin/dashboard/stats/"
CHART_URL = "/api/v1/admin/dashboard/chart/"
USERS_URL = "/api/v1/admin/users/"


class TestDashboardStats:
    def test_counts_match_database(self, auth_client, admin, seller, make_product):
        make_product(seller, status=ProductStatus.APPROVED)
        make_product(seller, status=ProductStatus.SOLD)
        make_product(seller, status=ProductStatus.DRAFT)

        response = auth_client(admin).get(STATS_URL)

        products = response.data["products"]
        assert products["total"] == 3
        assert products["approved"] == 1
        assert products["sold"] == 1
        assert products["draft"] == 1

    def test_user_counts_are_not_inflated_by_joins(
        self, auth_client, admin, seller, make_product
    ):
        """`sellers` mahsulotlar bilan JOIN talab qiladi — `distinct`
        bo'lmasa har bir sotuvchi e'lonlari soniga ko'ra takrorlanib,
        jami son bir necha barobar oshib ketardi."""
        for _ in range(4):
            make_product(seller)

        response = auth_client(admin).get(STATS_URL)

        assert response.data["users"]["total"] == User.objects.count()
        assert response.data["users"]["sellers"] == 1

    def test_activity_totals_are_summed(self, auth_client, admin, seller, make_product):
        make_product(seller, views_count=100, favorites_count=5)
        make_product(seller, views_count=50, favorites_count=2)

        response = auth_client(admin).get(STATS_URL)

        assert response.data["products"]["views"] == 150
        assert response.data["products"]["favorites"] == 7

    def test_empty_database_returns_zeros_not_nulls(self, auth_client, admin):
        response = auth_client(admin).get(STATS_URL)

        assert response.data["products"]["views"] == 0
        assert response.data["products"]["total"] == 0


class TestChart:
    def test_series_has_one_point_per_day(self, auth_client, admin):
        response = auth_client(admin).get(CHART_URL, {"days": 14})

        assert response.data["days"] == 14
        assert len(response.data["series"]) == 14

    def test_days_are_clamped(self, auth_client, admin):
        too_few = auth_client(admin).get(CHART_URL, {"days": 1})
        too_many = auth_client(admin).get(CHART_URL, {"days": 500})

        assert too_few.data["days"] == 7
        assert too_many.data["days"] == 90

    def test_invalid_days_falls_back_to_default(self, auth_client, admin):
        response = auth_client(admin).get(CHART_URL, {"days": "ko'p"})

        assert response.data["days"] == 30

    def test_empty_days_are_filled_with_zero(self, auth_client, admin):
        """Grafik uzilmasligi kerak — ma'lumotsiz kunlar ham qatorda."""
        response = auth_client(admin).get(CHART_URL, {"days": 7})

        assert all("products" in point for point in response.data["series"])
        assert response.data["series"][0]["products"] == 0


class TestUserManagement:
    def test_list_includes_roles_and_product_counts(
        self, auth_client, admin, seller, make_product
    ):
        make_product(seller)

        response = auth_client(admin).get(USERS_URL)

        row = next(r for r in response.data["results"] if r["id"] == str(seller.id))
        assert row["products_total"] == 1
        assert "user" in row["roles"]

    def test_search_by_phone(self, auth_client, admin, seller):
        response = auth_client(admin).get(USERS_URL, {"search": seller.phone[-4:]})

        assert response.data["count"] == 1

    def test_search_by_name(self, auth_client, admin, seller):
        response = auth_client(admin).get(USERS_URL, {"search": "Sotuvchi"})

        assert response.data["count"] >= 1

    def test_filter_by_role(self, auth_client, admin, moderator):
        response = auth_client(admin).get(USERS_URL, {"role": "moderator"})

        ids = {row["id"] for row in response.data["results"]}
        assert str(moderator.id) in ids

    def test_phone_is_visible_to_staff_only(self, auth_client, admin, user):
        """Xodim foydalanuvchi bilan bog'lanishi kerak — bu ro'yxat
        faqat `user.view` ruxsati borlarga ochiq."""
        response = auth_client(admin).get(USERS_URL)

        assert any(row["phone"] for row in response.data["results"])

    def test_ban_stores_reason_and_notifies(self, auth_client, admin, user):
        from apps.notifications.models import Notification

        response = auth_client(admin).post(
            f"{USERS_URL}{user.id}/ban/", {"reason": "Spam e'lonlar"}, format="json"
        )

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.is_banned is True
        assert user.ban_reason == "Spam e'lonlar"
        assert Notification.objects.filter(recipient=user, type="account_banned").exists()

    def test_temporary_ban_sets_expiry(self, auth_client, admin, user):
        auth_client(admin).post(
            f"{USERS_URL}{user.id}/ban/", {"reason": "Ogohlantirish", "days": 7}, format="json"
        )

        user.refresh_from_db()
        assert user.banned_until is not None

    def test_unban_clears_everything(self, auth_client, admin, user):
        auth_client(admin).post(f"{USERS_URL}{user.id}/ban/", {"reason": "x"}, format="json")

        auth_client(admin).post(f"{USERS_URL}{user.id}/unban/")

        user.refresh_from_db()
        assert user.is_banned is False
        assert user.ban_reason == ""
        assert user.banned_until is None

    def test_ban_is_audited(self, auth_client, admin, user):
        auth_client(admin).post(f"{USERS_URL}{user.id}/ban/", {"reason": "x"}, format="json")

        entry = AuditLog.objects.filter(action="ban").first()
        assert entry is not None
        assert entry.actor == admin
        assert entry.target_id == str(user.id)

    def test_verify_seller_toggles(self, auth_client, admin, seller):
        from apps.notifications.models import Notification

        first = auth_client(admin).post(f"{USERS_URL}{seller.id}/verify-seller/")
        second = auth_client(admin).post(f"{USERS_URL}{seller.id}/verify-seller/")

        assert first.data["is_verified_seller"] is True
        assert second.data["is_verified_seller"] is False
        assert Notification.objects.filter(type="seller_verified").count() == 1

    def test_missing_user_returns_404(self, auth_client, admin):
        import uuid

        response = auth_client(admin).post(
            f"{USERS_URL}{uuid.uuid4()}/ban/", {"reason": "x"}, format="json"
        )

        assert response.status_code == 404


class TestAuditLog:
    def test_requires_audit_permission(self, auth_client, moderator, admin):
        assert auth_client(moderator).get("/api/v1/admin/audit/").status_code == 403
        assert auth_client(admin).get("/api/v1/admin/audit/").status_code == 200

    def test_entries_are_listed_newest_first(
        self, auth_client, admin, user, seller, make_product
    ):
        auth_client(admin).post(f"{USERS_URL}{user.id}/ban/", {"reason": "x"}, format="json")

        response = auth_client(admin).get("/api/v1/admin/audit/")

        assert response.data["count"] >= 1
        assert response.data["results"][0]["action"] == "ban"

    def test_filter_by_action(self, auth_client, admin, user):
        auth_client(admin).post(f"{USERS_URL}{user.id}/ban/", {"reason": "x"}, format="json")
        auth_client(admin).post(f"{USERS_URL}{user.id}/unban/")

        response = auth_client(admin).get("/api/v1/admin/audit/", {"action": "unban"})

        assert all(row["action"] == "unban" for row in response.data["results"])

    def test_sensitive_fields_are_stripped(self, admin, user):
        from apps.analytics.services import log_action

        log_action(
            actor=admin,
            action="update",
            target=user,
            changes={"password": ["eski", "yangi"], "first_name": ["A", "B"]},
        )

        entry = AuditLog.objects.latest("created_at")
        assert "password" not in entry.changes
        assert "first_name" in entry.changes


class TestTelegramAdmin:
    def test_posts_are_listed(self, auth_client, admin, seller, moderator, make_product):
        from apps.products.services import approve_product

        approve_product(make_product(seller, status=ProductStatus.PENDING), actor=moderator)

        response = auth_client(admin).get("/api/v1/admin/telegram/")

        assert response.data["count"] == 1
        assert "rendered_text" in response.data["results"][0]

    def test_settings_report_configuration_state(self, auth_client, admin):
        response = auth_client(admin).get("/api/v1/admin/telegram/settings/")

        assert response.status_code == 200
        assert "is_configured" in response.data
        assert "post_template" in response.data

    def test_settings_update_is_audited(self, auth_client, admin):
        auth_client(admin).patch(
            "/api/v1/admin/telegram/settings/", {"auto_publish": False}, format="json"
        )

        assert AuditLog.objects.filter(action="settings_change").exists()

    def test_republish_queues_the_task(self, auth_client, admin, seller, moderator, make_product):
        from apps.products.services import approve_product
        from apps.telegrambot.models import TelegramPost

        approve_product(make_product(seller, status=ProductStatus.PENDING), actor=moderator)
        post = TelegramPost.objects.latest("created_at")

        response = auth_client(admin).post(f"/api/v1/admin/telegram/{post.id}/republish/")

        assert response.status_code == 200
        assert AuditLog.objects.filter(action="telegram_publish").exists()

    def test_republish_unknown_post_returns_404(self, auth_client, admin):
        response = auth_client(admin).post("/api/v1/admin/telegram/99999/republish/")

        assert response.status_code == 404

    def test_moderator_cannot_touch_telegram_settings(self, auth_client, moderator):
        response = auth_client(moderator).get("/api/v1/admin/telegram/settings/")

        assert response.status_code == 403
