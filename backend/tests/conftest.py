"""Umumiy test fixturelari.

Prinsip: har bir fixture eng kichik kerakli ma'lumotni yaratadi.
Katalog kabi qimmat narsalar `session` darajasida emas, `django_db`
bilan mos kelishi uchun funksiya darajasida, lekin yengil qilib
yaratiladi.
"""

import io
from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import (
    AttributeDefinition,
    AttributeOption,
    AttributeType,
    Brand,
    Category,
    District,
    Region,
)
from apps.products.models import Condition, Product, ProductStatus
from apps.rbac.constants import PERMISSION_CATALOG, ROLE_CATALOG, R
from apps.rbac.models import Permission, Role, RolePermission, UserRole

PASSWORD = "Test#Parol2026"


# --------------------------------------------------------------------------
# Klientlar
# --------------------------------------------------------------------------
@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def auth_client(api):
    """Berilgan foydalanuvchi nomidan so'rov yuboradigan klient qaytaradi."""

    def _make(user):
        from rest_framework_simplejwt.tokens import RefreshToken

        client = APIClient()
        token = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        return client

    return _make


# --------------------------------------------------------------------------
# Rollar va foydalanuvchilar
# --------------------------------------------------------------------------
@pytest.fixture
def roles(db):
    """Standart rollar va ruxsatlar — seed_roles bilan bir xil natija."""
    permissions = {}
    for code, (name, group, description) in PERMISSION_CATALOG.items():
        permissions[code] = Permission.objects.create(
            code=code, name=name, group=group, description=description
        )

    created = {}
    for code, spec in ROLE_CATALOG.items():
        role = Role.objects.create(
            code=code,
            name=spec["name"],
            description=spec["description"],
            is_system=spec["is_system"],
            is_staff_role=spec["is_staff_role"],
            order=spec["order"],
        )
        wanted = spec["permissions"]
        codes = permissions.keys() if wanted == "*" else wanted
        for permission_code in codes:
            RolePermission.objects.create(role=role, permission=permissions[permission_code])
        created[code] = role
    return created


def _make_user(phone, roles=None, role_code=R.USER, **extra):
    user = User.objects.create_user(
        phone=phone,
        password=PASSWORD,
        is_active=True,
        is_phone_verified=True,
        **extra,
    )
    if roles and role_code in roles:
        UserRole.objects.create(user=user, role=roles[role_code])
    return user


@pytest.fixture
def user(db, roles):
    return _make_user("+998901000101", roles, first_name="Oddiy", last_name="Foydalanuvchi")


@pytest.fixture
def seller(db, roles, region):
    return _make_user(
        "+998901000102", roles, first_name="Sotuvchi", last_name="Testov", region=region
    )


@pytest.fixture
def other_seller(db, roles, region):
    return _make_user("+998901000103", roles, first_name="Boshqa", region=region)


@pytest.fixture
def moderator(db, roles):
    user = _make_user("+998901000104", roles, role_code=R.MODERATOR, first_name="Moderator")
    user.is_staff = True
    user.save(update_fields=["is_staff"])
    return user


@pytest.fixture
def admin(db, roles):
    user = _make_user("+998901000105", roles, role_code=R.ADMIN, first_name="Admin")
    user.is_staff = True
    user.save(update_fields=["is_staff"])
    return user


@pytest.fixture
def superadmin(db, roles):
    user = _make_user("+998901000106", roles, role_code=R.SUPERADMIN, first_name="Bosh")
    user.is_staff = True
    user.is_superuser = True
    user.save(update_fields=["is_staff", "is_superuser"])
    return user


# --------------------------------------------------------------------------
# Katalog
# --------------------------------------------------------------------------
@pytest.fixture
def region(db):
    region = Region.objects.create(name_uz="Toshkent shahri", name_ru="Ташкент", slug="toshkent")
    District.objects.create(region=region, name_uz="Chilonzor", slug="chilonzor")
    return region


@pytest.fixture
def district(region):
    return region.districts.first()


@pytest.fixture
def brand(db):
    return Brand.objects.create(name="ASUS", slug="asus", is_active=True)


@pytest.fixture
def category(db):
    """Ota + bola kategoriya: meros testlari uchun kerak."""
    parent = Category.objects.create(name_uz="Noutbuklar", slug="noutbuklar", is_active=True)
    child = Category.objects.create(
        name_uz="Gaming noutbuklar", slug="gaming-noutbuklar", parent=parent, is_active=True
    )

    # Ildizdagi xususiyat — meros orqali bolaga ham tushishi kerak.
    AttributeDefinition.objects.create(
        category=parent,
        code="warranty_months",
        label_uz="Kafolat",
        data_type=AttributeType.INTEGER,
        unit="oy",
        is_filterable=True,
    )
    AttributeDefinition.objects.create(
        category=child,
        code="cpu",
        label_uz="Protsessor",
        data_type=AttributeType.TEXT,
        is_required=True,
        is_in_card=True,
    )
    AttributeDefinition.objects.create(
        category=child,
        code="ram_gb",
        label_uz="Operativ xotira",
        data_type=AttributeType.INTEGER,
        unit="GB",
        is_required=True,
        is_filterable=True,
        is_in_card=True,
        min_value=2,
        max_value=256,
    )
    os_attribute = AttributeDefinition.objects.create(
        category=child,
        code="os",
        label_uz="Operatsion tizim",
        data_type=AttributeType.SELECT,
        is_filterable=True,
    )
    AttributeOption.objects.create(attribute=os_attribute, value="win11", label_uz="Windows 11")
    AttributeOption.objects.create(attribute=os_attribute, value="linux", label_uz="Linux")

    return child


@pytest.fixture
def parent_category(category):
    return category.parent


# --------------------------------------------------------------------------
# Mahsulot
# --------------------------------------------------------------------------
@pytest.fixture
def product_payload(category, brand, region):
    return {
        "title": "ASUS ROG Strix G16 gaming noutbuk",
        "description": "Yaxshi holatda, 8 oy ishlatilgan. Original quti bor.",
        "category": category.id,
        "brand": brand.id,
        "region": region.id,
        "price": "12500000",
        "condition": Condition.GOOD,
        "specs": {"cpu": "Intel Core i7", "ram_gb": 16, "warranty_months": 6},
    }


@pytest.fixture
def make_product(db, category, brand, region):
    """Bazaga to'g'ridan-to'g'ri mahsulot yozadi (API'siz)."""

    def _make(seller, status=ProductStatus.APPROVED, **overrides):
        now = timezone.now()
        fields = {
            "title": overrides.pop("title", "ASUS ROG Strix G16"),
            "description": "Test uchun yaratilgan e'lon tavsifi.",
            "seller": seller,
            "category": overrides.pop("category", category),
            "brand": overrides.pop("brand", brand),
            "region": region,
            "price": overrides.pop("price", 12_500_000),
            "condition": overrides.pop("condition", Condition.GOOD),
            "status": status,
            "specs": overrides.pop("specs", {"cpu": "Intel Core i7", "ram_gb": 16}),
        }
        fields.update(overrides)

        if status in (ProductStatus.APPROVED, ProductStatus.SOLD, ProductStatus.RESERVED):
            fields.setdefault("published_at", now)
            fields.setdefault("expires_at", now + timedelta(days=30))

        product = Product.objects.create(**fields)

        from apps.products.services import update_search_vector

        update_search_vector(product)
        product.refresh_from_db()
        return product

    return _make


@pytest.fixture
def product(make_product, seller):
    return make_product(seller)


# --------------------------------------------------------------------------
# Media
# --------------------------------------------------------------------------
def build_image_bytes(width=800, height=600, fmt="JPEG"):
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (30, 41, 59)).save(buffer, format=fmt)
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def image_file():
    """Haqiqiy JPEG — magic bytes validatsiyasidan o'tadi."""

    def _make(name="test.jpg", width=800, height=600):
        return SimpleUploadedFile(name, build_image_bytes(width, height), content_type="image/jpeg")

    return _make


@pytest.fixture
def fake_image_file():
    """Kengaytmasi .jpg, lekin ichi oddiy matn."""
    return SimpleUploadedFile("soxta.jpg", b"bu rasm emas" * 100, content_type="image/jpeg")


# --------------------------------------------------------------------------
# Izolyatsiya
# --------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def clear_caches():
    """Har test toza keshdan boshlasin.

    Throttle tarixi va katalog keshi locmem'da saqlanadi va jarayon
    davomida testlar orasida oqib o'tadi — bu tartibga bog'liq,
    tushunish qiyin xatoliklarga olib keladi.
    """
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()
