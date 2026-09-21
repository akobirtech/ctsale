"""Admin panel uchun API.

Bu yerda faqat admin panelga xos jamlanmalar bor. Mahsulot,
moderatsiya va shikoyatlar o'z ilovalaridagi endpointlar orqali
boshqariladi — bir xil logika ikki joyda yozilmasin.
"""

from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.analytics.models import AuditLog
from apps.core.exceptions import BusinessError
from apps.interactions.models import Report, ReportStatus
from apps.moderation.models import ModerationStatus, ModerationTask
from apps.products.models import Product, ProductStatus
from apps.rbac.constants import P
from apps.rbac.models import Role, UserRole
from apps.rbac.permissions import IsStaff, require
from apps.telegrambot.models import TelegramPost, TelegramPostStatus

from .serializers import AdminUserSerializer, AuditLogSerializer, TelegramPostSerializer

# Grafiklar uchun standart oraliq.
DEFAULT_CHART_DAYS = 30


class DashboardViewSet(viewsets.GenericViewSet):
    """Bosh sahifa ko'rsatkichlari."""

    permission_classes = [IsAuthenticated, IsStaff]

    @action(detail=False, methods=["get"])
    def stats(self, request):
        now = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)

        products = Product.objects.aggregate(
            total=Count("id"),
            approved=Count("id", filter=Q(status=ProductStatus.APPROVED)),
            pending=Count("id", filter=Q(status=ProductStatus.PENDING)),
            sold=Count("id", filter=Q(status=ProductStatus.SOLD)),
            rejected=Count("id", filter=Q(status=ProductStatus.REJECTED)),
            draft=Count("id", filter=Q(status=ProductStatus.DRAFT)),
            new_week=Count("id", filter=Q(created_at__gte=week_ago)),
            views=Sum("views_count"),
            favorites=Sum("favorites_count"),
            phone_reveals=Sum("phone_reveals_count"),
        )

        # `sellers` mahsulotlar bilan JOIN talab qiladi va bu qolgan
        # hisoblarni ko'paytirib yuboradi (har bir user o'z e'lonlari
        # soniga ko'ra takrorlanadi), shuning uchun hammasi `distinct`.
        users = User.objects.aggregate(
            total=Count("id", distinct=True),
            verified=Count("id", filter=Q(is_phone_verified=True), distinct=True),
            sellers=Count("id", filter=Q(products__isnull=False), distinct=True),
            verified_sellers=Count("id", filter=Q(is_verified_seller=True), distinct=True),
            new_week=Count("id", filter=Q(created_at__gte=week_ago), distinct=True),
            banned=Count("id", filter=Q(is_banned=True), distinct=True),
        )

        moderation = ModerationTask.objects.aggregate(
            pending=Count("id", filter=Q(status=ModerationStatus.PENDING)),
            in_review=Count("id", filter=Q(status=ModerationStatus.IN_REVIEW)),
            approved_today=Count(
                "id", filter=Q(status=ModerationStatus.APPROVED, reviewed_at__date=today)
            ),
            rejected_today=Count(
                "id", filter=Q(status=ModerationStatus.REJECTED, reviewed_at__date=today)
            ),
        )

        telegram = TelegramPost.objects.aggregate(
            published=Count("id", filter=Q(status=TelegramPostStatus.PUBLISHED)),
            failed=Count("id", filter=Q(status=TelegramPostStatus.FAILED)),
            pending=Count("id", filter=Q(status=TelegramPostStatus.PENDING)),
        )

        reports = Report.objects.aggregate(
            new=Count("id", filter=Q(status=ReportStatus.NEW)),
            total=Count("id"),
        )

        return Response(
            {
                "products": {k: v or 0 for k, v in products.items()},
                "users": {k: v or 0 for k, v in users.items()},
                "moderation": moderation,
                "telegram": telegram,
                "reports": reports,
                "generated_at": now,
            }
        )

    @action(detail=False, methods=["get"])
    def chart(self, request):
        """Kunlik e'lon va foydalanuvchi dinamikasi.

        Bo'sh kunlar ham nol bilan qaytariladi — aks holda grafik
        uzilib qoladi.
        """
        try:
            days = min(max(int(request.query_params.get("days", DEFAULT_CHART_DAYS)), 7), 90)
        except (TypeError, ValueError):
            days = DEFAULT_CHART_DAYS

        start = timezone.now().date() - timedelta(days=days - 1)

        def daily_counts(queryset, field="created_at"):
            rows = (
                queryset.filter(**{f"{field}__date__gte": start})
                .annotate(day=TruncDate(field))
                .values("day")
                .annotate(total=Count("id"))
            )
            return {row["day"]: row["total"] for row in rows}

        product_days = daily_counts(Product.objects.all())
        user_days = daily_counts(User.objects.all())
        approved_days = daily_counts(
            Product.objects.filter(status=ProductStatus.APPROVED), "published_at"
        )

        series = []
        for offset in range(days):
            day = start + timedelta(days=offset)
            series.append(
                {
                    "date": day.isoformat(),
                    "products": product_days.get(day, 0),
                    "users": user_days.get(day, 0),
                    "approved": approved_days.get(day, 0),
                }
            )
        return Response({"days": days, "series": series})


class AdminUserViewSet(viewsets.GenericViewSet):
    """Foydalanuvchilarni boshqarish."""

    serializer_class = AdminUserSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated(), require(P.USER_VIEW)()]
        if self.action in ("ban", "unban"):
            return [IsAuthenticated(), require(P.USER_BAN)()]
        if self.action == "verify_seller":
            return [IsAuthenticated(), require(P.USER_VERIFY_SELLER)()]
        return [IsAuthenticated(), require(P.USER_CHANGE_ROLE)()]

    def get_queryset(self):
        queryset = User.objects.prefetch_related("roles__role").annotate(
            products_total=Count("products", distinct=True)
        )

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(phone__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
            )

        role = self.request.query_params.get("role")
        if role:
            queryset = queryset.filter(roles__role__code=role)

        if self.request.query_params.get("banned") == "true":
            queryset = queryset.filter(is_banned=True)

        return queryset.order_by("-created_at")

    def list(self, request):
        page = self.paginate_queryset(self.get_queryset())
        return self.get_paginated_response(
            AdminUserSerializer(page, many=True, context={"request": request}).data
        )

    def _get_user(self, pk):
        user = User.objects.filter(pk=pk).first()
        if user is None:
            raise BusinessError(
                "Foydalanuvchi topilmadi.", code="not_found", status_code=status.HTTP_404_NOT_FOUND
            )
        return user

    @action(detail=True, methods=["post"])
    def ban(self, request, pk=None):
        user = self._get_user(pk)

        # Superuser'ni bloklash tizimga kirishni butunlay yo'qotishi mumkin.
        if user.is_superuser:
            raise BusinessError(
                "Bosh administratorni bloklab bo'lmaydi.", code="cannot_ban_superuser"
            )
        if user.id == request.user.id:
            raise BusinessError("O'zingizni bloklay olmaysiz.", code="cannot_ban_self")

        reason = (request.data.get("reason") or "").strip()
        if not reason:
            raise BusinessError("Blok sababini ko'rsating.", code="reason_required")

        days = request.data.get("days")
        user.is_banned = True
        user.ban_reason = reason[:1000]
        user.banned_until = (
            timezone.now() + timedelta(days=int(days)) if days else None
        )
        user.save(update_fields=["is_banned", "ban_reason", "banned_until", "updated_at"])

        from apps.analytics.services import log_action
        from apps.notifications.services import notify

        log_action(
            actor=request.user, action="ban", target=user,
            target_label=str(user), note=reason, request=request,
        )
        notify(
            user, "account_banned", title="Hisobingiz bloklandi",
            body=f"Sabab: {reason}",
        )
        return Response({"detail": "Foydalanuvchi bloklandi."})

    @action(detail=True, methods=["post"])
    def unban(self, request, pk=None):
        user = self._get_user(pk)
        user.is_banned = False
        user.ban_reason = ""
        user.banned_until = None
        user.save(update_fields=["is_banned", "ban_reason", "banned_until", "updated_at"])

        from apps.analytics.services import log_action

        log_action(
            actor=request.user, action="unban", target=user,
            target_label=str(user), request=request,
        )
        return Response({"detail": "Blok olib tashlandi."})

    @action(detail=True, methods=["post"], url_path="verify-seller")
    def verify_seller(self, request, pk=None):
        user = self._get_user(pk)
        user.is_verified_seller = not user.is_verified_seller
        user.save(update_fields=["is_verified_seller", "updated_at"])

        from apps.analytics.services import log_action
        from apps.notifications.services import notify

        log_action(
            actor=request.user, action="update", target=user, target_label=str(user),
            note=f"is_verified_seller={user.is_verified_seller}", request=request,
        )
        if user.is_verified_seller:
            notify(
                user, "seller_verified", title="Siz tasdiqlangan sotuvchisiz",
                body="E'lonlaringiz yonida tasdiq belgisi ko'rinadi.",
            )
        return Response({"is_verified_seller": user.is_verified_seller})

    @action(detail=True, methods=["post"], url_path="roles")
    def set_roles(self, request, pk=None):
        user = self._get_user(pk)
        codes = request.data.get("roles") or []

        if user.is_superuser and request.user.id != user.id:
            raise BusinessError(
                "Bosh administrator rollarini o'zgartirib bo'lmaydi.", code="cannot_edit_superuser"
            )

        roles = list(Role.objects.filter(code__in=codes))
        found = {role.code for role in roles}
        unknown = set(codes) - found
        if unknown:
            raise BusinessError(
                f"Noma'lum rol: {', '.join(sorted(unknown))}", code="unknown_role"
            )

        UserRole.objects.filter(user=user).delete()
        for role in roles:
            UserRole.objects.create(user=user, role=role, assigned_by=request.user)

        user.is_staff = any(role.is_staff_role for role in roles)
        user.save(update_fields=["is_staff", "updated_at"])

        from apps.analytics.services import log_action

        log_action(
            actor=request.user, action="role_change", target=user,
            target_label=str(user), note=", ".join(sorted(found)), request=request,
        )
        return Response({"roles": sorted(found), "is_staff": user.is_staff})

    @action(detail=False, methods=["get"], url_path="roles")
    def available_roles(self, request):
        return Response(
            [
                {
                    "code": role.code,
                    "name": role.name,
                    "description": role.description,
                    "is_staff_role": role.is_staff_role,
                    "permissions": role.permissions.count(),
                }
                for role in Role.objects.order_by("order")
            ]
        )


class AuditLogViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, require(P.AUDIT_VIEW)]
    serializer_class = AuditLogSerializer

    def list(self, request):
        queryset = AuditLog.objects.select_related("actor").order_by("-created_at")

        action_filter = request.query_params.get("action")
        if action_filter:
            queryset = queryset.filter(action__in=action_filter.split(","))

        actor = request.query_params.get("actor")
        if actor:
            queryset = queryset.filter(actor_id=actor)

        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(AuditLogSerializer(page, many=True).data)


class TelegramAdminViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, require(P.TELEGRAM_MANAGE)]
    serializer_class = TelegramPostSerializer

    def list(self, request):
        queryset = TelegramPost.objects.select_related("product").order_by("-created_at")

        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status__in=status_filter.split(","))

        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(TelegramPostSerializer(page, many=True).data)

    @action(detail=False, methods=["get", "patch"])
    def settings(self, request):
        from apps.telegrambot.models import TelegramSettings
        from apps.telegrambot.services import resolve_channel_id

        from .serializers import TelegramSettingsSerializer

        config = TelegramSettings.load()

        if request.method == "PATCH":
            serializer = TelegramSettingsSerializer(config, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            from apps.analytics.services import log_action

            log_action(
                actor=request.user, action="settings_change", target=config,
                target_label="Telegram sozlamalari", request=request,
            )
        else:
            serializer = TelegramSettingsSerializer(config)

        data = dict(serializer.data)
        # Token hech qachon javobga chiqmaydi — faqat sozlangani ma'lum qilinadi.
        data["is_configured"] = bool(resolve_channel_id(config))
        return Response(data)

    @action(detail=True, methods=["post"])
    def republish(self, request, pk=None):
        post = TelegramPost.objects.filter(pk=pk).select_related("product").first()
        if post is None:
            raise BusinessError(
                "Post topilmadi.", code="not_found", status_code=status.HTTP_404_NOT_FOUND
            )

        from apps.telegrambot.tasks import publish_product_to_telegram

        publish_product_to_telegram.delay(str(post.product_id))

        from apps.analytics.services import log_action

        log_action(
            actor=request.user, action="telegram_publish", target=post.product,
            target_label=post.product.title, note="Qo'lda qayta yuborildi", request=request,
        )
        return Response({"detail": "Qayta yuborish navbatga qo'yildi."})
