"""Katalog filtrlari va saralash.

Dinamik xususiyat filtrlari (`spec_ram_gb_min=16`) django-filter
doirasidan tashqarida — ular `apply_spec_filters()` da JSONB
so'rovlariga aylantiriladi.
"""

import django_filters as filters
from django.db.models import Q

from apps.catalog.models import AttributeType, Brand, Category

from .models import Condition, Product, ProductStatus

# Saralash variantlari: tashqi nom -> ORM ifodasi
SORT_OPTIONS = {
    "newest": ("-bumped_at", "-published_at", "-created_at"),
    "oldest": ("published_at", "created_at"),
    "price_asc": ("price", "-published_at"),
    "price_desc": ("-price", "-published_at"),
    "popular": ("-favorites_count", "-views_count", "-published_at"),
    "most_viewed": ("-views_count", "-published_at"),
}
DEFAULT_SORT = "newest"

# `spec_` prefiksidan keyingi qo'shimchalar
SPEC_SUFFIXES = ("_min", "_max")


class ProductFilter(filters.FilterSet):
    category = filters.CharFilter(method="filter_category")
    brand = filters.CharFilter(method="filter_brand")
    region = filters.CharFilter(field_name="region__slug")
    district = filters.CharFilter(field_name="district__slug")
    seller = filters.UUIDFilter(field_name="seller_id")

    condition = filters.BaseInFilter(field_name="condition")
    is_new = filters.BooleanFilter(method="filter_is_new")

    price_min = filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = filters.NumberFilter(field_name="price", lookup_expr="lte")
    currency = filters.CharFilter(field_name="currency")

    has_warranty = filters.BooleanFilter(field_name="has_warranty")
    has_original_box = filters.BooleanFilter(field_name="has_original_box")
    is_exchange_possible = filters.BooleanFilter(field_name="is_exchange_possible")
    is_negotiable = filters.BooleanFilter(field_name="is_negotiable")
    is_featured = filters.BooleanFilter(field_name="is_featured")
    with_video = filters.BooleanFilter(method="filter_with_video")

    class Meta:
        model = Product
        fields = []

    # ------------------------------------------------------------------
    def filter_category(self, queryset, name, value):
        """Kategoriya va uning barcha ichki kategoriyalari."""
        category = Category.objects.filter(slug=value, is_active=True).first()
        if category is None:
            return queryset.none()
        return queryset.filter(category_id__in=category.descendant_ids())

    def filter_brand(self, queryset, name, value):
        """Bir nechta brend: `?brand=asus,msi`"""
        slugs = [s.strip() for s in value.split(",") if s.strip()]
        if not slugs:
            return queryset
        brand_ids = Brand.objects.filter(slug__in=slugs).values_list("id", flat=True)
        return queryset.filter(brand_id__in=list(brand_ids))

    def filter_is_new(self, queryset, name, value):
        if value is None:
            return queryset
        if value:
            return queryset.filter(condition=Condition.NEW)
        return queryset.exclude(condition=Condition.NEW)

    def filter_with_video(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(videos__isnull=False).distinct()


def apply_spec_filters(queryset, query_params, category=None):
    """`spec_<code>` parametrlarini JSONB so'roviga aylantiradi.

    Qo'llab-quvvatlanadigan ko'rinishlar:
        spec_ram_gb=16            aniq moslik
        spec_ram_gb_min=16        kamida
        spec_ram_gb_max=32        ko'pi bilan
        spec_os=win11,win10       ro'yxatdan biri

    Faqat kategoriya sxemasida mavjud va `is_filterable` bo'lgan
    kodlar qabul qilinadi — shunda ixtiyoriy JSONB yo'li bo'ylab
    so'rov yuborib bo'lmaydi.
    """
    if category is None:
        return queryset

    definitions = {
        a.code: a for a in category.inherited_attributes() if a.is_filterable
    }
    if not definitions:
        return queryset

    for key, raw in query_params.items():
        if not key.startswith("spec_") or not raw:
            continue

        body = key[len("spec_"):]
        suffix = ""
        for candidate in SPEC_SUFFIXES:
            if body.endswith(candidate):
                suffix = candidate
                body = body[: -len(candidate)]
                break

        definition = definitions.get(body)
        if definition is None:
            continue

        numeric = definition.data_type in (AttributeType.INTEGER, AttributeType.DECIMAL)

        if suffix and not numeric:
            continue

        if suffix == "_min":
            queryset = _numeric_compare(queryset, body, raw, "gte")
        elif suffix == "_max":
            queryset = _numeric_compare(queryset, body, raw, "lte")
        elif numeric:
            queryset = _numeric_compare(queryset, body, raw, "exact")
        else:
            values = [v.strip() for v in str(raw).split(",") if v.strip()]
            if not values:
                continue
            condition = Q()
            for value in values:
                # MULTISELECT qiymati ro'yxat bo'lgani uchun `contains`
                # ishlatiladi; SELECT/TEXT uchun to'g'ridan-to'g'ri moslik.
                if definition.data_type == AttributeType.MULTISELECT:
                    condition |= Q(specs__contains={body: [value]})
                else:
                    condition |= Q(**{f"specs__{body}": value})
            queryset = queryset.filter(condition)

    return queryset


def _numeric_compare(queryset, code, raw, operator):
    """JSONB ichidagi sonni taqqoslash.

    PostgreSQL JSONB soni raqam sifatida saqlanadi, shuning uchun
    to'g'ridan-to'g'ri `__gte` ishlaydi. Noto'g'ri qiymat kelsa
    filtr e'tiborsiz qoldiriladi — butun so'rov buzilmasin.
    """
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return queryset
    if number.is_integer():
        number = int(number)
    return queryset.filter(**{f"specs__{code}__{operator}": number})


def apply_sort(queryset, sort_key):
    """Saralash. VIP e'lonlar har doim yuqorida turadi."""
    fields = SORT_OPTIONS.get(sort_key or DEFAULT_SORT, SORT_OPTIONS[DEFAULT_SORT])

    if sort_key in ("price_asc", "price_desc"):
        # Narxsiz e'lonlar ro'yxat boshini egallamasligi kerak.
        queryset = queryset.exclude(price__isnull=True)

    return queryset.order_by("-is_featured", *fields)


def build_facets(queryset, category=None):
    """Har bir filtr varianti yonida nechta mahsulot borligini sanaydi.

    Foydalanuvchi natija bermaydigan filtrni bosmasligi uchun.
    """
    from django.db.models import Count, Max, Min

    facets = {}

    facets["condition"] = [
        {"value": row["condition"], "label": dict(Condition.choices)[row["condition"]],
         "count": row["total"]}
        for row in queryset.values("condition").annotate(total=Count("id")).order_by("-total")
    ]

    facets["brand"] = [
        {"value": row["brand__slug"], "label": row["brand__name"], "count": row["total"]}
        for row in queryset.exclude(brand__isnull=True)
        .values("brand__slug", "brand__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:30]
    ]

    facets["region"] = [
        {"value": row["region__slug"], "label": row["region__name_uz"], "count": row["total"]}
        for row in queryset.values("region__slug", "region__name_uz")
        .annotate(total=Count("id"))
        .order_by("-total")[:20]
    ]

    price_range = queryset.exclude(price__isnull=True).aggregate(
        min=Min("price"), max=Max("price")
    )
    facets["price"] = {
        "min": float(price_range["min"]) if price_range["min"] is not None else None,
        "max": float(price_range["max"]) if price_range["max"] is not None else None,
    }

    if category is not None:
        facets["specs"] = _spec_facets(queryset, category)

    return facets


def _spec_facets(queryset, category):
    """Kategoriya xususiyatlari bo'yicha variantlar va ularning soni."""
    rows = []
    definitions = [a for a in category.inherited_attributes() if a.is_filterable]

    # Katalog sahifasida bir necha yuz e'lon bo'ladi — specs ni
    # Python tomonda sanash JSONB bo'yicha N ta so'rovdan arzonroq.
    all_specs = list(queryset.values_list("specs", flat=True)[:5000])

    for definition in definitions:
        counter = {}
        for specs in all_specs:
            value = (specs or {}).get(definition.code)
            if value in (None, "", []):
                continue
            values = value if isinstance(value, list) else [value]
            for item in values:
                counter[str(item)] = counter.get(str(item), 0) + 1

        if not counter:
            continue

        if definition.data_type in (AttributeType.INTEGER, AttributeType.DECIMAL):
            numbers = [float(v) for v in counter if _is_number(v)]
            if not numbers:
                continue
            rows.append(
                {
                    "code": definition.code,
                    "label": definition.label_uz,
                    "type": "range",
                    "unit": definition.unit,
                    "min": min(numbers),
                    "max": max(numbers),
                }
            )
        else:
            labels = {o.value: o.label_uz for o in definition.options.all()}
            options = sorted(counter.items(), key=lambda kv: -kv[1])[:25]
            rows.append(
                {
                    "code": definition.code,
                    "label": definition.label_uz,
                    "type": "choice",
                    "unit": definition.unit,
                    "options": [
                        {"value": value, "label": labels.get(value, value), "count": count}
                        for value, count in options
                    ],
                }
            )
    return rows


def _is_number(value):
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False
