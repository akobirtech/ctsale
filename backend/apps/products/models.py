"""Mahsulot (e'lon) modeli va uning holat mashinasi."""

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import AuditableModel, BaseModel
from apps.core.utils import make_unique_slug


class ProductStatus(models.TextChoices):
    DRAFT = "draft", "Qoralama"
    PENDING = "pending", "Moderatsiyada"
    APPROVED = "approved", "Tasdiqlangan"
    REJECTED = "rejected", "Rad etilgan"
    RESERVED = "reserved", "Band qilingan"
    SOLD = "sold", "Sotilgan"
    EXPIRED = "expired", "Muddati tugagan"
    ARCHIVED = "archived", "Arxivlangan"


# Ruxsat etilgan holat o'tishlari. Bu yerda yo'q o'tish rad etiladi —
# shu sababli "sotilgan" e'lon to'g'ridan-to'g'ri "qoralama" ga qayta olmaydi.
STATUS_TRANSITIONS = {
    ProductStatus.DRAFT: {ProductStatus.PENDING, ProductStatus.ARCHIVED},
    ProductStatus.PENDING: {
        ProductStatus.APPROVED,
        ProductStatus.REJECTED,
        ProductStatus.DRAFT,
        ProductStatus.ARCHIVED,
    },
    ProductStatus.APPROVED: {
        ProductStatus.RESERVED,
        ProductStatus.SOLD,
        ProductStatus.ARCHIVED,
        ProductStatus.EXPIRED,
        ProductStatus.PENDING,
    },
    ProductStatus.REJECTED: {ProductStatus.DRAFT, ProductStatus.PENDING, ProductStatus.ARCHIVED},
    ProductStatus.RESERVED: {ProductStatus.APPROVED, ProductStatus.SOLD, ProductStatus.ARCHIVED},
    ProductStatus.SOLD: {ProductStatus.ARCHIVED},
    ProductStatus.EXPIRED: {ProductStatus.PENDING, ProductStatus.ARCHIVED},
    ProductStatus.ARCHIVED: {ProductStatus.DRAFT, ProductStatus.PENDING},
}

# Ommaga ko'rinadigan holatlar.
PUBLIC_STATUSES = (ProductStatus.APPROVED, ProductStatus.RESERVED, ProductStatus.SOLD)


class Condition(models.TextChoices):
    NEW = "new", "Yangi"
    LIKE_NEW = "like_new", "Deyarli yangi"
    GOOD = "good", "Yaxshi holatda"
    FAIR = "fair", "O'rtacha holatda"
    FOR_PARTS = "for_parts", "Ehtiyot qismlarga"


class Currency(models.TextChoices):
    UZS = "UZS", "so'm"
    USD = "USD", "$"


class ProductQuerySet(models.QuerySet):
    def public(self):
        """Saytda ko'rinadigan e'lonlar."""
        return self.filter(status__in=PUBLIC_STATUSES, is_deleted=False)

    def active(self):
        """Sotuvga ochiq e'lonlar (sotilgan/band emas)."""
        return self.filter(status=ProductStatus.APPROVED, is_deleted=False)

    def with_relations(self):
        return self.select_related(
            "seller", "category", "brand", "region", "district"
        ).prefetch_related("images")


class ProductManager(models.Manager.from_queryset(ProductQuerySet)):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Product(BaseModel, AuditableModel):
    """E'lon.

    `seller` — kimga tegishli; `created_by`/`updated_by` — kim
    kiritgan/oxirgi tahrirlagan. Odatda ikkalasi bir xil, lekin admin
    sotuvchi nomidan tahrirlaganda farq qiladi va shu farq muhim.
    """

    # --- Asosiy ---
    title = models.CharField("sarlavha", max_length=200)
    slug = models.SlugField("slug", max_length=255, unique=True, db_index=True)
    description = models.TextField("tavsif", max_length=5000)

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="sotuvchi",
        on_delete=models.CASCADE,
        related_name="products",
    )
    category = models.ForeignKey(
        "catalog.Category",
        verbose_name="kategoriya",
        on_delete=models.PROTECT,
        related_name="products",
    )
    brand = models.ForeignKey(
        "catalog.Brand",
        verbose_name="brend",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    model_name = models.CharField("model", max_length=150, blank=True)

    # --- Narx ---
    price = models.DecimalField(
        "narx",
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(
        "valyuta", max_length=3, choices=Currency.choices, default=Currency.UZS
    )
    is_negotiable = models.BooleanField("narx kelishiladi", default=False)
    price_on_request = models.BooleanField("narx so'rov bo'yicha", default=False)
    is_exchange_possible = models.BooleanField("almashtirish mumkin", default=False)
    quantity = models.PositiveIntegerField("miqdor", default=1)

    # --- Holat ---
    condition = models.CharField("holati", max_length=20, choices=Condition.choices)
    status = models.CharField(
        "status", max_length=20, choices=ProductStatus.choices, default=ProductStatus.DRAFT
    )

    # --- Ishlatilgan mahsulot uchun (barchasi ixtiyoriy) ---
    usage_period = models.CharField(
        "foydalanish muddati", max_length=100, blank=True, help_text="Masalan: 1 yil 3 oy"
    )
    defects = models.TextField("kamchiliklar", max_length=1000, blank=True)
    repair_history = models.TextField("ta'mirlash tarixi", max_length=1000, blank=True)
    has_warranty = models.BooleanField("kafolat bor", default=False)
    warranty_until = models.DateField("kafolat muddati", null=True, blank=True)
    has_original_box = models.BooleanField("original quti bor", default=False)
    accessories = models.CharField(
        "qo'shimcha aksessuarlar", max_length=300, blank=True, help_text="Zaryadlovchi, sumka..."
    )
    purchase_date = models.DateField("sotib olingan sana", null=True, blank=True)

    # --- Xususiyatlar (dinamik) ---
    specs = models.JSONField(
        "xususiyatlar",
        default=dict,
        blank=True,
        help_text="Kalit = AttributeDefinition.code",
    )

    # --- Manzil ---
    region = models.ForeignKey(
        "catalog.Region",
        verbose_name="viloyat",
        on_delete=models.PROTECT,
        related_name="products",
    )
    district = models.ForeignKey(
        "catalog.District",
        verbose_name="tuman",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    address_note = models.CharField("manzil izohi", max_length=200, blank=True)

    # --- Aloqa ---
    contact_phone = models.CharField(
        "aloqa telefoni",
        max_length=13,
        blank=True,
        help_text="Bo'sh bo'lsa sotuvchi profilidagi raqam ishlatiladi.",
    )
    contact_name = models.CharField("aloqa uchun ism", max_length=80, blank=True)

    # --- Statistika (denormalizatsiya: har so'rovda COUNT qilmaslik uchun) ---
    views_count = models.PositiveIntegerField("ko'rishlar", default=0)
    favorites_count = models.PositiveIntegerField("sevimlilar", default=0)
    phone_reveals_count = models.PositiveIntegerField("telefon ochilishi", default=0)

    # --- Reklama / tartib ---
    is_featured = models.BooleanField("tanlangan (VIP)", default=False)
    featured_until = models.DateTimeField("VIP muddati", null=True, blank=True)

    # --- Vaqtlar ---
    published_at = models.DateTimeField("e'lon qilingan", null=True, blank=True, db_index=True)
    expires_at = models.DateTimeField("muddati tugaydi", null=True, blank=True, db_index=True)
    sold_at = models.DateTimeField("sotilgan vaqt", null=True, blank=True)
    bumped_at = models.DateTimeField(
        "ko'tarilgan vaqt",
        null=True,
        blank=True,
        help_text="E'lon uzaytirilganda yangilanadi — saralashda ishlatiladi.",
    )

    # --- Qidiruv ---
    search_vector = SearchVectorField(null=True, blank=True, editable=False)

    # --- SEO ---
    # Bo'sh qoldirilsa avtomatik generatsiya qilinadi (apps/seo/services.py).
    # Admin/sotuvchi xohlasa qo'lda yozishi mumkin — shunda avtomatik
    # generatsiya bu maydonlarni bosib o'tmaydi.
    seo_title = models.CharField("SEO title", max_length=200, blank=True)
    seo_description = models.CharField("SEO description", max_length=300, blank=True)
    seo_keywords = models.CharField("SEO keywords", max_length=300, blank=True)
    og_title = models.CharField("OG title", max_length=200, blank=True)
    og_description = models.CharField("OG description", max_length=300, blank=True)
    og_image = models.ImageField("OG rasm", upload_to="seo/products/", null=True, blank=True)

    is_indexable = models.BooleanField(
        "qidiruv tizimlari indekslasin",
        default=True,
        help_text="O'chirilsa sahifa noindex bo'ladi va sitemapga tushmaydi.",
    )
    # Slug o'zgarganda eskisi saqlanadi va /product/<eski-slug> 301 qiladi.
    previous_slugs = models.JSONField("eski sluglar", default=list, blank=True)

    objects = ProductManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = "mahsulot"
        verbose_name_plural = "mahsulotlar"
        ordering = ["-published_at", "-created_at"]
        indexes = [
            GinIndex(fields=["search_vector"], name="product_search_gin"),
            GinIndex(fields=["specs"], name="product_specs_gin", opclasses=["jsonb_path_ops"]),
            models.Index(fields=["status", "-published_at"], name="product_status_pub_idx"),
            models.Index(fields=["category", "status", "price"], name="product_cat_status_idx"),
            models.Index(fields=["seller", "status"], name="product_seller_status_idx"),
            models.Index(fields=["brand", "status"], name="product_brand_status_idx"),
            models.Index(fields=["region", "status"], name="product_region_status_idx"),
            models.Index(fields=["-is_featured", "-published_at"], name="product_featured_idx"),
            models.Index(fields=["condition", "status"], name="product_condition_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(price__gte=0) | models.Q(price__isnull=True),
                name="product_price_non_negative",
            ),
            # Narx ko'rsatilmagan bo'lsa, "so'rov bo'yicha" yoki "kelishiladi"
            # belgilangan bo'lishi kerak — aks holda xaridor hech narsa bilmaydi.
            models.CheckConstraint(
                check=models.Q(price__isnull=False)
                | models.Q(price_on_request=True)
                | models.Q(is_negotiable=True),
                name="product_price_or_flag_required",
            ),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_unique_slug(Product, self.title, instance=self)
        elif self.pk:
            # Slug o'zgarsa eskisini saqlaymiz: tashqi havolalar va qidiruv
            # tizimlari indeksidagi URL 301 orqali yangisiga yo'naltiriladi.
            old_slug = (
                Product.all_objects.filter(pk=self.pk)
                .values_list("slug", flat=True)
                .first()
            )
            if old_slug and old_slug != self.slug and old_slug not in self.previous_slugs:
                self.previous_slugs = [*self.previous_slugs, old_slug][-10:]
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # Holat mashinasi
    # ------------------------------------------------------------------
    def can_transition_to(self, new_status):
        if new_status == self.status:
            return True
        return new_status in STATUS_TRANSITIONS.get(self.status, set())

    @property
    def is_public(self):
        return self.status in PUBLIC_STATUSES and not self.is_deleted

    @property
    def is_expired(self):
        return bool(self.expires_at and self.expires_at < timezone.now())

    @property
    def is_featured_now(self):
        if not self.is_featured:
            return False
        return not self.featured_until or self.featured_until > timezone.now()

    @property
    def primary_image(self):
        images = list(self.images.all())
        if not images:
            return None
        for image in images:
            if image.is_primary:
                return image
        return images[0]

    @property
    def display_phone(self):
        return self.contact_phone or self.seller.phone

    @property
    def is_used(self):
        return self.condition != Condition.NEW

    # ------------------------------------------------------------------
    # SEO
    # ------------------------------------------------------------------
    def locale_url(self, lang="uz"):
        """Til prefiksli to'liq URL: https://domain/uz/product/slug"""
        return f"{settings.FRONTEND_URL}/{lang}/product/{self.slug}"

    @property
    def absolute_url(self):
        """Canonical URL — standart til (uz)."""
        return self.locale_url(settings.DEFAULT_LANGUAGE)

    @property
    def alternate_urls(self):
        """hreflang uchun barcha til variantlari."""
        return {lang: self.locale_url(lang) for lang, _ in settings.LANGUAGES}

    @property
    def should_be_indexed(self):
        """Sahifa qidiruv tizimlari indeksiga tushsinmi?

        Sotilgan e'lon ham indekslanadi: Google ecommerce bo'yicha
        tavsiyasi "mavjud bo'lmagan mahsulotni noindex qilmang" deydi,
        chunki sahifa narx tarixi uchun foydali bo'lib qoladi va
        JSON-LD da holat `SoldOut` deb aniq ko'rsatiladi. Bu xatti-harakat
        admin paneldagi `index_sold_products` bilan o'chiriladi.
        """
        if not self.is_indexable or self.is_deleted:
            return False
        if self.status in (ProductStatus.APPROVED, ProductStatus.RESERVED):
            return True
        if self.status == ProductStatus.SOLD:
            from apps.seo.models import SeoSettings

            return SeoSettings.load().index_sold_products
        return False

    @property
    def schema_availability(self):
        """schema.org/ItemAvailability qiymati."""
        return {
            ProductStatus.APPROVED: "https://schema.org/InStock",
            ProductStatus.RESERVED: "https://schema.org/PreOrder",
            ProductStatus.SOLD: "https://schema.org/SoldOut",
        }.get(self.status, "https://schema.org/OutOfStock")

    @property
    def schema_condition(self):
        """schema.org/OfferItemCondition qiymati."""
        if self.condition == Condition.NEW:
            return "https://schema.org/NewCondition"
        if self.condition == Condition.FOR_PARTS:
            return "https://schema.org/DamagedCondition"
        return "https://schema.org/UsedCondition"


class SavedSearch(BaseModel):
    """Saqlangan qidiruv — mos e'lon chiqqanda xabar berish uchun."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="foydalanuvchi",
        on_delete=models.CASCADE,
        related_name="saved_searches",
    )
    name = models.CharField("nomi", max_length=120)
    query_params = models.JSONField("filtr parametrlari", default=dict)
    notify = models.BooleanField("yangi e'lon chiqsa xabar ber", default=True)
    last_notified_at = models.DateTimeField("oxirgi xabar", null=True, blank=True)

    class Meta:
        verbose_name = "saqlangan qidiruv"
        verbose_name_plural = "saqlangan qidiruvlar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.name}"


class SearchQueryLog(models.Model):
    """Qidiruv so'rovlari jurnali — autocomplete takliflari va tahlil uchun."""

    query = models.CharField("so'rov", max_length=200, db_index=True)
    results_count = models.PositiveIntegerField("natijalar soni", default=0)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="search_logs",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "qidiruv so'rovi"
        verbose_name_plural = "qidiruv so'rovlari"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["query", "-created_at"])]

    def __str__(self):
        return self.query
