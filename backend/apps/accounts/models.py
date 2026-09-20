"""Foydalanuvchi, do'kon profili va OTP modellari.

Identifikator sifatida telefon raqam ishlatiladi — O'zbekistonda
email'dan ko'ra ishonchli va marketplace uchun tabiiyroq.
"""

import hashlib
import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from apps.core.models import SoftDeleteModel, TimeStampedModel
from apps.core.utils import normalize_phone

PHONE_VALIDATOR = RegexValidator(
    regex=r"^\+998\d{9}$",
    message="Telefon raqam +998XXXXXXXXX ko'rinishida bo'lishi kerak.",
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone, password, **extra):
        if not phone:
            raise ValueError("Telefon raqam majburiy.")
        phone = normalize_phone(phone)
        email = extra.pop("email", None)
        user = self.model(phone=phone, email=self.normalize_email(email) if email else None, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(phone, password, **extra)

    def create_superuser(self, phone, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_active", True)
        extra.setdefault("is_phone_verified", True)
        if extra.get("is_staff") is not True:
            raise ValueError("Superuser is_staff=True bo'lishi kerak.")
        if extra.get("is_superuser") is not True:
            raise ValueError("Superuser is_superuser=True bo'lishi kerak.")
        return self._create_user(phone, password, **extra)

    def get_by_natural_key(self, username):
        return self.get(phone=normalize_phone(username))


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    phone = models.CharField(
        "telefon",
        max_length=13,
        unique=True,
        validators=[PHONE_VALIDATOR],
        help_text="+998XXXXXXXXX",
    )
    email = models.EmailField("email", null=True, blank=True, unique=True)

    first_name = models.CharField("ism", max_length=80, blank=True)
    last_name = models.CharField("familiya", max_length=80, blank=True)
    avatar = models.ImageField("avatar", upload_to="avatars/%Y/%m/", null=True, blank=True)

    region = models.ForeignKey(
        "catalog.Region",
        verbose_name="viloyat",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    district = models.ForeignKey(
        "catalog.District",
        verbose_name="tuman",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    # Tasdiqlash holatlari
    is_phone_verified = models.BooleanField("telefon tasdiqlangan", default=False)
    is_email_verified = models.BooleanField("email tasdiqlangan", default=False)
    is_verified_seller = models.BooleanField(
        "tasdiqlangan sotuvchi",
        default=False,
        help_text="Admin qo'lda beradi — sotuvchi kartasida ko'k belgi chiqadi.",
    )

    # Telegram bog'lanishi (bot orqali bildirishnoma yuborish uchun)
    telegram_id = models.BigIntegerField("Telegram ID", null=True, blank=True, db_index=True)
    telegram_username = models.CharField("Telegram username", max_length=64, blank=True)

    # Django auth
    is_active = models.BooleanField("faol", default=False)
    is_staff = models.BooleanField("xodim", default=False)

    # Bloklash
    is_banned = models.BooleanField("bloklangan", default=False)
    banned_until = models.DateTimeField("blok muddati", null=True, blank=True)
    ban_reason = models.TextField("blok sababi", blank=True)

    last_seen_at = models.DateTimeField("oxirgi faollik", null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "foydalanuvchi"
        verbose_name_plural = "foydalanuvchilar"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "is_banned"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return self.get_full_name() or self.phone

    def save(self, *args, **kwargs):
        self.phone = normalize_phone(self.phone)
        if not self.email:
            # Bo'sh satr unique cheklovini buzadi, NULL esa buzmaydi.
            self.email = None
        super().save(*args, **kwargs)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name or self.phone

    @property
    def masked_phone(self):
        """+998901234567 -> +998 90 *** ** 67"""
        if len(self.phone) != 13:
            return self.phone
        return f"{self.phone[:4]} {self.phone[4:6]} *** ** {self.phone[-2:]}"

    @property
    def ban_is_active(self):
        if not self.is_banned:
            return False
        if self.banned_until and self.banned_until < timezone.now():
            return False
        return True

    def has_perm_code(self, code):
        """RBAC tekshiruvi — Django permissionlaridan alohida."""
        if self.is_superuser:
            return True
        return self.roles.filter(role__permissions__code=code).exists()

    def permission_codes(self):
        from apps.rbac.models import Permission

        if self.is_superuser:
            return set(Permission.objects.values_list("code", flat=True))
        return set(
            Permission.objects.filter(roles__users__user=self)
            .values_list("code", flat=True)
            .distinct()
        )


class ShopProfile(TimeStampedModel):
    """Do'kon / kompaniya sifatida sotuvchi profili (ixtiyoriy)."""

    user = models.OneToOneField(
        User, verbose_name="egasi", on_delete=models.CASCADE, related_name="shop"
    )
    name = models.CharField("do'kon nomi", max_length=120)
    slug = models.SlugField("slug", max_length=140, unique=True)
    logo = models.ImageField("logo", upload_to="shops/%Y/%m/", null=True, blank=True)
    description = models.TextField("tavsif", blank=True)
    address = models.CharField("manzil", max_length=255, blank=True)
    working_hours = models.CharField(
        "ish vaqti", max_length=120, blank=True, help_text="Masalan: Du-Sha 09:00-18:00"
    )
    website = models.URLField("veb-sayt", blank=True)
    telegram_url = models.URLField("Telegram", blank=True)
    instagram_url = models.URLField("Instagram", blank=True)

    class Meta:
        verbose_name = "do'kon profili"
        verbose_name_plural = "do'kon profillari"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from apps.core.utils import make_unique_slug

            self.slug = make_unique_slug(ShopProfile, self.name, instance=self)
        super().save(*args, **kwargs)


class OTPPurpose(models.TextChoices):
    REGISTER = "register", "Ro'yxatdan o'tish"
    LOGIN = "login", "Kirish"
    RESET_PASSWORD = "reset_password", "Parolni tiklash"
    CHANGE_PHONE = "change_phone", "Telefonni o'zgartirish"


class OTPCode(TimeStampedModel):
    """Bir martalik tasdiqlash kodi.

    Kodning o'zi emas, SHA-256 hash'i saqlanadi: baza sizib chiqsa ham
    amaldagi kodlar foydasiz bo'ladi.
    """

    phone = models.CharField("telefon", max_length=13, db_index=True)
    code_hash = models.CharField("kod hash", max_length=64)
    purpose = models.CharField(
        "maqsad", max_length=20, choices=OTPPurpose.choices, default=OTPPurpose.REGISTER
    )
    attempts = models.PositiveSmallIntegerField("urinishlar", default=0)
    is_used = models.BooleanField("ishlatilgan", default=False)
    expires_at = models.DateTimeField("amal qilish muddati")
    ip_address = models.GenericIPAddressField("IP", null=True, blank=True)

    class Meta:
        verbose_name = "tasdiqlash kodi"
        verbose_name_plural = "tasdiqlash kodlari"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["phone", "purpose", "-created_at"])]

    def __str__(self):
        return f"{self.phone} / {self.purpose}"

    @staticmethod
    def hash_code(code):
        return hashlib.sha256(str(code).encode()).hexdigest()

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def verify(self, code):
        return (
            not self.is_used
            and not self.is_expired
            and self.code_hash == self.hash_code(code)
        )


class LoginAttempt(TimeStampedModel):
    """Brute-force aniqlash uchun kirish urinishlari jurnali."""

    phone = models.CharField("telefon", max_length=32, db_index=True)
    ip_address = models.GenericIPAddressField("IP", null=True, blank=True, db_index=True)
    user_agent = models.CharField("User-Agent", max_length=255, blank=True)
    was_successful = models.BooleanField("muvaffaqiyatli", default=False)

    class Meta:
        verbose_name = "kirish urinishi"
        verbose_name_plural = "kirish urinishlari"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["phone", "-created_at"])]
