"""Media yuklash endpointlari.

Barcha yo'llar mahsulotga bog'langan: `/products/{slug}/images/`.
Shu sababli egalik tekshiruvi bitta joyda bo'ladi.
"""

import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.core.exceptions import BusinessError
from apps.products.models import Product
from apps.rbac.constants import P
from apps.rbac.permissions import IsNotBanned, user_has_permission

from .models import ProductImage, ProductVideo
from .serializers import (
    ImageReorderSerializer,
    ProductImageSerializer,
    ProductVideoSerializer,
)
from .tasks import cleanup_product_media, process_product_image
from .validators import (
    check_image_limit,
    check_video_limit,
    validate_image,
    validate_video,
)

logger = logging.getLogger(__name__)


class ProductMediaMixin:
    permission_classes = [IsAuthenticated, IsNotBanned]
    # Fayl yuklash uchun multipart, tartiblash kabi amallar uchun JSON.
    # JSONParser'siz `reorder` 415 qaytarardi.
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    throttle_scope = "media_upload"

    def get_throttles(self):
        if self.request.method == "POST":
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_product(self):
        slug = self.kwargs.get("product_slug")
        product = Product.objects.filter(slug=slug).first()
        if product is None:
            from django.http import Http404

            raise Http404

        user = self.request.user
        if product.seller_id != user.id and not user_has_permission(
            user, P.PRODUCT_EDIT_ANY
        ):
            raise BusinessError(
                "Bu e'lonning media fayllarini boshqarishga ruxsatingiz yo'q.",
                code="permission_denied",
                status_code=403,
            )
        return product

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class ProductImageViewSet(ProductMediaMixin, viewsets.ModelViewSet):
    serializer_class = ProductImageSerializer
    pagination_class = None

    def get_queryset(self):
        return ProductImage.objects.filter(product=self.get_product()).order_by(
            "order", "created_at"
        )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Bir yoki bir nechta rasm yuklash.

        Fayllar `images` kaliti bilan yuboriladi (bir nechta bo'lishi
        mumkin). Bittasi noto'g'ri bo'lsa butun so'rov rad etiladi —
        shunda foydalanuvchi qaysi fayl muammoli ekanini biladi.
        """
        product = self.get_product()
        files = request.FILES.getlist("images") or request.FILES.getlist("image")
        if not files:
            raise BusinessError("Rasm fayli yuborilmadi.", code="no_file")

        try:
            remaining = check_image_limit(product)
        except DjangoValidationError as exc:
            raise BusinessError(exc.messages[0], code="limit_exceeded") from exc

        if len(files) > remaining:
            raise BusinessError(
                f"Yana {remaining} ta rasm qo'shish mumkin, siz {len(files)} ta yubordingiz.",
                code="limit_exceeded",
            )

        metadata = []
        for uploaded in files:
            try:
                metadata.append(validate_image(uploaded))
            except DjangoValidationError as exc:
                raise BusinessError(
                    f"«{uploaded.name}»: {exc.messages[0]}",
                    code="invalid_image",
                    status_code=status.HTTP_400_BAD_REQUEST,
                ) from exc

        has_primary = product.images.filter(is_primary=True).exists()
        last_order = product.images.count()
        created = []

        for index, (uploaded, info) in enumerate(zip(files, metadata)):
            image = ProductImage.objects.create(
                product=product,
                image=uploaded,
                alt_text=product.title[:200],
                is_primary=not has_primary and index == 0,
                order=last_order + index,
                width=info["width"],
                height=info["height"],
                file_size=uploaded.size,
            )
            created.append(image)
            transaction.on_commit(
                lambda image_id=image.pk: process_product_image.delay(image_id)
            )

        serializer = self.get_serializer(created, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        paths = [
            getattr(instance, field).name
            for field in ("image", "thumb", "medium", "large")
            if getattr(instance, field)
        ]
        was_primary = instance.is_primary
        product = instance.product
        instance.delete()

        # Asosiy rasm o'chirilsa, keyingisi asosiy bo'ladi — e'lon
        # rasmsiz qolmasin.
        if was_primary:
            replacement = product.images.order_by("order", "created_at").first()
            if replacement:
                replacement.is_primary = True
                replacement.save(update_fields=["is_primary"])

        cleanup_product_media.delay(paths)

    @action(detail=True, methods=["post"], url_path="set-primary")
    def set_primary(self, request, product_slug=None, pk=None):
        image = self.get_object()
        # Unique constraint tufayli avval eskisini bo'shatamiz.
        ProductImage.objects.filter(product=image.product, is_primary=True).update(
            is_primary=False
        )
        image.is_primary = True
        image.save(update_fields=["is_primary"])
        return Response({"detail": "Asosiy rasm o'zgartirildi.", "id": image.pk})

    @action(detail=False, methods=["post"])
    def reorder(self, request, product_slug=None):
        product = self.get_product()
        serializer = ImageReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        images = {i.pk: i for i in product.images.all()}
        updated = []
        for item in serializer.validated_data["items"]:
            image = images.get(int(item["id"]))
            if image is None:
                continue
            image.order = int(item["order"])
            updated.append(image)

        ProductImage.objects.bulk_update(updated, ["order"])
        return Response(
            self.get_serializer(
                product.images.order_by("order", "created_at"), many=True
            ).data
        )


class ProductVideoViewSet(ProductMediaMixin, viewsets.ModelViewSet):
    serializer_class = ProductVideoSerializer
    pagination_class = None

    def get_queryset(self):
        return ProductVideo.objects.filter(product=self.get_product()).order_by(
            "order", "created_at"
        )

    def create(self, request, *args, **kwargs):
        product = self.get_product()
        uploaded = request.FILES.get("video")
        if uploaded is None:
            raise BusinessError("Video fayli yuborilmadi.", code="no_file")

        try:
            check_video_limit(product)
            info = validate_video(uploaded)
        except DjangoValidationError as exc:
            raise BusinessError(exc.messages[0], code="invalid_video") from exc

        video = ProductVideo.objects.create(
            product=product,
            video=uploaded,
            title=request.data.get("title", "")[:150],
            order=product.videos.count(),
            file_size=uploaded.size,
            mime_type=info["mime"],
            is_processed=True,
        )
        return Response(
            self.get_serializer(video).data, status=status.HTTP_201_CREATED
        )

    def perform_destroy(self, instance):
        paths = [
            getattr(instance, field).name
            for field in ("video", "poster")
            if getattr(instance, field)
        ]
        instance.delete()
        cleanup_product_media.delay(paths)
