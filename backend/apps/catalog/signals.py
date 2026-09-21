"""Katalog o'zgarganda keshni yaroqsiz qiladi.

Xususiyat sxemasi `Category.inherited_attributes()` da keshlanadi.
Admin panelda xususiyat qo'shilsa yoki kategoriya ko'chirilsa, eski
kesh darhol bekor bo'lishi kerak — aks holda forma va filtrlar bir
soatgacha eski sxemani ko'rsatib turardi.
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import (
    AttributeDefinition,
    AttributeOption,
    Category,
    bump_attributes_cache,
)


@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
@receiver(post_save, sender=AttributeDefinition)
@receiver(post_delete, sender=AttributeDefinition)
@receiver(post_save, sender=AttributeOption)
@receiver(post_delete, sender=AttributeOption)
def invalidate_attribute_cache(sender, **kwargs):
    bump_attributes_cache()
