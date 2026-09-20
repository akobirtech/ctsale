"""Katalog endpointlari.

O'qish hammaga ochiq (SEO va mehmon foydalanuvchilar uchun), yozish
esa tegishli ruxsatga ega xodimlarga.
"""

from django.db.models import Prefetch
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.rbac.constants import P
from apps.rbac.permissions import require

from .models import AttributeDefinition, Brand, Category, Region
from .serializers import (
    AttributeDefinitionSerializer,
    AttributeDefinitionWriteSerializer,
    BrandSerializer,
    CategorySerializer,
    CategoryTreeSerializer,
    CategoryWriteSerializer,
    RegionSerializer,
)

# Katalog kamdan-kam o'zgaradi, lekin deyarli har sahifada kerak.
CATALOG_CACHE_SECONDS = 300


class ReadWritePermissionMixin:
    """O'qish hammaga, o'zgartirish esa `write_permission` egasiga.

    `public_actions` — ochiq qoladigan action nomlari. Yangi o'qish
    action'i qo'shilganda uni shu ro'yxatga kiritish kerak, aks holda
    u yopiq bo'lib qoladi (xavfsiz standart).
    """

    write_permission = None
    public_actions = ("list", "retrieve")

    def get_permissions(self):
        if self.action in self.public_actions:
            return [AllowAny()]
        return [require(self.write_permission)()]


class RegionViewSet(ReadWritePermissionMixin, viewsets.ModelViewSet):
    """Viloyatlar va tumanlar."""

    serializer_class = RegionSerializer
    write_permission = P.LOCATION_MANAGE
    pagination_class = None
    lookup_field = "slug"

    def get_queryset(self):
        queryset = Region.objects.filter(is_active=True).order_by("order", "name_uz")
        if self.request.query_params.get("with_districts") == "true":
            queryset = queryset.prefetch_related("districts")
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["with_districts"] = (
            self.request.query_params.get("with_districts") == "true"
        )
        return context


class CategoryViewSet(ReadWritePermissionMixin, viewsets.ModelViewSet):
    write_permission = P.CATEGORY_MANAGE
    public_actions = ("list", "retrieve", "tree", "attributes")
    lookup_field = "slug"
    pagination_class = None

    def get_queryset(self):
        queryset = Category.objects.select_related("parent")
        if self.action in ("list", "retrieve", "tree"):
            queryset = queryset.filter(is_active=True)
        return queryset.order_by("order", "name_uz")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return CategoryWriteSerializer
        return CategorySerializer

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(CATALOG_CACHE_SECONDS))
    def tree(self, request):
        """Butun daraxtni bitta so'rovda qaytaradi.

        Barcha kategoriyalar bir marta o'qiladi va daraxt xotirada
        quriladi — rekursiv so'rovlar (N+1) bo'lmaydi.
        """
        categories = list(
            Category.objects.filter(is_active=True).order_by("order", "name_uz")
        )
        by_parent = {}
        for category in categories:
            by_parent.setdefault(category.parent_id, []).append(category)

        for category in categories:
            category.prefetched_children = by_parent.get(category.pk, [])

        roots = by_parent.get(None, [])
        serializer = CategoryTreeSerializer(
            roots, many=True, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="attributes")
    def attributes(self, request, slug=None):
        """Kategoriya uchun xususiyatlar (ota kategoriyalardan meros bilan).

        E'lon qo'shish formasi shu ro'yxat asosida quriladi.
        """
        category = self.get_object()
        serializer = AttributeDefinitionSerializer(
            category.inherited_attributes(), many=True, context=self.get_serializer_context()
        )
        return Response(serializer.data)


class BrandViewSet(ReadWritePermissionMixin, viewsets.ModelViewSet):
    serializer_class = BrandSerializer
    write_permission = P.BRAND_MANAGE
    public_actions = ("list", "retrieve", "popular")
    lookup_field = "slug"
    pagination_class = None

    def get_queryset(self):
        queryset = Brand.objects.all()
        if self.action in ("list", "retrieve", "popular"):
            queryset = queryset.filter(is_active=True)
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset.order_by("order", "name")

    @action(detail=False, methods=["get"])
    def popular(self, request):
        brands = self.get_queryset().filter(is_popular=True)[:20]
        return Response(self.get_serializer(brands, many=True).data)


class AttributeViewSet(ReadWritePermissionMixin, viewsets.ModelViewSet):
    """Xususiyat sxemasi — asosan admin uchun."""

    write_permission = P.ATTRIBUTE_MANAGE
    pagination_class = None

    def get_queryset(self):
        queryset = AttributeDefinition.objects.select_related("category").prefetch_related(
            Prefetch("options")
        )
        category_slug = self.request.query_params.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        if self.action in ("list", "retrieve"):
            queryset = queryset.filter(is_active=True)
        return queryset.order_by("order", "label_uz")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return AttributeDefinitionWriteSerializer
        return AttributeDefinitionSerializer
