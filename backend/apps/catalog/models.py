"""Katalog: hudud, kategoriya daraxti, brend va dinamik atributlar.

Spec arxitekturasi gibrid: bu yerdagi AttributeDefinition — sxema
(admin panelda boshqariladi), qiymatlar esa Product.specs (JSONB) ichida.
Shu sababli yangi xususiyat qo'shish uchun migration kerak emas, lekin
o'qish bitta qatordan bo'ladi.
"""

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel
from apps.core.utils import make_unique_slug

# Xususiyat sxemasi deyarli o'zgarmaydi, lekin har bir mahsulot
# kartasi uchun kerak bo'ladi. Kesh versiyasi sxema o'zgarganda
# ko'tariladi — shunda eski yozuvlar bir zumda yaroqsiz bo'ladi va
# alohida o'chirish kerak emas.
ATTRIBUTE_CACHE_VERSION_KEY = "catalog:attr:version"
ATTRIBUTE_CACHE_TTL = 3600


def attributes_cache_version():
    version = cache.get(ATTRIBUTE_CACHE_VERSION_KEY)
    if version is None:
        version = 1
        cache.set(ATTRIBUTE_CACHE_VERSION_KEY, version, None)
    return version


def bump_attributes_cache():
    """Sxema o'zgarganda chaqiriladi (signallar orqali)."""
    try:
        cache.incr(ATTRIBUTE_CACHE_VERSION_KEY)
    except ValueError:
        # Kalit hali yo'q yoki kesh tozalangan.
        cache.set(ATTRIBUTE_CACHE_VERSION_KEY, 1, None)


class Region(TimeStampedModel):
    """Viloyat / shahar."""

    name_uz = models.CharField("nomi (uz)", max_length=80)
    name_ru = models.CharField("nomi (ru)", max_length=80, blank=True)
    name_en = models.CharField("nomi (en)", max_length=80, blank=True)
    slug = models.SlugField("slug", max_length=100, unique=True)
    order = models.PositiveSmallIntegerField("tartib", default=0)
    is_active = models.BooleanField("faol", default=True)

    class Meta:
        verbose_name = "viloyat"
        verbose_name_plural = "viloyatlar"
        ordering = ["order", "name_uz"]

    def __str__(self):
        return self.name_uz

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_unique_slug(Region, self.name_uz, instance=self)
        super().save(*args, **kwargs)


class District(TimeStampedModel):
    """Tuman / shahar tumani."""

    region = models.ForeignKey(
        Region, verbose_name="viloyat", on_delete=models.CASCADE, related_name="districts"
    )
    name_uz = models.CharField("nomi (uz)", max_length=80)
    name_ru = models.CharField("nomi (ru)", max_length=80, blank=True)
    name_en = models.CharField("nomi (en)", max_length=80, blank=True)
    slug = models.SlugField("slug", max_length=120)
    is_active = models.BooleanField("faol", default=True)

    class Meta:
        verbose_name = "tuman"
        verbose_name_plural = "tumanlar"
        ordering = ["name_uz"]
        constraints = [
            models.UniqueConstraint(fields=["region", "slug"], name="uniq_district_slug_in_region")
        ]

    def __str__(self):
        return f"{self.region.name_uz} / {self.name_uz}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_unique_slug(District, self.name_uz, instance=self)
        super().save(*args, **kwargs)


class Category(TimeStampedModel):
    """Ko'p darajali kategoriya daraxti (self-FK).

    Kategoriyalar soni kichik (~50-100), shuning uchun MPTT kabi
    qo'shimcha kutubxona kerak emas — oddiy rekursiya yetarli va
    natija keshlanadi.
    """

    parent = models.ForeignKey(
        "self",
        verbose_name="ota kategoriya",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    name_uz = models.CharField("nomi (uz)", max_length=120)
    name_ru = models.CharField("nomi (ru)", max_length=120, blank=True)
    name_en = models.CharField("nomi (en)", max_length=120, blank=True)
    slug = models.SlugField("slug", max_length=160, unique=True)
    description = models.TextField("tavsif", blank=True)

    icon = models.CharField(
        "ikonka", max_length=64, blank=True, help_text="Lucide ikonka nomi, masalan: laptop"
    )
    image = models.ImageField("rasm", upload_to="categories/", null=True, blank=True)

    order = models.PositiveSmallIntegerField("tartib", default=0)
    is_active = models.BooleanField("faol", default=True)
    is_featured = models.BooleanField("bosh sahifada", default=False)

    # SEO
    meta_title = models.CharField("meta title", max_length=180, blank=True)
    meta_description = models.CharField("meta description", max_length=300, blank=True)

    # Denormalizatsiya — katalogda har kategoriya yonida son ko'rsatish uchun.
    products_count = models.PositiveIntegerField("mahsulotlar soni", default=0)

    class Meta:
        verbose_name = "kategoriya"
        verbose_name_plural = "kategoriyalar"
        ordering = ["order", "name_uz"]
        indexes = [
            models.Index(fields=["parent", "is_active", "order"]),
            models.Index(fields=["is_featured", "is_active"]),
        ]

    def __str__(self):
        return self.full_path

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_unique_slug(Category, self.name_uz, instance=self)
        super().save(*args, **kwargs)

    def clean(self):
        # O'zini o'ziga ota qilib qo'yish yoki halqa yasash daraxtni buzadi.
        if self.parent_id and self.pk and self.parent_id == self.pk:
            raise ValidationError({"parent": "Kategoriya o'zining ota kategoriyasi bo'la olmaydi."})
        ancestor = self.parent
        while ancestor is not None:
            if self.pk and ancestor.pk == self.pk:
                raise ValidationError({"parent": "Kategoriyalar halqa hosil qilmasligi kerak."})
            ancestor = ancestor.parent

    @property
    def full_path(self):
        names, node = [], self
        while node is not None:
            names.append(node.name_uz)
            node = node.parent
        return " / ".join(reversed(names))

    @property
    def level(self):
        depth, node = 0, self.parent
        while node is not None:
            depth += 1
            node = node.parent
        return depth

    def ancestors(self, include_self=False):
        chain, node = [], self if include_self else self.parent
        while node is not None:
            chain.append(node)
            node = node.parent
        return list(reversed(chain))

    def descendant_ids(self):
        """O'zi + barcha avlodlari — katalogda 'ota kategoriya' tanlanganda.

        Butun daraxt bitta so'rovda o'qiladi va xotirada aylaniladi:
        qavat-qavat so'rash har daraja uchun alohida SQL degani edi.
        Kategoriyalar soni kichik (~70), shuning uchun hammasini olish
        arzonroq. Natija xususiyatlar bilan bir xil versiyada keshlanadi.
        """
        key = f"catalog:descendants:{attributes_cache_version()}:{self.pk}"
        cached = cache.get(key)
        if cached is not None:
            return cached

        pairs = Category.objects.values_list("pk", "parent_id")
        children_by_parent = {}
        for pk, parent_id in pairs:
            children_by_parent.setdefault(parent_id, []).append(pk)

        ids, stack = [self.pk], [self.pk]
        while stack:
            current = stack.pop()
            children = children_by_parent.get(current, [])
            ids.extend(children)
            stack.extend(children)

        cache.set(key, ids, ATTRIBUTE_CACHE_TTL)
        return ids

    def inherited_attributes(self, use_cache=True):
        """O'z atributlari + ota kategoriyalardan meros olganlari.

        Masalan "Elektronika" da `warranty` bo'lsa, "Noutbuk" ham oladi.

        Natija keshlanadi: katalogdagi har bir karta shu ro'yxatni
        so'raydi va sxema soatlab o'zgarmay turadi.
        """
        if use_cache:
            key = f"catalog:attrs:{attributes_cache_version()}:{self.pk}"
            cached = cache.get(key)
            if cached is not None:
                return cached

        category_ids = [c.pk for c in self.ancestors(include_self=True)]
        definitions = list(
            AttributeDefinition.objects.filter(category_id__in=category_ids, is_active=True)
            .select_related("category")
            .prefetch_related("options")
            .order_by("order", "label_uz")
        )

        if use_cache:
            cache.set(key, definitions, ATTRIBUTE_CACHE_TTL)
        return definitions


class Brand(TimeStampedModel):
    name = models.CharField("nomi", max_length=100, unique=True)
    slug = models.SlugField("slug", max_length=120, unique=True)
    logo = models.ImageField("logo", upload_to="brands/", null=True, blank=True)
    website = models.URLField("veb-sayt", blank=True)
    is_active = models.BooleanField("faol", default=True)
    is_popular = models.BooleanField("ommabop", default=False)
    order = models.PositiveSmallIntegerField("tartib", default=0)
    products_count = models.PositiveIntegerField("mahsulotlar soni", default=0)

    class Meta:
        verbose_name = "brend"
        verbose_name_plural = "brendlar"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_unique_slug(Brand, self.name, instance=self)
        super().save(*args, **kwargs)


class AttributeType(models.TextChoices):
    TEXT = "text", "Matn"
    INTEGER = "integer", "Butun son"
    DECIMAL = "decimal", "O'nlik son"
    BOOLEAN = "boolean", "Ha / Yo'q"
    SELECT = "select", "Tanlov (bitta)"
    MULTISELECT = "multiselect", "Tanlov (bir nechta)"


class AttributeDefinition(TimeStampedModel):
    """Kategoriyaga bog'langan xususiyat sxemasi.

    `code` — Product.specs JSONB ichidagi kalit. O'zgartirilsa eski
    e'lonlardagi qiymat yo'qoladi, shuning uchun yaratilgandan keyin
    o'zgartirish tavsiya etilmaydi (admin panelda ogohlantiriladi).
    """

    category = models.ForeignKey(
        Category, verbose_name="kategoriya", on_delete=models.CASCADE, related_name="attributes"
    )
    code = models.SlugField(
        "kod", max_length=60, help_text="specs JSONB ichidagi kalit, masalan: ram_gb"
    )
    label_uz = models.CharField("nomi (uz)", max_length=120)
    label_ru = models.CharField("nomi (ru)", max_length=120, blank=True)
    label_en = models.CharField("nomi (en)", max_length=120, blank=True)

    data_type = models.CharField(
        "turi", max_length=20, choices=AttributeType.choices, default=AttributeType.TEXT
    )
    unit = models.CharField("o'lchov birligi", max_length=20, blank=True, help_text="GB, GHz, \"")

    is_required = models.BooleanField("majburiy", default=False)
    is_filterable = models.BooleanField("filtrda ko'rinsin", default=True)
    is_in_card = models.BooleanField(
        "kartada ko'rinsin", default=False, help_text="Mahsulot kartasida qisqa ko'rsatiladi"
    )
    is_active = models.BooleanField("faol", default=True)
    order = models.PositiveSmallIntegerField("tartib", default=0)

    min_value = models.DecimalField(
        "eng kichik qiymat", max_digits=12, decimal_places=2, null=True, blank=True
    )
    max_value = models.DecimalField(
        "eng katta qiymat", max_digits=12, decimal_places=2, null=True, blank=True
    )
    placeholder = models.CharField("namuna matn", max_length=120, blank=True)

    class Meta:
        verbose_name = "xususiyat"
        verbose_name_plural = "xususiyatlar"
        ordering = ["order", "label_uz"]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "code"], name="uniq_attribute_code_in_category"
            )
        ]
        indexes = [models.Index(fields=["category", "is_active", "order"])]

    def __str__(self):
        return f"{self.category.name_uz} / {self.label_uz}"

    @property
    def has_options(self):
        return self.data_type in (AttributeType.SELECT, AttributeType.MULTISELECT)


class AttributeOption(TimeStampedModel):
    """SELECT / MULTISELECT turidagi xususiyat uchun variantlar."""

    attribute = models.ForeignKey(
        AttributeDefinition,
        verbose_name="xususiyat",
        on_delete=models.CASCADE,
        related_name="options",
    )
    value = models.CharField("qiymat", max_length=120, help_text="specs ichida saqlanadigan qiymat")
    label_uz = models.CharField("ko'rinishi (uz)", max_length=120)
    label_ru = models.CharField("ko'rinishi (ru)", max_length=120, blank=True)
    label_en = models.CharField("ko'rinishi (en)", max_length=120, blank=True)
    order = models.PositiveSmallIntegerField("tartib", default=0)
    is_active = models.BooleanField("faol", default=True)

    class Meta:
        verbose_name = "xususiyat varianti"
        verbose_name_plural = "xususiyat variantlari"
        ordering = ["order", "label_uz"]
        constraints = [
            models.UniqueConstraint(
                fields=["attribute", "value"], name="uniq_option_value_in_attribute"
            )
        ]

    def __str__(self):
        return self.label_uz
