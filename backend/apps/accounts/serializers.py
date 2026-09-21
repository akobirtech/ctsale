"""Auth va profil serializerlari."""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.core.utils import normalize_phone

from .models import PHONE_VALIDATOR, ShopProfile, User


class PhoneField(serializers.CharField):
    """Foydalanuvchi qanday yozsa ham +998XXXXXXXXX ga keltiradi."""

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        normalized = normalize_phone(value)
        PHONE_VALIDATOR(normalized)
        return normalized


def _validate_password_strength(value, user=None):
    try:
        validate_password(value, user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(list(exc.messages)) from exc
    return value


# --------------------------------------------------------------------------
# Ro'yxatdan o'tish / kirish
# --------------------------------------------------------------------------
class RegisterSerializer(serializers.Serializer):
    phone = PhoneField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=80, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=80, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Parollar mos kelmadi."}
            )
        _validate_password_strength(attrs["password"])
        return attrs


class OTPVerifySerializer(serializers.Serializer):
    phone = PhoneField(max_length=20)
    code = serializers.CharField(min_length=4, max_length=8)


class OTPRequestSerializer(serializers.Serializer):
    phone = PhoneField(max_length=20)


class LoginSerializer(serializers.Serializer):
    phone = PhoneField(max_length=20)
    password = serializers.CharField(write_only=True, max_length=128)


class PasswordResetRequestSerializer(serializers.Serializer):
    phone = PhoneField(max_length=20)


class PasswordResetConfirmSerializer(serializers.Serializer):
    phone = PhoneField(max_length=20)
    code = serializers.CharField(min_length=4, max_length=8)
    new_password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Parollar mos kelmadi."}
            )
        _validate_password_strength(attrs["new_password"])
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Joriy parol noto'g'ri.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Parollar mos kelmadi."}
            )
        _validate_password_strength(attrs["new_password"], self.context["request"].user)
        return attrs


# --------------------------------------------------------------------------
# Profil
# --------------------------------------------------------------------------
class ShopProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopProfile
        fields = [
            "id", "name", "slug", "logo", "description", "address",
            "working_hours", "website", "telegram_url", "instagram_url",
            "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at"]

    def validate_name(self, value):
        value = (value or "").strip()
        if len(value) < 2:
            raise serializers.ValidationError("Do'kon nomi kamida 2 ta belgidan iborat bo'lsin.")
        return value

    def validate_logo(self, value):
        if not value:
            return value

        from django.core.exceptions import ValidationError as DjangoValidationError

        from apps.mediafiles.validators import validate_image

        try:
            validate_image(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages[0]) from exc
        return value


class UserSerializer(serializers.ModelSerializer):
    """Foydalanuvchining o'zi uchun to'liq profil."""

    full_name = serializers.CharField(source="get_full_name", read_only=True)
    shop = ShopProfileSerializer(read_only=True)
    permissions = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    region_name = serializers.CharField(source="region.name_uz", read_only=True, default=None)
    district_name = serializers.CharField(source="district.name_uz", read_only=True, default=None)

    class Meta:
        model = User
        fields = [
            "id", "phone", "email", "first_name", "last_name", "full_name",
            "avatar", "region", "region_name", "district", "district_name",
            "is_phone_verified", "is_email_verified", "is_verified_seller",
            "telegram_username", "is_staff", "is_superuser", "shop",
            "roles", "permissions", "created_at", "last_seen_at",
        ]
        read_only_fields = [
            "id", "phone", "is_phone_verified", "is_email_verified",
            "is_verified_seller", "is_staff", "is_superuser", "created_at",
            "last_seen_at", "telegram_username",
        ]

    def get_permissions(self, obj):
        return sorted(obj.permission_codes())

    def get_roles(self, obj):
        return list(obj.roles.values_list("role__code", flat=True))


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "avatar", "region", "district"]

    def validate_avatar(self, value):
        """Avatar ham mahsulot rasmi bilan bir xil tekshiruvdan o'tadi.

        Alohida yengilroq qoida yozilmaydi: `.php` ni `.jpg` deb
        nomlash bu yerda ham xuddi shunday ishlaydi.
        """
        if not value:
            return value

        from django.core.exceptions import ValidationError as DjangoValidationError

        from apps.mediafiles.validators import validate_image

        try:
            validate_image(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages[0]) from exc
        return value

    def validate_email(self, value):
        if not value:
            return None
        qs = User.all_objects.filter(email__iexact=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Bu email boshqa hisobga biriktirilgan.")
        return value

    def validate(self, attrs):
        region = attrs.get("region", getattr(self.instance, "region", None))
        district = attrs.get("district", getattr(self.instance, "district", None))
        if district and region and district.region_id != region.id:
            raise serializers.ValidationError(
                {"district": "Tanlangan tuman ko'rsatilgan viloyatga tegishli emas."}
            )
        return attrs


class PublicSellerSerializer(serializers.ModelSerializer):
    """Sotuvchi kartasi — telefon raqam bu yerda YO'Q.

    Raqam faqat alohida, cheklangan endpoint orqali beriladi.
    """

    full_name = serializers.CharField(source="get_full_name", read_only=True)
    shop = ShopProfileSerializer(read_only=True)
    masked_phone = serializers.CharField(read_only=True)
    products_count = serializers.IntegerField(read_only=True, default=0)
    region_name = serializers.CharField(source="region.name_uz", read_only=True, default=None)

    class Meta:
        model = User
        fields = [
            "id", "full_name", "avatar", "masked_phone", "is_verified_seller",
            "shop", "region_name", "products_count", "created_at", "last_seen_at",
        ]
