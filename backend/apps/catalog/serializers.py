"""Katalog serializerlari.

Ko'p tilli maydonlar (`name_uz/ru/en`) frontendga ikki ko'rinishda
beriladi: `name` — so'ralgan tildagi tayyor matn, `names` — barcha
tillar. Birinchisi oddiy ishlatish uchun, ikkinchisi til almashganda
qayta so'rov yubormaslik uchun.
"""

from django.conf import settings
from rest_framework import serializers

from .models import (
    AttributeDefinition,
    AttributeOption,
    AttributeType,
    Brand,
    Category,
    District,
    Region,
)


def _language(context):
    request = context.get("request")
    lang = None
    if request is not None:
        lang = request.query_params.get("lang") or getattr(request, "language", None)
    if lang not in settings.SUPPORTED_LANGUAGES:
        lang = settings.DEFAULT_LANGUAGE
    return lang


class TranslatedNameMixin:
    """`name` va `names` maydonlarini `name_uz/ru/en` dan yasaydi."""

    translated_prefix = "name"

    def get_name(self, obj):
        lang = _language(self.context)
        prefix = self.translated_prefix
        # Tarjima bo'sh bo'lsa standart tilga qaytamiz: yarim
        # tarjima qilingan katalogda bo'sh nom chiqmasin.
        return (
            getattr(obj, f"{prefix}_{lang}", "")
            or getattr(obj, f"{prefix}_{settings.DEFAULT_LANGUAGE}", "")
        )

    def get_names(self, obj):
        prefix = self.translated_prefix
        return {
            lang: getattr(obj, f"{prefix}_{lang}", "")
            for lang in settings.SUPPORTED_LANGUAGES
        }


# --------------------------------------------------------------------------
# Hudud
# --------------------------------------------------------------------------
class DistrictSerializer(TranslatedNameMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    names = serializers.SerializerMethodField()

    class Meta:
        model = District
        fields = ["id", "slug", "name", "names", "region"]


class RegionSerializer(TranslatedNameMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    names = serializers.SerializerMethodField()
    districts = serializers.SerializerMethodField()

    class Meta:
        model = Region
        fields = ["id", "slug", "name", "names", "order", "districts"]

    def get_districts(self, obj):
        # Faqat so'ralganda yuklaymiz — viloyatlar ro'yxati uchun
        # tumanlar keraksiz yuk bo'ladi.
        if not self.context.get("with_districts"):
            return None
        districts = [d for d in obj.districts.all() if d.is_active]
        return DistrictSerializer(districts, many=True, context=self.context).data


# --------------------------------------------------------------------------
# Xususiyatlar
# --------------------------------------------------------------------------
class AttributeOptionSerializer(TranslatedNameMixin, serializers.ModelSerializer):
    translated_prefix = "label"
    label = serializers.SerializerMethodField(method_name="get_name")
    labels = serializers.SerializerMethodField(method_name="get_names")

    class Meta:
        model = AttributeOption
        fields = ["id", "value", "label", "labels", "order"]


class AttributeDefinitionSerializer(TranslatedNameMixin, serializers.ModelSerializer):
    translated_prefix = "label"
    label = serializers.SerializerMethodField(method_name="get_name")
    labels = serializers.SerializerMethodField(method_name="get_names")
    options = serializers.SerializerMethodField()

    class Meta:
        model = AttributeDefinition
        fields = [
            "id", "code", "label", "labels", "data_type", "unit",
            "is_required", "is_filterable", "is_in_card", "order",
            "min_value", "max_value", "placeholder", "options", "category",
        ]

    def get_options(self, obj):
        if not obj.has_options:
            return []
        options = [o for o in obj.options.all() if o.is_active]
        return AttributeOptionSerializer(options, many=True, context=self.context).data


class AttributeDefinitionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeDefinition
        fields = [
            "id", "category", "code", "label_uz", "label_ru", "label_en",
            "data_type", "unit", "is_required", "is_filterable", "is_in_card",
            "is_active", "order", "min_value", "max_value", "placeholder",
        ]

    def validate(self, attrs):
        data_type = attrs.get("data_type", getattr(self.instance, "data_type", None))
        min_value = attrs.get("min_value", getattr(self.instance, "min_value", None))
        max_value = attrs.get("max_value", getattr(self.instance, "max_value", None))

        if min_value is not None and max_value is not None and min_value > max_value:
            raise serializers.ValidationError(
                {"max_value": "Eng katta qiymat eng kichigidan kam bo'lmasligi kerak."}
            )
        if data_type in (AttributeType.SELECT, AttributeType.MULTISELECT) and (
            min_value is not None or max_value is not None
        ):
            raise serializers.ValidationError(
                {"data_type": "Tanlov turidagi xususiyatda son chegaralari ishlatilmaydi."}
            )
        return attrs

    def validate_code(self, value):
        # `code` — specs JSONB kaliti. O'zgartirilsa eski e'lonlardagi
        # qiymat "yetim" qolib ketadi, shuning uchun bloklaymiz.
        if self.instance and self.instance.code != value:
            raise serializers.ValidationError(
                "Yaratilgandan keyin kodni o'zgartirib bo'lmaydi — "
                "mavjud e'lonlardagi ma'lumot yo'qoladi. Yangi xususiyat yarating."
            )
        return value


# --------------------------------------------------------------------------
# Brend
# --------------------------------------------------------------------------
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = [
            "id", "name", "slug", "logo", "website",
            "is_popular", "order", "products_count",
        ]
        read_only_fields = ["id", "slug", "products_count"]


# --------------------------------------------------------------------------
# Kategoriya
# --------------------------------------------------------------------------
class CategoryBriefSerializer(TranslatedNameMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "slug", "name", "icon"]


class CategorySerializer(TranslatedNameMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    names = serializers.SerializerMethodField()
    level = serializers.IntegerField(read_only=True)
    breadcrumbs = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id", "slug", "name", "names", "parent", "icon", "image",
            "order", "is_featured", "level", "products_count",
            "description", "meta_title", "meta_description", "breadcrumbs",
        ]

    def get_breadcrumbs(self, obj):
        return CategoryBriefSerializer(
            obj.ancestors(include_self=True), many=True, context=self.context
        ).data


class CategoryTreeSerializer(TranslatedNameMixin, serializers.ModelSerializer):
    """Rekursiv daraxt. `children` oldindan yuklangan bo'lishi kutiladi."""

    name = serializers.SerializerMethodField()
    names = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id", "slug", "name", "names", "icon", "image",
            "order", "is_featured", "products_count", "children",
        ]

    def get_children(self, obj):
        children = getattr(obj, "prefetched_children", None)
        if children is None:
            children = [c for c in obj.children.all() if c.is_active]
        return CategoryTreeSerializer(children, many=True, context=self.context).data


class CategoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id", "parent", "name_uz", "name_ru", "name_en", "slug",
            "description", "icon", "image", "order", "is_active",
            "is_featured", "meta_title", "meta_description",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {"slug": {"required": False}}

    def validate_parent(self, value):
        if value is None:
            return value
        if self.instance and value.pk == self.instance.pk:
            raise serializers.ValidationError(
                "Kategoriya o'zining ota kategoriyasi bo'la olmaydi."
            )
        if self.instance:
            # Halqa hosil bo'lmasin: yangi ota mavjud kategoriyaning
            # avlodi bo'lsa, daraxt buziladi.
            if value.pk in self.instance.descendant_ids():
                raise serializers.ValidationError(
                    "Ota kategoriya sifatida o'zining ichki kategoriyasini tanlab bo'lmaydi."
                )
        return value
