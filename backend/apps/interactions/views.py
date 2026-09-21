"""Sevimlilar, taqqoslash va shikoyatlar."""

from django.db.models import F
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.core.exceptions import BusinessError
from apps.products.models import Product, PUBLIC_STATUSES
from apps.products.serializers import ProductCardSerializer
from apps.rbac.constants import P
from apps.rbac.permissions import IsNotBanned, require_any

from .models import Favorite, Report, ReportReason, ReportStatus
from .serializers import FavoriteSerializer, ReportAdminSerializer, ReportSerializer

# Taqqoslashda bir vaqtda ushlab turiladigan eng ko'p mahsulot.
MAX_COMPARE_ITEMS = 4


class FavoriteViewSet(viewsets.GenericViewSet):
    """Sevimlilar.

    Ro'yxat foydalanuvchiga bog'langan, shuning uchun alohida
    `product_id` bo'yicha izlash o'rniga toggle ishlatiladi —
    bu frontend uchun eng kam so'rov degani.
    """

    permission_classes = [IsAuthenticated, IsNotBanned]
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        return (
            Favorite.objects.filter(user=self.request.user)
            .select_related("product", "product__category", "product__brand", "product__region")
            .prefetch_related("product__images")
            .order_by("-created_at")
        )

    def list(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        products = [favorite.product for favorite in page]

        serializer = ProductCardSerializer(
            products,
            many=True,
            context={
                "request": request,
                "lang": request.query_params.get("lang", "uz"),
                # Bu ro'yxatdagi hamma narsa ta'rifi bo'yicha sevimli.
                "favorited_ids": {product.pk for product in products},
            },
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["post"])
    def toggle(self, request):
        slug = request.data.get("slug")
        if not slug:
            raise BusinessError("Mahsulot ko'rsatilmadi.", code="slug_required")

        product = Product.objects.filter(slug=slug, status__in=PUBLIC_STATUSES).first()
        if product is None:
            raise BusinessError(
                "Mahsulot topilmadi.", code="not_found", status_code=status.HTTP_404_NOT_FOUND
            )

        favorite = Favorite.objects.filter(user=request.user, product=product).first()

        if favorite:
            favorite.delete()
            Product.all_objects.filter(pk=product.pk).update(
                favorites_count=F("favorites_count") - 1
            )
            return Response({"is_favorited": False, "detail": "Sevimlilardan olib tashlandi."})

        Favorite.objects.create(user=request.user, product=product)
        Product.all_objects.filter(pk=product.pk).update(
            favorites_count=F("favorites_count") + 1
        )
        return Response(
            {"is_favorited": True, "detail": "Sevimlilarga qo'shildi."},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def ids(self, request):
        """Faqat IDlar — katalogda yurakchalarni belgilash uchun yengil so'rov."""
        return Response(
            {"ids": list(self.get_queryset().values_list("product_id", flat=True))}
        )


class CompareViewSet(viewsets.GenericViewSet):
    """Taqqoslash.

    Ro'yxat brauzerda (localStorage) saqlanadi — mehmon ham
    foydalana olsin. Server faqat sluglar bo'yicha to'liq
    ma'lumotni qaytaradi.
    """

    permission_classes = [AllowAny]

    @action(detail=False, methods=["get"])
    def items(self, request):
        slugs = [s for s in (request.query_params.get("slugs") or "").split(",") if s]
        if not slugs:
            return Response({"results": [], "attributes": []})

        products = list(
            Product.objects.with_relations()
            .filter(slug__in=slugs[:MAX_COMPARE_ITEMS], status__in=PUBLIC_STATUSES)
        )

        lang = request.query_params.get("lang", "uz")
        serializer = ProductCardSerializer(
            products, many=True, context={"request": request, "lang": lang}
        )

        # Taqqoslash jadvali uchun umumiy xususiyatlar ro'yxati:
        # turli kategoriyadagi mahsulotlar ham solishtirilishi mumkin.
        attributes = []
        seen = set()
        for product in products:
            if not product.category_id:
                continue
            for definition in product.category.inherited_attributes():
                if definition.code in seen:
                    continue
                seen.add(definition.code)
                attributes.append(
                    {
                        "code": definition.code,
                        "label": getattr(definition, f"label_{lang}", "") or definition.label_uz,
                        "unit": definition.unit,
                    }
                )

        return Response({"results": serializer.data, "attributes": attributes})


class ReportViewSet(viewsets.GenericViewSet):
    """Shikoyatlar: foydalanuvchi yuboradi, xodim ko'radi."""

    serializer_class = ReportSerializer

    def get_permissions(self):
        if self.action in ("list", "resolve"):
            return [IsAuthenticated(), require_any(P.REPORT_VIEW, P.REPORT_RESOLVE)()]
        return [IsAuthenticated(), IsNotBanned()]

    def get_throttles(self):
        if self.action == "create":
            self.throttle_scope = "report"
            return [ScopedRateThrottle()]
        return super().get_throttles()

    @action(detail=False, methods=["get"])
    def reasons(self, request):
        return Response(
            [{"value": value, "label": label} for value, label in ReportReason.choices]
        )

    def create(self, request):
        serializer = ReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = Product.objects.filter(
            slug=serializer.validated_data["slug"], status__in=PUBLIC_STATUSES
        ).first()
        if product is None:
            raise BusinessError(
                "Mahsulot topilmadi.", code="not_found", status_code=status.HTTP_404_NOT_FOUND
            )

        if product.seller_id == request.user.id:
            raise BusinessError(
                "O'z e'loningizga shikoyat qila olmaysiz.", code="own_product"
            )

        report, created = Report.objects.get_or_create(
            product=product,
            reporter=request.user,
            defaults={
                "reason": serializer.validated_data["reason"],
                "comment": serializer.validated_data.get("comment", ""),
            },
        )
        if not created:
            raise BusinessError(
                "Siz bu e'lon haqida allaqachon shikoyat yuborgansiz.",
                code="already_reported",
                status_code=status.HTTP_409_CONFLICT,
            )

        return Response(
            {"detail": "Shikoyatingiz qabul qilindi. Moderatorlar ko'rib chiqadi."},
            status=status.HTTP_201_CREATED,
        )

    def list(self, request):
        queryset = Report.objects.select_related(
            "product", "reporter", "resolved_by"
        ).order_by("-created_at")

        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status__in=status_filter.split(","))

        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(
            ReportAdminSerializer(page, many=True, context={"request": request}).data
        )

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        report = Report.objects.filter(pk=pk).first()
        if report is None:
            raise BusinessError(
                "Shikoyat topilmadi.", code="not_found", status_code=status.HTTP_404_NOT_FOUND
            )

        new_status = request.data.get("status", ReportStatus.RESOLVED)
        if new_status not in dict(ReportStatus.choices):
            raise BusinessError("Noto'g'ri status.", code="invalid_status")

        from django.utils import timezone

        report.status = new_status
        report.resolution_note = request.data.get("note", "")[:1000]
        report.resolved_by = request.user
        report.resolved_at = timezone.now()
        report.save()

        from apps.analytics.services import log_action

        log_action(
            actor=request.user,
            action="update",
            target=report,
            target_label=f"Shikoyat: {report.product.title}",
            note=f"{new_status}: {report.resolution_note}",
            request=request,
        )

        return Response({"detail": "Shikoyat bo'yicha qaror saqlandi."})
