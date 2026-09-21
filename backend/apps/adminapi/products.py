"""Admin panel uchun e'lonlar jadvali.

Alohida modulda: `views.py` da foydalanuvchi, audit va Telegram
bo'limlari bor, e'lonlar mantiqi esa o'z filtrlari va ommaviy
amallari bilan birga o'sib boradi.

Moderatsiya (tasdiqlash / rad etish) ataylab bu yerda emas — u
`moderation` ilovasida, chunki u yerda navbat, tarix va bildirishnoma
mantiqi bor. Bu yerda faqat administrativ amallar: VIP, arxiv,
o'chirish va statusni majburan o'zgartirish.
"""

from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.analytics.services import log_action
from apps.core.exceptions import BusinessError
from apps.products.models import Product, ProductStatus
from apps.rbac.constants import P
from apps.rbac.permissions import require

from .serializers import AdminProductSerializer

# Bulk amallarda bir so'rovda ishlov beriladigan eng ko'p e'lon soni.
# Cheklovsiz qoldirilsa bitta so'rov bazani uzoq band qilishi mumkin.
BULK_LIMIT = 100


class AdminProductViewSet(viewsets.GenericViewSet):
    """E'lonlar jadvali: filtr, qidiruv va ommaviy amallar."""

    serializer_class = AdminProductSerializer

    ACTION_PERMISSIONS = {
        "list": P.PRODUCT_VIEW_ANY,
        "retrieve": P.PRODUCT_VIEW_ANY,
        "feature": P.PRODUCT_FEATURE,
        "force_status": P.PRODUCT_FORCE_STATUS,
        "destroy": P.PRODUCT_DELETE_ANY,
        "restore": P.PRODUCT_DELETE_ANY,
        # `bulk` ichida amalga qarab aniqroq tekshiriladi.
        "bulk": P.PRODUCT_VIEW_ANY,
    }

    def get_permissions(self):
        code = self.ACTION_PERMISSIONS.get(self.action, P.PRODUCT_VIEW_ANY)
        return [IsAuthenticated(), require(code)()]

    def get_queryset(self):
        params = self.request.query_params
        queryset = (
            Product.all_objects.select_related("seller", "category")
            .prefetch_related("images", "telegram_posts")
            .order_by("-created_at", "-id")
        )

        # O'chirilganlar faqat aniq so'ralganda ko'rinadi — admin ularni
        # tiklashi kerak bo'lishi mumkin.
        queryset = queryset.filter(is_deleted=params.get("deleted") == "true")

        status_filter = params.get("status")
        if status_filter:
            queryset = queryset.filter(status__in=status_filter.split(","))

        search = (params.get("search") or "").strip()
        if search:
            # Admin qidiruvi full-text emas: u aniq e'lonni sarlavha,
            # slug yoki sotuvchi raqami bo'yicha topish uchun.
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(slug__icontains=search)
                | Q(seller__phone__icontains=search)
            )

        category = params.get("category")
        if category:
            queryset = queryset.filter(category__slug=category)

        seller = params.get("seller")
        if seller:
            queryset = queryset.filter(seller_id=seller)

        if params.get("featured") == "true":
            queryset = queryset.filter(is_featured=True)

        return queryset

    def list(self, request):
        page = self.paginate_queryset(self.get_queryset())
        data = AdminProductSerializer(page, many=True, context={"request": request}).data
        response = self.get_paginated_response(data)
        response.data["status_counts"] = self._status_counts()
        return response

    @staticmethod
    def _status_counts():
        """Jadval ustidagi hisoblagichlar — bitta so'rovda."""
        rows = Product.objects.values("status").annotate(total=Count("id")).order_by()
        return {row["status"]: row["total"] for row in rows}

    def retrieve(self, request, pk=None):
        product = self._get_product(pk)
        return Response(AdminProductSerializer(product, context={"request": request}).data)

    @staticmethod
    def _get_product(pk):
        product = Product.all_objects.filter(pk=pk).first()
        if product is None:
            raise BusinessError(
                "E'lon topilmadi.", code="not_found", status_code=status.HTTP_404_NOT_FOUND
            )
        return product

    @action(detail=True, methods=["post"])
    def feature(self, request, pk=None):
        """VIP belgisini qo'yadi yoki olib tashlaydi."""
        product = self._get_product(pk)
        days = request.data.get("days")

        product.is_featured = not product.is_featured
        product.featured_until = (
            timezone.now() + timedelta(days=int(days))
            if product.is_featured and days
            else None
        )
        product.save(update_fields=["is_featured", "featured_until", "updated_at"])

        log_action(
            actor=request.user,
            action="feature" if product.is_featured else "unfeature",
            target=product,
            target_label=product.title,
            request=request,
        )
        return Response(
            {"is_featured": product.is_featured, "featured_until": product.featured_until}
        )

    @action(detail=True, methods=["post"], url_path="force-status")
    def force_status(self, request, pk=None):
        """Holat mashinasini chetlab o'tib statusni o'zgartiradi.

        Faqat qo'lda tuzatish uchun: masalan noto'g'ri holatda qotib
        qolgan e'lonni arxivga olish.
        """
        product = self._get_product(pk)
        new_status = request.data.get("status")

        if new_status not in ProductStatus.values:
            raise BusinessError("Noma'lum status.", code="invalid_status")

        old_status = product.status
        if new_status == old_status:
            return Response({"status": old_status, "changed": False})

        product.status = new_status
        product.save(update_fields=["status", "updated_at"])

        log_action(
            actor=request.user,
            action="force_status",
            target=product,
            target_label=product.title,
            changes={"status": [old_status, new_status]},
            note=(request.data.get("reason") or "")[:255],
            request=request,
        )
        return Response({"status": new_status, "changed": True})

    def destroy(self, request, pk=None):
        product = self._get_product(pk)
        product.delete()  # soft delete

        log_action(
            actor=request.user,
            action="delete",
            target=product,
            target_label=product.title,
            note=(request.data.get("reason") or "")[:255],
            request=request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        """O'chirilgan e'lonni qaytaradi."""
        product = self._get_product(pk)
        if not product.is_deleted:
            return Response({"detail": "E'lon o'chirilmagan.", "restored": False})

        product.is_deleted = False
        product.deleted_at = None
        product.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

        log_action(
            actor=request.user,
            action="restore",
            target=product,
            target_label=product.title,
            request=request,
        )
        return Response({"detail": "E'lon tiklandi.", "restored": True})

    @action(detail=False, methods=["post"])
    def bulk(self, request):
        """Bir nechta e'longa bitta amal: `{"action": "...", "ids": [...]}`."""
        action_name = request.data.get("action")
        ids = request.data.get("ids") or []

        if not isinstance(ids, list) or not ids:
            raise BusinessError("E'lonlarni tanlang.", code="ids_required")
        if len(ids) > BULK_LIMIT:
            raise BusinessError(
                f"Bir vaqtda ko'pi bilan {BULK_LIMIT} ta e'lon.", code="too_many"
            )

        handlers = {
            "feature": (P.PRODUCT_FEATURE, self._bulk_feature),
            "unfeature": (P.PRODUCT_FEATURE, self._bulk_unfeature),
            # Arxivlash holat mashinasida deyarli har qanday holatdan
            # ruxsat etilgan, shuning uchun u `force_status` emas.
            "archive": (P.PRODUCT_EDIT_ANY, self._bulk_archive),
            "delete": (P.PRODUCT_DELETE_ANY, self._bulk_delete),
        }
        if action_name not in handlers:
            raise BusinessError("Noma'lum amal.", code="invalid_action")

        # Ro'yxatga kirish huquqi ommaviy amalga ruxsat bermaydi:
        # har bir amal o'z ruxsatini talab qiladi.
        permission, handler = handlers[action_name]
        if not request.user.has_perm_code(permission):
            raise BusinessError(
                "Bu amal uchun ruxsat yo'q.",
                code="forbidden",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        queryset = Product.all_objects.filter(pk__in=ids, is_deleted=False)
        affected = handler(queryset)

        log_action(
            actor=request.user,
            action=f"bulk_{action_name}",
            target_label=f"{affected} ta e'lon",
            changes={"ids": [str(i) for i in ids[:BULK_LIMIT]]},
            request=request,
        )
        return Response({"affected": affected, "action": action_name})

    # `update` ishlatiladi: 100 ta obyektni birma-bir saqlash
    # 100 ta so'rov bo'lardi.
    @staticmethod
    def _bulk_feature(queryset):
        return queryset.update(is_featured=True, updated_at=timezone.now())

    @staticmethod
    def _bulk_unfeature(queryset):
        return queryset.update(
            is_featured=False, featured_until=None, updated_at=timezone.now()
        )

    @staticmethod
    def _bulk_archive(queryset):
        # Arxivdagi e'lon qayta arxivlanmaydi — hisob noto'g'ri chiqmasin.
        return queryset.exclude(status=ProductStatus.ARCHIVED).update(
            status=ProductStatus.ARCHIVED, updated_at=timezone.now()
        )

    @staticmethod
    def _bulk_delete(queryset):
        return queryset.update(is_deleted=True, deleted_at=timezone.now())
