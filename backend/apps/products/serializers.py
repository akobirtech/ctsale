"""Mahsulot serializerlari.

Uch xil ko'rinish:
  ProductCardSerializer   — ro'yxat/katalog (yengil)
  ProductDetailSerializer — mahsulot sahifasi (to'liq + SEO)
  ProductWriteSerializer  — yaratish/tahrirlash
"""

from django.conf import settings
from rest_framework import serializers

from apps.accounts.serializers import PublicSellerSerializer
from apps.catalog.models import Brand, Category, District, Region
from apps.catalog.serializers import CategoryBriefSerializer
from apps.mediafiles.serializers import ProductImageSerializer, ProductVideoSerializer

from .models import Condition, Currency, Product, ProductStatus
from .services import validate_specs


class SpecDisplaySerializer(serializers.Serializer):
    """Xususiyatni ko'rsatishga tayyor ko'rinishda: nom, qiymat, birlik."""

    code = serializers.CharField()
    label = serializers.CharField()
    value = serializers.CharField()
    unit = serializers.CharField()
    in_card = serializers.BooleanField()


def build_spec_display(product, lang=None):
    """`specs` JSONB ni kategoriya sxemasi bilan birlashtiradi."""
    if not product.specs or not product.category_id:
        return []

    lang = lang if lang in settings.SUPPORTED_LANGUAGES else settings.DEFAULT_LANGUAGE
    rows = []

    for definition in product.category.inherited_attributes():
        value = product.specs.get(definition.code)
        if value in (None, "", []):
            continue

        if isinstance(value, bool):
            display = "Ha" if value else "Yo'q"
        elif isinstance(value, list):
            display = ", ".join(_option_label(definition, v, lang) for v in value)
        else:
            display = _option_label(definition, value, lang)

        rows.append(
            {
                "code": definition.code,
                "label": getattr(definition, f"label_{lang}", "") or definition.label_uz,
                "value": display,
                "unit": definition.unit,
                "in_card": definition.is_in_card,
            }
        )
    return rows


def _option_label(definition, value, lang):
    """SELECT qiymati uchun texnik kod emas, o'qiladigan matn."""
    if not definition.has_options:
        return str(value)
    for option in definition.options.all():
        if option.value == str(value):
            return getattr(option, f"label_{lang}", "") or option.label_uz
    return str(value)


class PriceMixin:
    def get_price_display(self, obj):
        if obj.price_on_request:
            return "So'rov bo'yicha"
        if obj.price is None:
            return "Kelishiladi"
        formatted = f"{int(obj.price):,}".replace(",", " ")
        if obj.currency == Currency.USD:
            return f"${formatted}"
        return f"{formatted} so'm"


# --------------------------------------------------------------------------
# O'qish
# --------------------------------------------------------------------------
class ProductCardSerializer(PriceMixin, serializers.ModelSerializer):
    """Katalog kartasi — faqat ro'yxatda kerak bo'ladigan maydonlar."""

    price_display = serializers.SerializerMethodField()
    condition_display = serializers.CharField(source="get_condition_display", read_only=True)
    primary_image = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    brand_name = serializers.CharField(source="brand.name", read_only=True, default=None)
    region_name = serializers.SerializerMethodField()
    card_specs = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "slug", "title", "price", "currency", "price_display",
            "is_negotiable", "price_on_request", "condition", "condition_display",
            "status", "primary_image", "category", "category_name",
            "brand", "brand_name", "region_name", "card_specs",
            "views_count", "favorites_count", "is_favorited", "is_featured",
            "published_at", "created_at", "url",
        ]

    def get_primary_image(self, obj):
        image = obj.primary_image
        if image is None:
            return None
        request = self.context.get("request")
        url = image.thumb_url or ""
        if request and url:
            url = request.build_absolute_uri(url)
        return {"url": url, "alt": image.alt_text or obj.title}

    def get_category_name(self, obj):
        if not obj.category_id:
            return None
        lang = self.context.get("lang", settings.DEFAULT_LANGUAGE)
        return getattr(obj.category, f"name_{lang}", "") or obj.category.name_uz

    def get_region_name(self, obj):
        if not obj.region_id:
            return None
        lang = self.context.get("lang", settings.DEFAULT_LANGUAGE)
        return getattr(obj.region, f"name_{lang}", "") or obj.region.name_uz

    def get_card_specs(self, obj):
        """Kartada ko'rsatiladigan 3 ta xususiyat (masalan RTX 4060 / 16GB / 1TB)."""
        rows = self.context.get("spec_rows", {}).get(obj.pk)
        if rows is None:
            rows = build_spec_display(obj, self.context.get("lang"))
        return [
            f"{row['value']} {row['unit']}".strip()
            for row in rows
            if row["in_card"]
        ][:3]

    def get_is_favorited(self, obj):
        favorited = self.context.get("favorited_ids")
        if favorited is None:
            return False
        return obj.pk in favorited

    def get_url(self, obj):
        lang = self.context.get("lang", settings.DEFAULT_LANGUAGE)
        return f"/{lang}/product/{obj.slug}"


class ProductDetailSerializer(PriceMixin, serializers.ModelSerializer):
    """Mahsulot sahifasi — SEO va JSON-LD uchun hamma narsa bor."""

    price_display = serializers.SerializerMethodField()
    condition_display = serializers.CharField(source="get_condition_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    images = ProductImageSerializer(many=True, read_only=True)
    videos = ProductVideoSerializer(many=True, read_only=True)
    seller = PublicSellerSerializer(read_only=True)

    category_detail = serializers.SerializerMethodField()
    breadcrumbs = serializers.SerializerMethodField()
    brand_name = serializers.CharField(source="brand.name", read_only=True, default=None)
    region_name = serializers.SerializerMethodField()
    district_name = serializers.SerializerMethodField()

    spec_rows = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    seo = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "slug", "title", "description",
            "price", "currency", "price_display", "is_negotiable",
            "price_on_request", "is_exchange_possible", "quantity",
            "condition", "condition_display", "status", "status_display",
            "usage_period", "defects", "repair_history", "has_warranty",
            "warranty_until", "has_original_box", "accessories", "purchase_date",
            "specs", "spec_rows",
            "images", "videos", "seller",
            "category", "category_detail", "breadcrumbs", "brand", "brand_name",
            "model_name", "region", "region_name", "district", "district_name",
            "address_note", "contact_name",
            "views_count", "favorites_count", "is_favorited", "is_featured",
            "published_at", "created_at", "updated_at", "expires_at", "sold_at",
            "seo",
        ]

    def get_category_detail(self, obj):
        if not obj.category_id:
            return None
        return CategoryBriefSerializer(obj.category, context=self.context).data

    def get_breadcrumbs(self, obj):
        if not obj.category_id:
            return []
        return CategoryBriefSerializer(
            obj.category.ancestors(include_self=True), many=True, context=self.context
        ).data

    def get_region_name(self, obj):
        return obj.region.name_uz if obj.region_id else None

    def get_district_name(self, obj):
        return obj.district.name_uz if obj.district_id else None

    def get_spec_rows(self, obj):
        return build_spec_display(obj, self.context.get("lang"))

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_seo(self, obj):
        """Frontend `<head>` uchun tayyor ma'lumot (hreflang, OG, JSON-LD)."""
        from apps.seo.services import product_seo_payload

        return product_seo_payload(obj, lang=self.context.get("lang"))


# --------------------------------------------------------------------------
# Yozish
# --------------------------------------------------------------------------
class ProductWriteSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    brand = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.filter(is_active=True), required=False, allow_null=True
    )
    region = serializers.PrimaryKeyRelatedField(queryset=Region.objects.filter(is_active=True))
    district = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.filter(is_active=True), required=False, allow_null=True
    )

    class Meta:
        model = Product
        fields = [
            "id", "title", "description", "category", "brand", "model_name",
            "price", "currency", "is_negotiable", "price_on_request",
            "is_exchange_possible", "quantity", "condition",
            "usage_period", "defects", "repair_history", "has_warranty",
            "warranty_until", "has_original_box", "accessories", "purchase_date",
            "specs", "region", "district", "address_note",
            "contact_phone", "contact_name",
            "seo_title", "seo_description", "seo_keywords",
            "og_title", "og_description",
        ]
        read_only_fields = ["id"]

    def validate_title(self, value):
        value = " ".join(value.split())
        if len(value) < 10:
            raise serializers.ValidationError(
                "Sarlavha kamida 10 ta belgidan iborat bo'lsin — "
                "xaridor nimani sotayotganingizni tushunsin."
            )
        return value

    def validate_description(self, value):
        value = value.strip()
        if len(value) < 20:
            raise serializers.ValidationError(
                "Tavsif kamida 20 ta belgidan iborat bo'lsin."
            )
        return value

    def validate_category(self, value):
        if value.children.filter(is_active=True).exists():
            raise serializers.ValidationError(
                "Aniqroq (ichki) kategoriyani tanlang — bu kategoriyada ichki bo'limlar bor."
            )
        return value

    def validate(self, attrs):
        instance = self.instance

        def current(field, default=None):
            if field in attrs:
                return attrs[field]
            return getattr(instance, field, default)

        # --- Narx mantiqi ---
        price = current("price")
        price_on_request = current("price_on_request", False)
        is_negotiable = current("is_negotiable", False)

        if price is None and not (price_on_request or is_negotiable):
            raise serializers.ValidationError(
                {
                    "price": "Narxni kiriting yoki «Kelishiladi» / "
                    "«So'rov bo'yicha» variantini belgilang."
                }
            )
        if price is not None and price <= 0:
            raise serializers.ValidationError({"price": "Narx noldan katta bo'lishi kerak."})
        if price is not None and price_on_request:
            raise serializers.ValidationError(
                {"price_on_request": "Narx ko'rsatilgan bo'lsa «So'rov bo'yicha» belgilanmaydi."}
            )

        # --- Hudud mosligi ---
        region = current("region")
        district = current("district")
        if district and region and district.region_id != region.id:
            raise serializers.ValidationError(
                {"district": "Tanlangan tuman ko'rsatilgan viloyatga tegishli emas."}
            )

        # --- Ishlatilgan mahsulot maydonlari yangiga tegishli emas ---
        condition = current("condition")
        if condition == Condition.NEW:
            for field in ("usage_period", "defects", "repair_history"):
                if attrs.get(field):
                    raise serializers.ValidationError(
                        {field: "Bu maydon faqat ishlatilgan mahsulot uchun to'ldiriladi."}
                    )

        # --- Kafolat ---
        if current("has_warranty") and not current("warranty_until"):
            raise serializers.ValidationError(
                {"warranty_until": "Kafolat bor bo'lsa, uning muddatini ko'rsating."}
            )

        # --- Xususiyatlar kategoriyaga mos bo'lsin ---
        category = current("category")
        if category is not None:
            attrs["specs"] = validate_specs(category, attrs.get("specs", current("specs", {})))

        return attrs


class ProductStatusActionSerializer(serializers.Serializer):
    """`/products/{id}/status/` uchun."""

    status = serializers.ChoiceField(choices=ProductStatus.choices)
