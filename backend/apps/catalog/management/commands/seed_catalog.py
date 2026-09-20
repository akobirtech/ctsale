"""Hudud, kategoriya, brend va xususiyatlarni bazaga yozadi (idempotent)."""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.data import ATTRIBUTES, BRANDS, CATEGORIES, COMMON_ATTRIBUTES, REGIONS
from apps.catalog.models import (
    AttributeDefinition,
    AttributeOption,
    Brand,
    Category,
    District,
    Region,
)
from apps.core.utils import make_unique_slug


class Command(BaseCommand):
    help = "Katalogning boshlang'ich ma'lumotlarini yaratadi."

    @transaction.atomic
    def handle(self, *args, **options):
        regions = self._seed_regions()
        categories = self._seed_categories()
        brands = self._seed_brands()
        attributes = self._seed_attributes(categories)

        self.stdout.write(
            self.style.SUCCESS(
                f"Katalog tayyor: {regions[0]} viloyat / {regions[1]} tuman, "
                f"{len(categories)} kategoriya, {brands} brend, "
                f"{attributes} xususiyat"
            )
        )

    # ------------------------------------------------------------------
    def _seed_regions(self):
        region_count = 0
        for order, (uz, ru, en, districts) in enumerate(REGIONS):
            region, created = Region.objects.get_or_create(
                name_uz=uz,
                defaults={
                    "name_ru": ru,
                    "name_en": en,
                    "order": order,
                    "slug": make_unique_slug(Region, uz),
                },
            )
            if not created:
                region.name_ru, region.name_en, region.order = ru, en, order
                region.save(update_fields=["name_ru", "name_en", "order"])
            region_count += 1

            for name in districts:
                District.objects.get_or_create(
                    region=region,
                    name_uz=name,
                    defaults={"slug": make_unique_slug(District, name)},
                )
        return region_count, District.objects.count()

    # ------------------------------------------------------------------
    def _seed_categories(self):
        created = {}
        for order, (slug, uz, ru, en, icon, featured, children) in enumerate(CATEGORIES):
            parent, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    "name_uz": uz,
                    "name_ru": ru,
                    "name_en": en,
                    "icon": icon,
                    "is_featured": featured,
                    "order": order,
                    "parent": None,
                    "is_active": True,
                },
            )
            created[slug] = parent

            for child_order, (c_slug, c_uz, c_ru, c_en) in enumerate(children):
                child, _ = Category.objects.update_or_create(
                    slug=c_slug,
                    defaults={
                        "name_uz": c_uz,
                        "name_ru": c_ru,
                        "name_en": c_en,
                        "parent": parent,
                        "order": child_order,
                        "is_active": True,
                    },
                )
                created[c_slug] = child
        return created

    # ------------------------------------------------------------------
    def _seed_brands(self):
        for order, (name, popular) in enumerate(BRANDS):
            Brand.objects.update_or_create(
                name=name,
                defaults={
                    "is_popular": popular,
                    "order": order,
                    "is_active": True,
                    "slug": make_unique_slug(Brand, name),
                },
            )
        return Brand.objects.count()

    # ------------------------------------------------------------------
    def _seed_attributes(self, categories):
        total = 0

        # Umumiy xususiyatlar — har bir ildiz kategoriyaga. Meros
        # ildizdan pastga ishlagani uchun ichki kategoriyalar ham oladi.
        for slug, category in categories.items():
            if category.parent_id is not None:
                continue
            total += self._create_attributes(category, COMMON_ATTRIBUTES, offset=900)

        for slug, definitions in ATTRIBUTES.items():
            category = categories.get(slug)
            if category is None:
                self.stdout.write(self.style.WARNING(f"Kategoriya topilmadi: {slug}"))
                continue
            total += self._create_attributes(category, definitions)
        return total

    def _create_attributes(self, category, definitions, offset=0):
        count = 0
        for order, spec in enumerate(definitions):
            (code, uz, ru, en, data_type, unit,
             required, filterable, in_card, options) = spec

            attribute, _ = AttributeDefinition.objects.update_or_create(
                category=category,
                code=code,
                defaults={
                    "label_uz": uz,
                    "label_ru": ru,
                    "label_en": en,
                    "data_type": data_type,
                    "unit": unit,
                    "is_required": required,
                    "is_filterable": filterable,
                    "is_in_card": in_card,
                    "is_active": True,
                    "order": offset + order,
                },
            )
            count += 1

            for option_order, (value, label) in enumerate(options):
                AttributeOption.objects.update_or_create(
                    attribute=attribute,
                    value=value,
                    defaults={"label_uz": label, "order": option_order, "is_active": True},
                )
        return count
