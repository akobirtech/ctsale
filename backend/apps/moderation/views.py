"""Moderatsiya navbati va qarorlar."""

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.exceptions import BusinessError
from apps.products import services as product_services
from apps.products.models import Product, ProductStatus
from apps.products.serializers import ProductDetailSerializer
from apps.rbac.constants import P
from apps.rbac.permissions import require, require_any, user_has_permission

from .models import ModerationStatus, ModerationTask, RejectReasonCode
from .serializers import (
    BulkApproveSerializer,
    ModerationTaskSerializer,
    RejectSerializer,
)

# Bitta so'rovda tasdiqlanishi mumkin bo'lgan eng ko'p e'lon — xato
# bosilgan tugma yuzlab e'lonni bir zumda chiqarib yubormasligi uchun.
MAX_BULK_APPROVE = 50


class ModerationViewSet(viewsets.ReadOnlyModelViewSet):
    """Moderatorlar uchun navbat.

    `/api/v1/moderation/queue/` — kutayotgan e'lonlar
    `/api/v1/moderation/{id}/approve|reject/` — qaror
    """

    serializer_class = ModerationTaskSerializer
    permission_classes = [
        IsAuthenticated,
        require_any(P.PRODUCT_APPROVE, P.PRODUCT_REJECT, P.PRODUCT_VIEW_ANY),
    ]

    def get_queryset(self):
        queryset = ModerationTask.objects.select_related(
            "product", "product__seller", "product__category", "product__brand",
            "product__region", "assignee",
        ).prefetch_related("product__images")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status__in=status_filter.split(","))

        assignee = self.request.query_params.get("assignee")
        if assignee == "me":
            queryset = queryset.filter(assignee=self.request.user)
        elif assignee == "none":
            queryset = queryset.filter(assignee__isnull=True)

        return queryset.order_by("-created_at")

    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"])
    def queue(self, request):
        """Ko'rib chiqilmagan e'lonlar — eng eskisi birinchi.

        Navbat FIFO: sotuvchi kutish vaqti taxmin qilinadigan bo'lsin.
        """
        queryset = (
            self.get_queryset()
            .filter(
                status__in=[ModerationStatus.PENDING, ModerationStatus.IN_REVIEW],
                product__status=ProductStatus.PENDING,
            )
            .order_by("created_at")
        )
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        counts = ModerationTask.objects.aggregate(
            pending=Count("id", filter=Q(status=ModerationStatus.PENDING)),
            in_review=Count("id", filter=Q(status=ModerationStatus.IN_REVIEW)),
            approved=Count("id", filter=Q(status=ModerationStatus.APPROVED)),
            rejected=Count("id", filter=Q(status=ModerationStatus.REJECTED)),
        )
        counts["reject_reasons"] = [
            {"value": value, "label": label} for value, label in RejectReasonCode.choices
        ]
        return Response(counts)

    @action(detail=True, methods=["get"])
    def preview(self, request, pk=None):
        """Moderator ko'rish uchun mahsulotning to'liq ko'rinishi."""
        task = self.get_object()
        serializer = ProductDetailSerializer(
            task.product, context={"request": request, "lang": "uz"}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def claim(self, request, pk=None):
        """Vazifani o'ziga biriktiradi — ikki moderator bitta e'lonni
        bir vaqtda ko'rib chiqmasligi uchun."""
        task = self.get_object()

        if task.assignee_id and task.assignee_id != request.user.id:
            raise BusinessError(
                f"Bu e'lonni {task.assignee.get_full_name()} ko'rib chiqmoqda.",
                code="already_claimed",
                status_code=status.HTTP_409_CONFLICT,
            )

        task.assignee = request.user
        task.status = ModerationStatus.IN_REVIEW
        task.save(update_fields=["assignee", "status", "updated_at"])
        return Response(self.get_serializer(task).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, require(P.PRODUCT_APPROVE)])
    def approve(self, request, pk=None):
        task = self.get_object()
        product = task.product

        if product.status != ProductStatus.PENDING:
            raise BusinessError(
                f"E'lon «{product.get_status_display()}» holatida — tasdiqlash mumkin emas.",
                code="invalid_state",
            )

        product_services.approve_product(
            product, actor=request.user, note=request.data.get("note", "")
        )
        task.refresh_from_db()
        return Response(
            {
                "detail": "E'lon tasdiqlandi va Telegram kanalga yuborildi.",
                "task": self.get_serializer(task).data,
            }
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, require(P.PRODUCT_REJECT)])
    def reject(self, request, pk=None):
        task = self.get_object()
        product = task.product

        serializer = RejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if product.status != ProductStatus.PENDING:
            raise BusinessError(
                f"E'lon «{product.get_status_display()}» holatida — rad etish mumkin emas.",
                code="invalid_state",
            )

        product_services.reject_product(
            product,
            actor=request.user,
            reason_code=serializer.validated_data["reason_code"],
            comment=serializer.validated_data.get("comment", ""),
            internal_note=serializer.validated_data.get("internal_note", ""),
        )
        task.refresh_from_db()
        return Response(
            {
                "detail": "E'lon rad etildi, sotuvchiga xabar yuborildi.",
                "task": self.get_serializer(task).data,
            }
        )

    @action(detail=False, methods=["post"], url_path="bulk-approve",
            permission_classes=[IsAuthenticated, require(P.PRODUCT_APPROVE)])
    def bulk_approve(self, request):
        serializer = BulkApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task_ids = serializer.validated_data["task_ids"][:MAX_BULK_APPROVE]

        tasks = ModerationTask.objects.filter(
            id__in=task_ids, product__status=ProductStatus.PENDING
        ).select_related("product")

        approved, failed = [], []
        for task in tasks:
            try:
                product_services.approve_product(task.product, actor=request.user)
                approved.append(task.id)
            except Exception as exc:
                # Bitta e'londagi muammo qolganlarini to'xtatmasin.
                failed.append({"task_id": task.id, "error": str(exc)})

        return Response(
            {
                "approved": approved,
                "approved_count": len(approved),
                "failed": failed,
                "detail": f"{len(approved)} ta e'lon tasdiqlandi.",
            }
        )
