"""Autentifikatsiya testlari."""

from datetime import timedelta

import pytest
from django.conf import settings
from django.utils import timezone

from apps.accounts.models import LoginAttempt, OTPCode, OTPPurpose, User
from tests.conftest import PASSWORD

pytestmark = pytest.mark.django_db

REGISTER_URL = "/api/v1/auth/register/"
VERIFY_URL = "/api/v1/auth/verify/"
LOGIN_URL = "/api/v1/auth/login/"
REFRESH_URL = "/api/v1/auth/refresh/"
LOGOUT_URL = "/api/v1/auth/logout/"
ME_URL = "/api/v1/auth/me/"

VALID_REGISTRATION = {
    "phone": "+998901234567",
    "password": "Kuchli#Parol9",
    "password_confirm": "Kuchli#Parol9",
    "first_name": "Akobir",
}


def register(api, **overrides):
    return api.post(REGISTER_URL, {**VALID_REGISTRATION, **overrides}, format="json")


def latest_code(phone):
    """OTP hash saqlanadi, shuning uchun testda kodni bilish uchun
    barcha ehtimoliy kodlarni tekshirish o'rniga yangisini qo'yamiz."""
    otp = OTPCode.objects.filter(phone=phone).order_by("-created_at").first()
    otp.code_hash = OTPCode.hash_code("123456")
    otp.save(update_fields=["code_hash"])
    return "123456"


class TestRegistration:
    def test_creates_inactive_user_and_otp(self, api, roles):
        response = register(api)

        assert response.status_code == 201
        user = User.all_objects.get(phone="+998901234567")
        assert user.is_phone_verified is False
        assert user.is_active is False
        assert OTPCode.objects.filter(phone=user.phone).count() == 1

    def test_phone_is_normalized(self, api, roles):
        response = register(api, phone="90 123 45 67")

        assert response.status_code == 201
        assert User.all_objects.filter(phone="+998901234567").exists()

    @pytest.mark.parametrize(
        "password,expected_fragment",
        [
            ("12345678", "keng tarqalgan"),
            ("parolparol", "raqam"),
            ("Ab1", "8 ta belgi"),
        ],
    )
    def test_rejects_weak_passwords(self, api, roles, password, expected_fragment):
        response = register(api, password=password, password_confirm=password)

        assert response.status_code == 400
        assert expected_fragment in str(response.data["error"]["details"])

    def test_rejects_mismatched_confirmation(self, api, roles):
        response = register(api, password_confirm="Boshqa#Parol9")

        assert response.status_code == 400
        assert "password_confirm" in response.data["error"]["details"]

    def test_rejects_invalid_phone_format(self, api, roles):
        response = register(api, phone="12345")

        assert response.status_code == 400
        assert "phone" in response.data["error"]["details"]

    def test_verified_phone_cannot_register_again(self, api, roles, user):
        response = register(api, phone=user.phone)

        assert response.status_code == 400
        assert response.data["error"]["code"] == "phone_taken"

    def test_unverified_registration_can_be_retried(self, api, roles):
        """Tasdiqlanmagan hisob qolib ketsa foydalanuvchi qamalib qolmasligi kerak."""
        register(api)
        OTPCode.objects.all().delete()  # cooldown testga xalaqit bermasin

        response = register(api, first_name="Yangi")

        assert response.status_code == 201
        assert User.all_objects.filter(phone="+998901234567").count() == 1

    def test_resend_is_rate_limited_by_cooldown(self, api, roles):
        register(api)

        response = register(api)

        assert response.status_code == 429
        assert response.data["error"]["code"] == "otp_cooldown"


class TestVerification:
    def test_correct_code_activates_and_returns_tokens(self, api, roles):
        register(api)
        code = latest_code("+998901234567")

        response = api.post(
            VERIFY_URL, {"phone": "+998901234567", "code": code}, format="json"
        )

        assert response.status_code == 200
        assert "access" in response.data
        assert response.data["user"]["is_phone_verified"] is True

        user = User.objects.get(phone="+998901234567")
        assert user.is_active is True

    def test_refresh_token_is_httponly_cookie(self, api, roles):
        register(api)
        code = latest_code("+998901234567")

        response = api.post(
            VERIFY_URL, {"phone": "+998901234567", "code": code}, format="json"
        )

        cookie = response.cookies[settings.REFRESH_COOKIE_NAME]
        assert cookie["httponly"] is True
        # Token javob tanasida bo'lmasligi kerak — faqat cookie'da.
        assert "refresh" not in response.data

    def test_wrong_code_reports_remaining_attempts(self, api, roles):
        register(api)

        response = api.post(
            VERIFY_URL, {"phone": "+998901234567", "code": "000000"}, format="json"
        )

        assert response.status_code == 400
        assert response.data["error"]["code"] == "otp_invalid"
        assert "urinish" in response.data["error"]["message"]

    def test_expired_code_is_rejected(self, api, roles):
        register(api)
        code = latest_code("+998901234567")
        OTPCode.objects.update(expires_at=timezone.now() - timedelta(seconds=1))

        response = api.post(
            VERIFY_URL, {"phone": "+998901234567", "code": code}, format="json"
        )

        assert response.status_code == 400
        assert response.data["error"]["code"] == "otp_expired"

    def test_code_is_single_use(self, api, roles):
        register(api)
        code = latest_code("+998901234567")
        api.post(VERIFY_URL, {"phone": "+998901234567", "code": code}, format="json")

        response = api.post(
            VERIFY_URL, {"phone": "+998901234567", "code": code}, format="json"
        )

        assert response.status_code == 400
        assert response.data["error"]["code"] == "otp_not_found"

    def test_too_many_attempts_burns_the_code(self, api, roles):
        register(api)
        code = latest_code("+998901234567")

        for _ in range(settings.OTP_MAX_ATTEMPTS):
            api.post(VERIFY_URL, {"phone": "+998901234567", "code": "000000"}, format="json")

        response = api.post(
            VERIFY_URL, {"phone": "+998901234567", "code": code}, format="json"
        )

        assert response.status_code == 400
        assert response.data["error"]["code"] in ("otp_attempts_exceeded", "otp_not_found")


class TestLogin:
    def test_successful_login(self, api, user):
        response = api.post(
            LOGIN_URL, {"phone": user.phone, "password": PASSWORD}, format="json"
        )

        assert response.status_code == 200
        assert response.data["user"]["phone"] == user.phone
        assert LoginAttempt.objects.filter(phone=user.phone, was_successful=True).exists()

    def test_wrong_password_is_recorded(self, api, user):
        response = api.post(
            LOGIN_URL, {"phone": user.phone, "password": "NotoGri#1"}, format="json"
        )

        assert response.status_code == 401
        assert response.data["error"]["code"] == "invalid_credentials"
        assert LoginAttempt.objects.filter(phone=user.phone, was_successful=False).exists()

    def test_error_does_not_reveal_whether_phone_exists(self, api, user):
        """Xato xabari ikkala holatda bir xil bo'lishi kerak — aks holda
        raqamlarni tekshirib chiqish mumkin bo'lardi."""
        existing = api.post(
            LOGIN_URL, {"phone": user.phone, "password": "NotoGri#1"}, format="json"
        )
        missing = api.post(
            LOGIN_URL, {"phone": "+998909999999", "password": "NotoGri#1"}, format="json"
        )

        assert existing.data["error"]["message"] == missing.data["error"]["message"]

    def test_unverified_phone_cannot_login(self, api, roles):
        User.objects.create_user(phone="+998901111111", password=PASSWORD, is_active=True)

        response = api.post(
            LOGIN_URL, {"phone": "+998901111111", "password": PASSWORD}, format="json"
        )

        assert response.status_code == 403
        assert response.data["error"]["code"] == "phone_not_verified"

    def test_banned_user_cannot_login(self, api, user):
        user.is_banned = True
        user.ban_reason = "Qoidabuzarlik"
        user.save()

        response = api.post(
            LOGIN_URL, {"phone": user.phone, "password": PASSWORD}, format="json"
        )

        assert response.status_code == 403
        assert response.data["error"]["code"] == "account_banned"
        assert "Qoidabuzarlik" in response.data["error"]["message"]

    def test_expired_ban_allows_login(self, api, user):
        user.is_banned = True
        user.banned_until = timezone.now() - timedelta(days=1)
        user.save()

        response = api.post(
            LOGIN_URL, {"phone": user.phone, "password": PASSWORD}, format="json"
        )

        assert response.status_code == 200

    def test_brute_force_lock_after_threshold(self, api, user):
        from apps.accounts.services import BRUTE_FORCE_THRESHOLD

        for _ in range(BRUTE_FORCE_THRESHOLD):
            LoginAttempt.objects.create(phone=user.phone, was_successful=False)

        response = api.post(
            LOGIN_URL, {"phone": user.phone, "password": PASSWORD}, format="json"
        )

        assert response.status_code == 429
        assert response.data["error"]["code"] == "too_many_attempts"


class TestSession:
    def test_me_requires_authentication(self, api):
        response = api.get(ME_URL)

        assert response.status_code == 401
        assert response.data["error"]["code"] == "not_authenticated"

    def test_me_returns_permissions(self, auth_client, moderator):
        response = auth_client(moderator).get(ME_URL)

        assert response.status_code == 200
        assert "product.approve" in response.data["permissions"]
        assert "moderator" in response.data["roles"]

    def test_profile_update(self, auth_client, user, region):
        response = auth_client(user).patch(
            ME_URL, {"first_name": "Yangilangan", "region": region.id}, format="json"
        )

        assert response.status_code == 200
        assert response.data["first_name"] == "Yangilangan"

    def test_district_must_belong_to_region(self, auth_client, user, region, district):
        from apps.catalog.models import Region

        other = Region.objects.create(name_uz="Buxoro", slug="buxoro")

        response = auth_client(user).patch(
            ME_URL, {"region": other.id, "district": district.id}, format="json"
        )

        assert response.status_code == 400
        assert "district" in response.data["error"]["details"]

    def test_refresh_rotates_and_blacklists_old_token(self, api, user):
        login = api.post(LOGIN_URL, {"phone": user.phone, "password": PASSWORD}, format="json")
        old_cookie = login.cookies[settings.REFRESH_COOKIE_NAME].value

        first = api.post(REFRESH_URL)
        assert first.status_code == 200
        assert "access" in first.data

        # Eski refresh qayta ishlatilsa rad etilishi kerak.
        api.cookies[settings.REFRESH_COOKIE_NAME] = old_cookie
        second = api.post(REFRESH_URL)

        assert second.status_code == 401
        assert second.data["error"]["code"] == "invalid_refresh_token"

    def test_refresh_without_cookie(self, api):
        response = api.post(REFRESH_URL)

        assert response.status_code == 401
        assert response.data["error"]["code"] == "no_refresh_token"

    def test_logout_clears_cookie(self, api, user):
        api.post(LOGIN_URL, {"phone": user.phone, "password": PASSWORD}, format="json")

        response = api.post(LOGOUT_URL)

        assert response.status_code == 200
        assert response.cookies[settings.REFRESH_COOKIE_NAME].value == ""

    def test_banned_user_refresh_is_rejected(self, api, user):
        api.post(LOGIN_URL, {"phone": user.phone, "password": PASSWORD}, format="json")
        user.is_banned = True
        user.save()

        response = api.post(REFRESH_URL)

        assert response.status_code == 401
        assert response.data["error"]["code"] == "account_unavailable"


class TestPasswordReset:
    def test_request_does_not_reveal_missing_account(self, api, user):
        existing = api.post(
            "/api/v1/auth/password/reset/", {"phone": user.phone}, format="json"
        )
        missing = api.post(
            "/api/v1/auth/password/reset/", {"phone": "+998909999999"}, format="json"
        )

        assert existing.status_code == missing.status_code == 200
        assert existing.data["detail"] == missing.data["detail"]

    def test_reset_changes_password_and_revokes_sessions(self, api, user):
        api.post("/api/v1/auth/password/reset/", {"phone": user.phone}, format="json")
        otp = OTPCode.objects.filter(
            phone=user.phone, purpose=OTPPurpose.RESET_PASSWORD
        ).latest("created_at")
        otp.code_hash = OTPCode.hash_code("654321")
        otp.save(update_fields=["code_hash"])

        response = api.post(
            "/api/v1/auth/password/reset/confirm/",
            {
                "phone": user.phone,
                "code": "654321",
                "new_password": "Yangi#Parol9",
                "new_password_confirm": "Yangi#Parol9",
            },
            format="json",
        )

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.check_password("Yangi#Parol9")

    def test_change_password_requires_correct_current(self, auth_client, user):
        response = auth_client(user).post(
            "/api/v1/auth/password/change/",
            {
                "old_password": "NotoGri#1",
                "new_password": "Yangi#Parol9",
                "new_password_confirm": "Yangi#Parol9",
            },
            format="json",
        )

        assert response.status_code == 400
        assert "old_password" in response.data["error"]["details"]
