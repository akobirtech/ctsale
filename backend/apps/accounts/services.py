"""Autentifikatsiya biznes logikasi.

Views bu yerdagi funksiyalarni chaqiradi. Shu sababli bir xil logikani
Telegram botdan yoki management command'dan ham ishlatish mumkin.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import BusinessError
from apps.core.utils import generate_otp_code, normalize_phone
from apps.rbac.constants import R
from apps.rbac.models import Role, UserRole

from .models import LoginAttempt, OTPCode, OTPPurpose, User

logger = logging.getLogger(__name__)

# Bir xil telefon uchun ketma-ket OTP so'rovlari orasidagi eng qisqa vaqt.
OTP_RESEND_COOLDOWN_SECONDS = 60
# Shuncha muvaffaqiyatsiz urinishdan keyin kirish vaqtincha bloklanadi.
BRUTE_FORCE_THRESHOLD = 10
BRUTE_FORCE_WINDOW_MINUTES = 15


# --------------------------------------------------------------------------
# OTP
# --------------------------------------------------------------------------
def issue_otp(phone, purpose=OTPPurpose.REGISTER, ip_address=None):
    """Yangi OTP yaratadi va yuboradi.

    Kodning o'zi qaytariladi, lekin faqat DEBUG rejimida javobga
    qo'shiladi (view hal qiladi) — productionda hech qachon.
    """
    phone = normalize_phone(phone)

    recent = (
        OTPCode.objects.filter(phone=phone, purpose=purpose)
        .order_by("-created_at")
        .first()
    )
    if recent:
        elapsed = (timezone.now() - recent.created_at).total_seconds()
        if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
            wait = int(OTP_RESEND_COOLDOWN_SECONDS - elapsed)
            raise BusinessError(
                f"Yangi kod so'rash uchun {wait} soniya kuting.",
                code="otp_cooldown",
                status_code=429,
            )

    # Eski kodlarni bekor qilamiz: bir vaqtda faqat bitta kod amal qilsin.
    OTPCode.objects.filter(phone=phone, purpose=purpose, is_used=False).update(is_used=True)

    code = generate_otp_code()
    otp = OTPCode.objects.create(
        phone=phone,
        code_hash=OTPCode.hash_code(code),
        purpose=purpose,
        expires_at=timezone.now() + timedelta(seconds=settings.OTP_TTL_SECONDS),
        ip_address=ip_address,
    )
    _deliver_otp(phone, code, purpose)
    return otp, code


def _deliver_otp(phone, code, purpose):
    """Kodni yetkazish.

    Hozircha logga yoziladi (dev). Real SMS provayder ulanganda faqat
    shu funksiya o'zgaradi — chaqiruvchi kod tegilmaydi.
    """
    message = f"CT Sale tasdiqlash kodi: {code}"
    logger.info("OTP [%s] %s -> %s", purpose, phone, message)

    # Foydalanuvchi Telegram botga ulangan bo'lsa, kodni o'sha yerga ham yuboramiz.
    user = User.all_objects.filter(phone=phone, telegram_id__isnull=False).first()
    if user:
        try:
            from apps.telegrambot.services import send_direct_message

            send_direct_message(user.telegram_id, message)
        except Exception:  # pragma: no cover - tashqi servis
            logger.warning("OTP ni Telegram orqali yuborib bo'lmadi: %s", phone)


def verify_otp(phone, code, purpose=OTPPurpose.REGISTER):
    """Kodni tekshiradi. Muvaffaqiyatsizlikda aniq sabab bilan xato otadi.

    MUHIM: bu funksiya tranzaksiya ICHIDA chaqirilmasligi kerak.
    Noto'g'ri urinish hisoblagichi saqlanadi va keyin xato otiladi —
    agar chaqiruvchi `atomic` blok ichida bo'lsa, xato rollback
    qiladi va hisoblagich hech qachon oshmaydi. Bu esa kodni
    cheksiz marta taxmin qilish imkonini berardi.
    """
    phone = normalize_phone(phone)
    otp = (
        OTPCode.objects.filter(phone=phone, purpose=purpose, is_used=False)
        .order_by("-created_at")
        .first()
    )
    if otp is None:
        raise BusinessError(
            "Tasdiqlash kodi topilmadi. Yangi kod so'rang.", code="otp_not_found"
        )
    if otp.is_expired:
        raise BusinessError(
            "Kod muddati tugagan. Yangi kod so'rang.", code="otp_expired"
        )
    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        otp.is_used = True
        otp.save(update_fields=["is_used"])
        raise BusinessError(
            "Juda ko'p noto'g'ri urinish. Yangi kod so'rang.", code="otp_attempts_exceeded"
        )

    if not otp.verify(code):
        otp.attempts += 1
        otp.save(update_fields=["attempts"])
        remaining = settings.OTP_MAX_ATTEMPTS - otp.attempts
        raise BusinessError(
            f"Kod noto'g'ri. Yana {remaining} ta urinish qoldi.", code="otp_invalid"
        )

    otp.is_used = True
    otp.save(update_fields=["is_used"])
    return otp


# --------------------------------------------------------------------------
# Ro'yxatdan o'tish
# --------------------------------------------------------------------------
@transaction.atomic
def register_user(phone, password, first_name="", last_name="", ip_address=None):
    phone = normalize_phone(phone)

    existing = User.all_objects.filter(phone=phone).first()
    if existing and existing.is_phone_verified:
        raise BusinessError(
            "Bu raqam allaqachon ro'yxatdan o'tgan. Kirishga urinib ko'ring.",
            code="phone_taken",
        )

    if existing:
        # Tasdiqlanmagan hisob qolib ketgan — uni qayta ishlatamiz,
        # aks holda foydalanuvchi hech qachon ro'yxatdan o'ta olmaydi.
        existing.set_password(password)
        existing.first_name = first_name or existing.first_name
        existing.last_name = last_name or existing.last_name
        existing.is_deleted = False
        existing.save()
        user = existing
    else:
        user = User.objects.create_user(
            phone=phone,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=False,
        )
        _assign_default_role(user)

    otp, code = issue_otp(phone, OTPPurpose.REGISTER, ip_address)
    return user, code


def _assign_default_role(user):
    role = Role.objects.filter(code=R.USER).first()
    if role:
        UserRole.objects.get_or_create(user=user, role=role)


def confirm_registration(phone, code):
    # Tekshiruv tranzaksiyadan tashqarida: urinishlar hisoblagichi
    # xato otilganda ham saqlanib qolishi kerak.
    verify_otp(phone, code, OTPPurpose.REGISTER)
    return _activate_registered_user(phone)


@transaction.atomic
def _activate_registered_user(phone):
    user = User.all_objects.filter(phone=normalize_phone(phone)).first()
    if user is None:
        raise BusinessError("Foydalanuvchi topilmadi.", code="user_not_found", status_code=404)

    user.is_phone_verified = True
    user.is_active = True
    user.save(update_fields=["is_phone_verified", "is_active", "updated_at"])
    _assign_default_role(user)

    from apps.notifications.models import NotificationPreference

    NotificationPreference.objects.get_or_create(user=user)
    return user


# --------------------------------------------------------------------------
# Kirish
# --------------------------------------------------------------------------
def check_brute_force(phone, ip_address):
    """Ko'p muvaffaqiyatsiz urinishdan keyin vaqtincha bloklash.

    DRF throttling so'rov sonini cheklaydi, bu esa aynan bitta hisobga
    qaratilgan hujumni aniqlaydi.
    """
    since = timezone.now() - timedelta(minutes=BRUTE_FORCE_WINDOW_MINUTES)
    failures = LoginAttempt.objects.filter(
        phone=phone, was_successful=False, created_at__gte=since
    ).count()
    if failures >= BRUTE_FORCE_THRESHOLD:
        raise BusinessError(
            f"Juda ko'p muvaffaqiyatsiz urinish. {BRUTE_FORCE_WINDOW_MINUTES} daqiqadan keyin "
            "qaytadan urinib ko'ring yoki parolni tiklang.",
            code="too_many_attempts",
            status_code=429,
        )


def record_login_attempt(phone, ip_address, user_agent, success):
    LoginAttempt.objects.create(
        phone=phone or "",
        ip_address=ip_address or None,
        user_agent=(user_agent or "")[:255],
        was_successful=success,
    )


def authenticate_user(phone, password, ip_address=None, user_agent=""):
    phone = normalize_phone(phone)
    check_brute_force(phone, ip_address)

    user = authenticate(phone=phone, password=password)

    if user is None:
        record_login_attempt(phone, ip_address, user_agent, success=False)
        # Qaysi qismi noto'g'ri ekanini aytmaymiz — bu raqam
        # ro'yxatdan o'tganini aniqlash imkonini berardi.
        raise BusinessError(
            "Telefon raqam yoki parol noto'g'ri.", code="invalid_credentials", status_code=401
        )

    if not user.is_phone_verified:
        record_login_attempt(phone, ip_address, user_agent, success=False)
        raise BusinessError(
            "Telefon raqamingiz tasdiqlanmagan. Tasdiqlash kodini so'rang.",
            code="phone_not_verified",
            status_code=403,
        )

    if user.ban_is_active:
        record_login_attempt(phone, ip_address, user_agent, success=False)
        reason = user.ban_reason or "Qoidalar buzilgani uchun"
        raise BusinessError(
            f"Hisobingiz bloklangan. Sabab: {reason}", code="account_banned", status_code=403
        )

    record_login_attempt(phone, ip_address, user_agent, success=True)
    return user


# --------------------------------------------------------------------------
# Parolni tiklash
# --------------------------------------------------------------------------
def request_password_reset(phone, ip_address=None):
    phone = normalize_phone(phone)
    user = User.objects.filter(phone=phone, is_phone_verified=True).first()

    # Foydalanuvchi topilmasa ham xato qaytarmaymiz: aks holda bu
    # raqamlarni tekshirib chiqish vositasiga aylanadi.
    if user is None:
        logger.info("Mavjud bo'lmagan raqam uchun parol tiklash so'rovi: %s", phone)
        return None, None

    return issue_otp(phone, OTPPurpose.RESET_PASSWORD, ip_address)


def confirm_password_reset(phone, code, new_password):
    verify_otp(phone, code, OTPPurpose.RESET_PASSWORD)
    return _apply_new_password(phone, new_password)


@transaction.atomic
def _apply_new_password(phone, new_password):
    user = User.objects.filter(phone=normalize_phone(phone)).first()
    if user is None:
        raise BusinessError("Foydalanuvchi topilmadi.", code="user_not_found", status_code=404)

    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])
    revoke_all_refresh_tokens(user)
    return user


def revoke_all_refresh_tokens(user):
    """Parol o'zgarganda barcha qurilmalardagi sessiyalarni yopish."""
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )

    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)
