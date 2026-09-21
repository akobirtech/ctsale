"""Rol va ruxsat testlari.

Asosiy savol: har bir rol AYNAN nima qila oladi va nima qila olmaydi.
Shu sababli matritsa ko'rinishida yoziladi — yangi rol qo'shilganda
nima o'zgarishi darhol ko'rinadi.
"""

import pytest

from apps.rbac.constants import P, R
from apps.rbac.models import Role, UserRole

pytestmark = pytest.mark.django_db


class TestPermissionResolution:
    def test_user_role_has_no_permissions(self, user):
        assert user.permission_codes() == set()
        assert user.has_perm_code(P.PRODUCT_APPROVE) is False

    def test_moderator_has_moderation_permissions(self, moderator):
        codes = moderator.permission_codes()

        assert P.PRODUCT_APPROVE in codes
        assert P.PRODUCT_REJECT in codes
        # Moderator katalogni boshqara olmaydi.
        assert P.CATEGORY_MANAGE not in codes

    def test_admin_manages_catalog_but_not_roles(self, admin):
        codes = admin.permission_codes()

        assert P.CATEGORY_MANAGE in codes
        assert P.TELEGRAM_MANAGE in codes
        # Rol berish huquqi faqat superadminda — huquqlarni o'ziga
        # ko'paytirib olish imkoni bo'lmasligi kerak.
        assert P.ROLE_MANAGE not in codes

    def test_superuser_bypasses_permission_table(self, superadmin):
        assert superadmin.has_perm_code(P.ROLE_MANAGE) is True
        assert superadmin.has_perm_code("hech.qachon.mavjud.emas") is True

    def test_banned_user_loses_permissions_at_api_level(self, auth_client, moderator):
        moderator.is_banned = True
        moderator.save()

        response = auth_client(moderator).get("/api/v1/moderation/queue/")

        assert response.status_code == 403

    def test_multiple_roles_are_merged(self, user, roles):
        UserRole.objects.create(user=user, role=roles[R.MODERATOR])
        UserRole.objects.create(user=user, role=roles[R.SUPPORT])

        codes = user.permission_codes()

        assert P.PRODUCT_APPROVE in codes  # moderatordan
        assert P.USER_VIEW in codes  # supportdan


class TestEndpointAccessMatrix:
    """Har bir endpoint uchun: kim kiradi, kim kirmaydi."""

    @pytest.mark.parametrize(
        "role_fixture,expected",
        [("user", 403), ("moderator", 200), ("admin", 200), ("superadmin", 200)],
    )
    def test_moderation_queue_access(self, request, auth_client, role_fixture, expected):
        actor = request.getfixturevalue(role_fixture)

        response = auth_client(actor).get("/api/v1/moderation/queue/")

        assert response.status_code == expected

    @pytest.mark.parametrize(
        "role_fixture,expected",
        [("user", 403), ("moderator", 403), ("admin", 200), ("superadmin", 200)],
    )
    def test_category_create_access(self, request, auth_client, role_fixture, expected):
        actor = request.getfixturevalue(role_fixture)

        response = auth_client(actor).post(
            "/api/v1/categories/", {"name_uz": "Yangi bo'lim"}, format="json"
        )

        assert response.status_code in (expected, 201 if expected == 200 else expected)

    @pytest.mark.parametrize(
        "role_fixture,expected",
        [("user", 403), ("moderator", 200), ("admin", 200)],
    )
    def test_admin_dashboard_access(self, request, auth_client, role_fixture, expected):
        actor = request.getfixturevalue(role_fixture)

        response = auth_client(actor).get("/api/v1/admin/dashboard/stats/")

        assert response.status_code == expected

    def test_anonymous_gets_401_not_403(self, api):
        """Anonim uchun 401 (kim ekaningiz noma'lum), ruxsatsiz
        foydalanuvchi uchun 403 (kimligingiz ma'lum, lekin mumkin emas)."""
        assert api.get("/api/v1/moderation/queue/").status_code == 401
        assert api.get("/api/v1/admin/dashboard/stats/").status_code == 401

    def test_public_endpoints_open_to_anonymous(self, api, category, product):
        assert api.get("/api/v1/categories/tree/").status_code == 200
        assert api.get("/api/v1/products/").status_code == 200
        assert api.get(f"/api/v1/products/{product.slug}/").status_code == 200


class TestObjectOwnership:
    def test_seller_can_edit_own_product(self, auth_client, seller, product):
        response = auth_client(seller).patch(
            f"/api/v1/products/{product.slug}/", {"model_name": "G614"}, format="json"
        )

        assert response.status_code == 200

    def test_seller_cannot_edit_foreign_product(self, auth_client, other_seller, product):
        response = auth_client(other_seller).patch(
            f"/api/v1/products/{product.slug}/", {"model_name": "O'g'irlangan"}, format="json"
        )

        assert response.status_code in (403, 404)

    def test_admin_can_edit_any_product(self, auth_client, admin, product):
        response = auth_client(admin).patch(
            f"/api/v1/products/{product.slug}/", {"model_name": "Admin tuzatdi"}, format="json"
        )

        assert response.status_code == 200

    def test_seller_cannot_delete_foreign_product(self, auth_client, other_seller, product):
        response = auth_client(other_seller).delete(f"/api/v1/products/{product.slug}/")

        assert response.status_code in (403, 404)
        product.refresh_from_db()
        assert product.is_deleted is False


class TestPrivilegeEscalation:
    def test_user_cannot_grant_themselves_a_role(self, auth_client, user, roles):
        response = auth_client(user).post(
            f"/api/v1/admin/users/{user.id}/roles/", {"roles": [R.ADMIN]}, format="json"
        )

        assert response.status_code == 403
        assert user.roles.filter(role__code=R.ADMIN).exists() is False

    def test_admin_cannot_change_roles_without_permission(self, auth_client, admin, user):
        """ADMIN rolida `user.change_role` yo'q — bu ataylab shunday."""
        response = auth_client(admin).post(
            f"/api/v1/admin/users/{user.id}/roles/", {"roles": [R.ADMIN]}, format="json"
        )

        assert response.status_code == 403

    def test_superadmin_can_assign_roles(self, auth_client, superadmin, user, roles):
        response = auth_client(superadmin).post(
            f"/api/v1/admin/users/{user.id}/roles/", {"roles": [R.MODERATOR]}, format="json"
        )

        assert response.status_code == 200
        assert user.roles.filter(role__code=R.MODERATOR).exists()

    def test_unknown_role_is_rejected(self, auth_client, superadmin, user):
        response = auth_client(superadmin).post(
            f"/api/v1/admin/users/{user.id}/roles/", {"roles": ["xudojon"]}, format="json"
        )

        assert response.status_code == 400
        assert response.data["error"]["code"] == "unknown_role"

    def test_superuser_cannot_be_banned(self, auth_client, superadmin, roles):
        from tests.conftest import _make_user

        target = _make_user("+998901000199", roles)
        target.is_superuser = True
        target.save()

        response = auth_client(superadmin).post(
            f"/api/v1/admin/users/{target.id}/ban/", {"reason": "sinov"}, format="json"
        )

        assert response.status_code == 400
        assert response.data["error"]["code"] == "cannot_ban_superuser"

    def test_cannot_ban_self(self, auth_client, admin):
        """Superuser bo'lmagan, lekin `user.ban` huquqi bor xodim
        o'zini bloklay olmasligi kerak.

        Aktyor sifatida `admin` olinadi: `superadmin` da superuser
        himoyasi birinchi ishga tushib, aynan shu qoidani yashirardi.
        """
        response = auth_client(admin).post(
            f"/api/v1/admin/users/{admin.id}/ban/", {"reason": "sinov"}, format="json"
        )

        assert response.status_code == 400
        assert response.data["error"]["code"] == "cannot_ban_self"

    def test_ban_requires_reason(self, auth_client, superadmin, user):
        response = auth_client(superadmin).post(
            f"/api/v1/admin/users/{user.id}/ban/", {}, format="json"
        )

        assert response.status_code == 400
        assert response.data["error"]["code"] == "reason_required"

    def test_ban_blocks_writes_but_allows_reads(self, auth_client, user, product, roles):
        from apps.rbac.models import Role

        superadmin_role = Role.objects.get(code=R.SUPERADMIN)
        user.is_banned = True
        user.ban_reason = "Spam"
        user.save()

        client = auth_client(user)
        assert client.get(f"/api/v1/products/{product.slug}/").status_code == 200
        assert client.post("/api/v1/favorites/toggle/", {"slug": product.slug}).status_code == 403
        assert superadmin_role is not None


class TestStaffFlag:
    def test_assigning_staff_role_sets_is_staff(self, auth_client, superadmin, user):
        assert user.is_staff is False

        auth_client(superadmin).post(
            f"/api/v1/admin/users/{user.id}/roles/", {"roles": [R.MODERATOR]}, format="json"
        )

        user.refresh_from_db()
        assert user.is_staff is True

    def test_removing_staff_role_clears_is_staff(self, auth_client, superadmin, moderator):
        auth_client(superadmin).post(
            f"/api/v1/admin/users/{moderator.id}/roles/", {"roles": [R.USER]}, format="json"
        )

        moderator.refresh_from_db()
        assert moderator.is_staff is False

    def test_role_catalog_is_exposed(self, auth_client, superadmin):
        response = auth_client(superadmin).get("/api/v1/admin/users/roles/")

        assert response.status_code == 200
        codes = {row["code"] for row in response.data}
        assert codes == set(Role.objects.values_list("code", flat=True))
