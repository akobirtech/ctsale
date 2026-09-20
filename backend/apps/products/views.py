"""Mahsulot endpointlari.

Ommaviy o'qish (katalog, sahifa, qidiruv) autentifikatsiyasiz —
SEO va mehmonlar uchun. Yozish faqat egasi yoki ruxsati borga.
"""

import hashlib
import logging

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramSimilarity
from django.db.models import F, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.catalog.models import Category
from apps.core.exceptions import BusinessError
from apps.core.utils import get_client_ip
from apps.rbac.constants import P
from apps.rbac.permissions import IsNotBanned, IsPhoneVerified, user_has_permission

from . import services
from .filters import (
    DEFAULT_SORT,
    SORT_OPTIONS,
    ProductFilter,
    apply_sort,
    apply_spec_filters,
    build_facets,
)
from .models import Product, ProductStatus, PUBLIC_STATUSES, SearchQueryLog
from .serializers import (
    ProductCardSerializer,
    ProductDetailSerializer,
    ProductStatusActionSerializer,
    ProductWriteSerializer,
)

logger = logging.getLogger(__name__)

# Bir xil IP/foydalanuvchi shu muddat ichida ko'rishni takrorlasa
# hisoblanmaydi.
VIEW_DEDUPE_HOURS = 24
MIN_SEARCH_LENGTH = 2


def _hash_ip(ip):
    """IP ochiq saqlanmaydi — faqat takrorni aniqlash uchun hash."""
    salt = settings.SECRET_KEY[:16]
    return hashlib.sha256(f"{salt}{ip}".encode()).hexdigest()


class ProductViewSet(viewsets.ModelViewSet):
    lookup_field = "slug"
    filterset_class = ProductFilter

    public_actions = (
        "list", "retrieve", "search", "autocomplete", "similar", "featured",
    )

    # ------------------------------------------------------------------
    def get_permissions(self):
        if self.action in self.public_actions:
            return [AllowAny()]
        if self.action == "create":
            return [IsAuthenticated(), IsNotBanned(), IsPhoneVerified()]
        return [IsAuthenticated(), IsNotBanned()]

    def get_throttles(self):
        if self.action == "create":
            self.throttle_scope = "product_create"
            return [ScopedRateThrottle()]
        if self.action in ("search", "autocomplete"):
            self.throttle_scope = "search"
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProductWriteSerializer
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductCardSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["lang"] = self._language()
        context["favorited_ids"] = self._favorited_ids()
        return context

    def _language(self):
        lang = self.request.query_params.get("lang")
        return lang if lang in settings.SUPPORTED_LANGUAGES else settings.DEFAULT_LANGUAGE

    def _favorited_ids(self):
        """Ro'yxatdagi qaysi mahsulot sevimlida — bitta so'rovda.

        Har karta uchun alohida so'rov yuborish N+1 muammosini
        keltirib chiqarardi.
        """
        user = self.request.user
        if not user.is_authenticated:
            return set()
        from apps.interactions.models import Favorite

        return set(
            Favorite.objects.filter(user=user).values_list("product_id", flat=True)
        )

    # ------------------------------------------------------------------
    def get_queryset(self):
        user = self.request.user
        base = Product.objects.with_relations()

        if self.action in self.public_actions:
            queryset = base.filter(status__in=PUBLIC_STATUSES)
            # Sotilganlar standart ro'yxatda ko'rinmaydi, lekin
            # sahifasi ochiq qoladi (SEO qiymati saqlanadi).
            if self.action in ("list", "search", "featured"):
                if self.request.query_params.get("include_sold") != "true":
                    queryset = queryset.exclude(status=ProductStatus.SOLD)
            return queryset

        if user.is_authenticated and user_has_permission(user, P.PRODUCT_VIEW_ANY):
            return base

        if user.is_authenticated:
            return base.filter(seller=user)

        return base.none()

    # ------------------------------------------------------------------
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        category = None
        category_slug = request.query_params.get("category")
        if category_slug:
            category = Category.objects.filter(slug=category_slug, is_active=True).first()

        queryset = apply_spec_filters(queryset, request.query_params, category)
        queryset = apply_sort(queryset, request.query_params.get("sort"))

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        response = self.get_paginated_response(serializer.data)

        if request.query_params.get("facets") == "true":
            response.data["facets"] = build_facets(queryset, category)
        response.data["sort_options"] = list(SORT_OPTIONS)
        response.data["applied_sort"] = request.query_params.get("sort") or DEFAULT_SORT
        return response

    def retrieve(self, request, *args, **kwargs):
        product = self.get_object()

        # O'chirilgan e'lon: 410 Gone — qidiruv tizimlari uni
        # indeksdan chiqarsin (404 dan ko'ra aniqroq signal).
        if product.is_deleted:
            return Response(
                {
                    "error": {
                        "code": "gone",
                        "message": "Bu e'lon o'chirilgan.",
                        "details": {},
                    }
                },
                status=status.HTTP_410_GONE,
            )

        self._register_view(product, request)
        serializer = self.get_serializer(product)
        return Response(serializer.data)

    def get_object(self):
        """Slug o'zgargan bo'lsa eski slug ham topilsin (301 uchun)."""
        slug = self.kwargs.get(self.lookup_field)
        queryset = self.get_queryset()

        product = queryset.filter(slug=slug).first()
        if product is not None:
            self.check_object_permissions(self.request, product)
            return product

        # Eski slug — yangisiga yo'naltirish frontend vazifasi,
        # lekin ma'lumotni baribir beramiz.
        moved = queryset.filter(previous_slugs__contains=[slug]).first()
        if moved is not None:
            self.check_object_permissions(self.request, moved)
            return moved

        from django.http import Http404

        raise Http404

    def _register_view(self, product, request):
        """Ko'rishni hisoblash — 24 soat ichida takrorlanmaydi."""
        from apps.interactions.models import ProductView

        ip_hash = _hash_ip(get_client_ip(request))
        since = timezone.now() - timezone.timedelta(hours=VIEW_DEDUPE_HOURS)

        already = ProductView.objects.filter(
            product=product, ip_hash=ip_hash, created_at__gte=since
        ).exists()
        if already:
            return

        ProductView.objects.create(
            product=product,
            user=request.user if request.user.is_authenticated else None,
            ip_hash=ip_hash,
            referrer=request.META.get("HTTP_REFERER", "")[:255],
        )
        Product.all_objects.filter(pk=product.pk).update(
            views_count=F("views_count") + 1
        )
        product.views_count += 1

    # ------------------------------------------------------------------
    def create(self, request, *args, **kwargs):
        """Yaratgandan keyin to'liq obyektni qaytaramiz.

        Frontendga darhol `slug` kerak bo'ladi (rasm yuklash va
        sahifaga o'tish uchun), yozish serializeri esa uni bermaydi.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        detail = ProductDetailSerializer(
            serializer.instance, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(serializer.data)
        return Response(detail.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        detail = ProductDetailSerializer(
            serializer.instance, context=self.get_serializer_context()
        )
        return Response(detail.data)

    def perform_create(self, serializer):
        product = serializer.save(
            seller=self.request.user,
            status=ProductStatus.DRAFT,
            created_by=self.request.user,
        )
        services.build_seo_metadata(product)
        product.save()
        services.update_search_vector(product)

    def perform_update(self, serializer):
        instance = serializer.instance
        before = {
            field: getattr(instance, field) for field in services.MODERATION_SENSITIVE_FIELDS
        }

        product = serializer.save(updated_by=self.request.user)
        services.build_seo_metadata(product)
        product.save()
        services.update_search_vector(product)

        changed = [
            field
            for field in services.MODERATION_SENSITIVE_FIELDS
            if before[field] != getattr(product, field)
        ]
        if services.needs_remoderation(product, changed):
            services.submit_for_moderation(product, actor=self.request.user)

    def perform_destroy(self, instance):
        if not self._can_modify(instance):
            raise BusinessError(
                "Bu e'lonni o'chirishga ruxsatingiz yo'q.",
                code="permission_denied",
                status_code=403,
            )
        instance.delete()  # soft delete
        from apps.analytics.services import log_action

        log_action(
            actor=self.request.user,
            action="delete",
            target=instance,
            target_label=instance.title,
            request=self.request,
        )

    def _can_modify(self, product):
        user = self.request.user
        if product.seller_id == user.id:
            return True
        return user_has_permission(user, P.PRODUCT_EDIT_ANY)

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if self.action in self.public_actions:
            return
        if not self._can_modify(obj):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Bu e'lon sizga tegishli emas.")

    # ------------------------------------------------------------------
    # Sotuvchi amallari
    # ------------------------------------------------------------------
    @action(detail=True, methods=["post"])
    def submit(self, request, slug=None):
        product = self.get_object()
        services.submit_for_moderation(product, actor=request.user)
        return Response(ProductDetailSerializer(product, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"], url_path="mark-sold")
    def mark_sold(self, request, slug=None):
        product = self.get_object()
        services.mark_as_sold(product, actor=request.user)
        return Response({"detail": "E'lon sotilgan deb belgilandi.", "status": product.status})

    @action(detail=True, methods=["post"])
    def renew(self, request, slug=None):
        product = self.get_object()
        services.renew_product(product, actor=request.user)
        return Response(
            {"detail": "E'lon muddati uzaytirildi.", "expires_at": product.expires_at}
        )

    @action(detail=True, methods=["post"])
    def status(self, request, slug=None):
        product = self.get_object()
        serializer = ProductStatusActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        force = user_has_permission(request.user, P.PRODUCT_FORCE_STATUS)

        # Sotuvchi o'z e'lonini o'zi tasdiqlay olmaydi.
        if new_status in (ProductStatus.APPROVED, ProductStatus.REJECTED) and not force:
            raise BusinessError(
                "Bu holatga o'tkazish moderator vazifasi.",
                code="moderation_required",
                status_code=403,
            )

        services.change_status(product, new_status, actor=request.user, force=force)
        return Response({"detail": "Holat o'zgartirildi.", "status": product.status})

    @action(detail=False, methods=["get"], url_path="my")
    def my_products(self, request):
        queryset = Product.objects.with_relations().filter(seller=request.user)

        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status__in=status_filter.split(","))

        queryset = queryset.order_by("-created_at")
        page = self.paginate_queryset(queryset)
        serializer = ProductCardSerializer(
            page, many=True, context=self.get_serializer_context()
        )
        return self.get_paginated_response(serializer.data)

    # ------------------------------------------------------------------
    # Ommaviy
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"])
    def search(self, request):
        """Full-text qidiruv, opechatkaga chidamli."""
        query = (request.query_params.get("q") or "").strip()
        if len(query) < MIN_SEARCH_LENGTH:
            raise BusinessError(
                f"Qidiruv so'zi kamida {MIN_SEARCH_LENGTH} ta belgidan iborat bo'lsin.",
                code="query_too_short",
            )

        queryset = self.filter_queryset(self.get_queryset())
        queryset = self._apply_search(queryset, query)

        category = None
        category_slug = request.query_params.get("category")
        if category_slug:
            category = Category.objects.filter(slug=category_slug, is_active=True).first()
        queryset = apply_spec_filters(queryset, request.query_params, category)

        sort = request.query_params.get("sort")
        if sort:
            queryset = apply_sort(queryset, sort)

        page = self.paginate_queryset(queryset)
        serializer = ProductCardSerializer(
            page, many=True, context=self.get_serializer_context()
        )
        response = self.get_paginated_response(serializer.data)
        response.data["query"] = query

        total = response.data.get("count", 0)
        SearchQueryLog.objects.create(
            query=query[:200],
            results_count=total,
            user=request.user if request.user.is_authenticated else None,
        )

        if total == 0:
            response.data["suggestions"] = self._suggestions(query)
        return response

    def _apply_search(self, queryset, query):
        """Avval full-text, natija bo'lmasa trigram (opechatka uchun)."""
        search_query = SearchQuery(query, config="simple")
        ranked = (
            queryset.filter(search_vector=search_query)
            .annotate(rank=SearchRank(F("search_vector"), search_query))
            .order_by("-is_featured", "-rank", "-published_at")
        )
        if ranked.exists():
            return ranked

        return (
            queryset.annotate(similarity=TrigramSimilarity("title", query))
            .filter(
                Q(similarity__gt=0.2)
                | Q(title__icontains=query)
                | Q(model_name__icontains=query)
            )
            .order_by("-is_featured", "-similarity", "-published_at")
        )

    def _suggestions(self, query):
        """Natija bo'lmaganda yaqin so'rovlarni taklif qilamiz."""
        similar = (
            Product.objects.public()
            .annotate(similarity=TrigramSimilarity("title", query))
            .filter(similarity__gt=0.15)
            .order_by("-similarity")
            .values_list("title", flat=True)[:5]
        )
        return list(similar)

    @action(detail=False, methods=["get"])
    def autocomplete(self, request):
        query = (request.query_params.get("q") or "").strip()
        if len(query) < MIN_SEARCH_LENGTH:
            return Response({"results": []})

        titles = (
            self.get_queryset()
            .filter(Q(title__istartswith=query) | Q(title__icontains=query))
            .order_by("-views_count")
            .values("title", "slug")[:8]
        )
        categories = (
            Category.objects.filter(is_active=True, name_uz__icontains=query)
            .values("name_uz", "slug")[:4]
        )
        return Response(
            {
                "products": list(titles),
                "categories": [
                    {"title": c["name_uz"], "slug": c["slug"]} for c in categories
                ],
            }
        )

    @action(detail=True, methods=["get"])
    def similar(self, request, slug=None):
        """O'xshash mahsulotlar: bir kategoriya, yaqin narx."""
        product = self.get_object()
        queryset = (
            Product.objects.with_relations()
            .active()
            .filter(category_id=product.category_id)
            .exclude(pk=product.pk)
        )

        if product.price:
            low, high = product.price * 0.6, product.price * 1.6
            nearby = queryset.filter(price__gte=low, price__lte=high)
            if nearby.count() >= 4:
                queryset = nearby

        items = queryset.order_by("-is_featured", "-views_count")[:12]
        return Response(
            ProductCardSerializer(
                items, many=True, context=self.get_serializer_context()
            ).data
        )

    @action(detail=False, methods=["get"])
    def featured(self, request):
        """Bosh sahifa bloklari: featured / new / popular / used."""
        base = Product.objects.with_relations().active()
        context = self.get_serializer_context()
        limit = min(int(request.query_params.get("limit", 12)), 24)

        def serialize(queryset):
            return ProductCardSerializer(queryset[:limit], many=True, context=context).data

        return Response(
            {
                "featured": serialize(
                    base.filter(is_featured=True).order_by("-published_at")
                ),
                "newest": serialize(base.order_by("-published_at")),
                "popular": serialize(base.order_by("-views_count", "-favorites_count")),
                "used": serialize(
                    base.exclude(condition="new").order_by("-published_at")
                ),
            }
        )

    @action(detail=True, methods=["post"], url_path="reveal-phone",
            permission_classes=[AllowAny])
    def reveal_phone(self, request, slug=None):
        """Telefon raqamni ochadi va hisoblaydi.

        Raqam ro'yxat/detal javoblarida yo'q — shu endpoint orqali,
        chegara bilan beriladi, aks holda uni ommaviy yig'ish oson
        bo'lardi.
        """
        self.throttle_scope = "phone_reveal"
        product = self.get_object()

        if not product.is_public:
            raise BusinessError(
                "Bu e'lon uchun aloqa ma'lumoti mavjud emas.", code="not_available"
            )

        from apps.interactions.models import PhoneReveal

        ip_hash = _hash_ip(get_client_ip(request))
        since = timezone.now() - timezone.timedelta(hours=VIEW_DEDUPE_HOURS)
        already = PhoneReveal.objects.filter(
            product=product, ip_hash=ip_hash, created_at__gte=since
        ).exists()

        if not already:
            PhoneReveal.objects.create(
                product=product,
                user=request.user if request.user.is_authenticated else None,
                ip_hash=ip_hash,
            )
            Product.all_objects.filter(pk=product.pk).update(
                phone_reveals_count=F("phone_reveals_count") + 1
            )

        phone = product.display_phone
        return Response(
            {
                "phone": phone,
                "name": product.contact_name or product.seller.get_full_name(),
                "telegram": product.seller.telegram_username,
            }
        )
