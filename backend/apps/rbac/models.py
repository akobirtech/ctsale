"""Rol asosidagi ruxsatlar (RBAC).

Django'ning o'z permission tizimi model/CRUD ga bog'langan. Bizga
biznes harakatlari kerak ("mahsulotni tasdiqlash", "Telegramga yuborish"),
shuning uchun alohida, kod asosidagi tizim ishlatiladi.

    User --< UserRole >-- Role --< RolePermission >-- Permission(code)

Yangi rol yaratish uchun kod o'zgartirish shart emas — admin panelda
rol yaratib, kerakli permissionlarni belgilash yetarli.
"""

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class PermissionGroup(models.TextChoices):
    PRODUCT = "product", "Mahsulotlar"
    USER = "user", "Foydalanuvchilar"
    CATALOG = "catalog", "Katalog"
    MODERATION = "moderation", "Moderatsiya"
    TELEGRAM = "telegram", "Telegram"
    REPORT = "report", "Shikoyatlar"
    SYSTEM = "system", "Tizim"


class Permission(TimeStampedModel):
    """Bitta aniq harakatga ruxsat. `code` — kodda ishlatiladigan kalit."""

    code = models.SlugField(
        "kod", max_length=60, unique=True, help_text="resurs.harakat, masalan: product.approve"
    )
    name = models.CharField("nomi", max_length=120)
    description = models.CharField("izoh", max_length=255, blank=True)
    group = models.CharField(
        "guruh", max_length=20, choices=PermissionGroup.choices, default=PermissionGroup.SYSTEM
    )

    class Meta:
        verbose_name = "ruxsat"
        verbose_name_plural = "ruxsatlar"
        ordering = ["group", "code"]

    def __str__(self):
        return self.code


class Role(TimeStampedModel):
    code = models.SlugField("kod", max_length=40, unique=True)
    name = models.CharField("nomi", max_length=80)
    description = models.CharField("izoh", max_length=255, blank=True)
    permissions = models.ManyToManyField(
        Permission, verbose_name="ruxsatlar", through="RolePermission", related_name="roles"
    )
    is_system = models.BooleanField(
        "tizim roli",
        default=False,
        help_text="Tizim rolini o'chirib bo'lmaydi (SUPERADMIN, USER).",
    )
    is_staff_role = models.BooleanField(
        "xodim roli", default=False, help_text="Bu rol admin panelga kirish huquqini beradi."
    )
    order = models.PositiveSmallIntegerField("tartib", default=0)

    class Meta:
        verbose_name = "rol"
        verbose_name_plural = "rollar"
        ordering = ["order", "code"]

    def __str__(self):
        return self.name

    @property
    def permission_codes(self):
        return list(self.permissions.values_list("code", flat=True))


class RolePermission(TimeStampedModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name="permission_roles"
    )

    class Meta:
        verbose_name = "rol ruxsati"
        verbose_name_plural = "rol ruxsatlari"
        constraints = [
            models.UniqueConstraint(fields=["role", "permission"], name="uniq_role_permission")
        ]

    def __str__(self):
        return f"{self.role.code} -> {self.permission.code}"


class UserRole(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="foydalanuvchi",
        on_delete=models.CASCADE,
        related_name="roles",
    )
    role = models.ForeignKey(Role, verbose_name="rol", on_delete=models.CASCADE, related_name="users")
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="kim bergan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        verbose_name = "foydalanuvchi roli"
        verbose_name_plural = "foydalanuvchi rollari"
        constraints = [models.UniqueConstraint(fields=["user", "role"], name="uniq_user_role")]
        indexes = [models.Index(fields=["user"])]

    def __str__(self):
        return f"{self.user} -> {self.role.code}"
