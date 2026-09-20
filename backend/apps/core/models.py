"""Abstract modellar — barcha ilovalar shulardan meros oladi."""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Yaratilgan va o'zgartirilgan vaqtni saqlaydi."""

    created_at = models.DateTimeField("yaratilgan", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("o'zgartirilgan", auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Tashqariga ko'rinadigan obyektlar uchun taxmin qilib bo'lmaydigan ID.

    Ketma-ket integer ID e'lonlar sonini va o'sish tezligini oshkor qiladi.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """Odatiy `objects` faqat o'chirilmaganlarni qaytaradi."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(models.Model):
    """O'chirish o'rniga belgilash — audit va tiklash imkoniyati uchun."""

    is_deleted = models.BooleanField("o'chirilgan", default=False, db_index=True)
    deleted_at = models.DateTimeField("o'chirilgan vaqt", null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])


class AuditableModel(models.Model):
    """Kim yaratgani va kim oxirgi o'zgartirgani."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="yaratuvchi",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="o'zgartiruvchi",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel, SoftDeleteModel):
    """Loyihaning asosiy obyektlari uchun standart baza."""

    class Meta:
        abstract = True
