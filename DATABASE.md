# CT Sale — DATABASE

**PostgreSQL 16** · 33 model · 45 jadval (Django tizim jadvallari bilan) · 239 indeks

Kengaytmalar: `pg_trgm` (opechatkaga chidamli qidiruv), `unaccent`.
Ular `apps/core/migrations/0001_postgres_extensions.py` orqali
o'rnatiladi — test bazasi har safar noldan qurilgani uchun qo'lda
yaratib bo'lmaydi.

---

## Abstract modellar

Barcha jadvallar `apps/core/models.py` dagi aralashmalardan quriladi:

| Model | Beradi |
|---|---|
| `TimeStampedModel` | `created_at`, `updated_at` |
| `UUIDModel` | `id` = UUIDv4 |
| `SoftDeleteModel` | `is_deleted`, `deleted_at`, `objects` / `all_objects` |
| `AuditableModel` | `created_by`, `updated_by` |
| `BaseModel` | Yuqoridagilarning birlashmasi |

### Nega UUID

Tashqariga ko'rinadigan obyektlarda (`Product`, `User`) ketma-ket
integer ID e'lonlar sonini va o'sish tezligini oshkor qiladi —
raqobatchi `/products/1`, `/products/2` deb yurib katalogni yig'ib
olishi mumkin. Ichki ma'lumotnomalar (`Category`, `Brand`) esa
`BigAutoField` da qoladi: ular ommaviy sir emas va JOIN'lar arzonroq.

### Nega soft delete

O'chirilgan e'lon audit va shikoyat tekshiruvi uchun kerak bo'lib
qolishi mumkin. `objects` menejeri o'chirilganlarni ko'rsatmaydi,
`all_objects` — hammasini.

---

## Sxema

```
              ┌──────────────┐
              │    User      │◄──────┐
              └──────┬───────┘       │
       ┌─────────────┼─────────────┐ │
       ▼             ▼             ▼ │
┌────────────┐ ┌──────────┐ ┌─────────────┐
│ShopProfile │ │ UserRole │ │   Product   │
└────────────┘ └────┬─────┘ └──────┬──────┘
                    ▼              │
              ┌──────────┐         ├──► ProductImage
              │   Role   │         ├──► ProductVideo
              └────┬─────┘         ├──► ModerationTask
                   ▼               ├──► Favorite
            ┌──────────────┐       ├──► ProductView
            │RolePermission│       ├──► PhoneReveal
            └──────┬───────┘       ├──► Report
                   ▼               └──► TelegramPost
            ┌──────────────┐
            │  Permission  │       ┌──────────┐
            └──────────────┘       │ Category │◄─┐ (self-FK)
                                   └────┬─────┘──┘
     ┌──────────┐                       ▼
     │  Region  │◄─┐              ┌──────────────────┐
     └────┬─────┘  │              │AttributeDefinition│
          ▼        │              └────────┬─────────┘
     ┌──────────┐  │                       ▼
     │ District │  │               ┌───────────────┐
     └──────────┘  │               │AttributeOption│
                   │               └───────────────┘
              (Product.region)
```

---

## Asosiy jadvallar

### `accounts_user` — 28 maydon

Identifikator: **telefon raqam** (`USERNAME_FIELD`), `+998XXXXXXXXX`
ko'rinishida normallashtiriladi.

| Guruh | Maydonlar |
|---|---|
| Kimlik | `phone` (unique), `email` (unique, nullable), `first_name`, `last_name`, `avatar` |
| Manzil | `region`, `district` |
| Tasdiqlash | `is_phone_verified`, `is_email_verified`, `is_verified_seller` |
| Telegram | `telegram_id`, `telegram_username` |
| Django auth | `is_active`, `is_staff`, `is_superuser`, `password` |
| Bloklash | `is_banned`, `banned_until`, `ban_reason` |
| Kuzatuv | `last_seen_at`, `created_at`, `updated_at` |

`email` bo'sh satr emas, **NULL** saqlanadi — aks holda unique cheklov
ikkinchi bo'sh emailda buzilardi.

### `products_product` — 54 maydon

Loyihaning markaziy jadvali.

| Guruh | Maydonlar |
|---|---|
| Asosiy | `title`, `slug` (unique), `description`, `seller`, `category`, `brand`, `model_name` |
| Narx | `price`, `currency`, `is_negotiable`, `price_on_request`, `is_exchange_possible`, `quantity` |
| Holat | `condition`, `status` |
| Ishlatilgan | `usage_period`, `defects`, `repair_history`, `has_warranty`, `warranty_until`, `has_original_box`, `accessories`, `purchase_date` |
| Xususiyatlar | `specs` (**JSONB**) |
| Manzil | `region`, `district`, `address_note` |
| Aloqa | `contact_phone`, `contact_name` |
| Statistika | `views_count`, `favorites_count`, `phone_reveals_count` |
| Reklama | `is_featured`, `featured_until` |
| Vaqtlar | `published_at`, `expires_at`, `sold_at`, `bumped_at` |
| Qidiruv | `search_vector` (**tsvector**) |
| SEO | `seo_title`, `seo_description`, `seo_keywords`, `og_title`, `og_description`, `og_image`, `is_indexable`, `previous_slugs` (JSONB) |
| Audit | `created_by`, `updated_by`, `is_deleted`, `deleted_at` |

#### Cheklovlar

```sql
-- Narx manfiy bo'lmasin
CHECK (price >= 0 OR price IS NULL)

-- Narx ko'rsatilmagan bo'lsa, sabab belgilangan bo'lishi shart —
-- aks holda xaridor hech narsa bilmaydi
CHECK (price IS NOT NULL OR price_on_request OR is_negotiable)
```

#### `previous_slugs`

Slug o'zgarganda eskisi shu massivga qo'shiladi (oxirgi 10 tasi).
`/products/{eski-slug}` so'rovi baribir mahsulotni topadi — tashqi
havolalar va qidiruv tizimlari indeksidagi URL buzilmaydi.

---

## Dinamik xususiyatlar (gibrid EAV + JSONB)

Bu loyihaning eng muhim sxema qarori.

**Sxema** — `catalog_attributedefinition` jadvalida, admin panelda
boshqariladi:

| Maydon | Izoh |
|---|---|
| `category` | Qaysi kategoriyaga tegishli |
| `code` | `specs` JSONB ichidagi kalit (`ram_gb`) |
| `label_uz/ru/en` | Ko'rinadigan nom |
| `data_type` | `text`, `integer`, `decimal`, `boolean`, `select`, `multiselect` |
| `unit` | `GB`, `GHz`, `"` |
| `is_required`, `is_filterable`, `is_in_card` | Xulq bayroqlari |
| `min_value`, `max_value` | Son chegaralari |

**Qiymat** — `products_product.specs` JSONB ustunida:

```json
{
  "cpu": "Intel Core i7-13650HX",
  "ram_gb": 16,
  "storage_gb": 1000,
  "gpu": "RTX 4060",
  "screen_inch": 16.0,
  "os": "win11"
}
```

### Nega gibrid

| Yondashuv | Muammo |
|---|---|
| Sof EAV (`attribute_value` jadvali) | Har xususiyat uchun JOIN — 10 ta xususiyatli mahsulot ro'yxati 10 ta JOIN degani. O'qish sekin |
| Sof JSONB (sxemasiz) | Admin boshqara olmaydi, validatsiya yo'q, filtr variantlarini bilib bo'lmaydi |
| **Gibrid** | Sxema jadvalda (admin boshqaradi, validatsiya bor), qiymat JSONB da (bitta qatordan o'qiladi) |

Yangi xususiyat qo'shish uchun **migratsiya kerak emas** — admin
panelda yaratiladi va forma avtomatik o'zgaradi.

### Meros

`AttributeDefinition` kategoriyaga bog'lanadi, lekin
`Category.inherited_attributes()` ota kategoriyalardagilarni ham
qaytaradi:

```
Noutbuklar          → warranty_months
  └ Gaming noutbuklar → cpu, ram_gb, gpu, os   (+ warranty_months meros)
```

### Filtrlash

`specs` ustida `GIN (jsonb_path_ops)` indeksi bor. Filtrlar faqat
sxemada mavjud va `is_filterable` bo'lgan kodlarni qabul qiladi —
foydalanuvchi ixtiyoriy JSONB yo'li bo'ylab so'rov yubora olmaydi.

---

## Indekslar

Jami 239 ta. Eng muhimlari:

| Jadval | Indeks | Nima uchun |
|---|---|---|
| `products_product` | `GIN(search_vector)` | Full-text qidiruv |
| | `GIN(specs jsonb_path_ops)` | Xususiyat filtrlari |
| | `(status, published_at DESC)` | Katalog ro'yxati |
| | `(category_id, status, price)` | Kategoriya + narx filtri |
| | `(seller_id, status)` | "Mening e'lonlarim" |
| | `(brand_id, status)` · `(region_id, status)` | Filtrlar |
| | `(is_featured DESC, published_at DESC)` | VIP saralash |
| | `UNIQUE(slug)` | SEO URL |
| `interactions_favorite` | `UNIQUE(user_id, product_id)` | Takror sevimli bo'lmasin |
| `interactions_productview` | `(product_id, ip_hash, created_at)` | 24 soatlik dedup |
| `interactions_report` | `UNIQUE(product_id, reporter_id)` qisman | Bitta user — bitta shikoyat |
| `mediafiles_productimage` | `UNIQUE(product_id) WHERE is_primary` | Faqat bitta asosiy rasm |
| `analytics_auditlog` | `(actor_id, created_at DESC)` · `(target_type, target_id)` | Audit qidiruv |
| `accounts_otpcode` | `(phone, purpose, created_at DESC)` | Oxirgi kodni topish |

### Qisman unique indekslar

```sql
-- Bitta mahsulotda faqat bitta asosiy rasm
UNIQUE (product_id) WHERE is_primary = true

-- Anonim shikoyatlar cheklanmaydi, ro'yxatdan o'tganlar — bir marta
UNIQUE (product_id, reporter_id) WHERE reporter_id IS NOT NULL
```

---

## Qidiruv

`search_vector` ustuni mahsulot saqlanganda yangilanadi
(`apps/products/services.update_search_vector`):

| Manba | Vazn |
|---|---|
| `title` | A (eng muhim) |
| `model_name` | B |
| `description` | C |

Qidiruv ikki bosqichli: avval `SearchQuery`, natija bo'lmasa
`TrigramSimilarity` (shuning uchun `noutbukk` ham topiladi).

> **Nega Elasticsearch emas:** 100 000 e'longacha PostgreSQL FTS
> yetarli va u qo'shimcha servis, RAM hamda sinxronizatsiya muammosi
> talab qilmaydi. Arxitektura keyinchalik almashtirishga tayyor —
> qidiruv mantig'i `apps/products/views.py` dagi `_apply_search` da
> to'plangan.

---

## Denormalizatsiya

Tez-tez o'qiladigan, kam o'zgaradigan hisoblagichlar jadvalda saqlanadi:

| Ustun | Qayerda yangilanadi |
|---|---|
| `products_product.views_count` | Har yangi ko'rishda `F()` bilan |
| `products_product.favorites_count` | Sevimli qo'shilganda/olinganda |
| `products_product.phone_reveals_count` | Telefon ochilganda |
| `catalog_category.products_count` | Status o'zgarganda; `manage.py recount` bilan tiklanadi |
| `catalog_brand.products_count` | Shu tarzda |

Ommaviy import yoki bazani qo'lda o'zgartirgandan keyin:

```bash
manage.py recount
```

---

## Ko'rish va telefon hisoblagichlari

`ProductView` va `PhoneReveal` jadvallarida IP **ochiq saqlanmaydi**:

```python
ip_hash = sha256(SECRET_KEY[:16] + ip)
```

Takrorni aniqlash uchun yetarli, lekin bazadan IP manzillarni tiklab
bo'lmaydi. Bir xil hash 24 soat ichida qayta kelsa hisoblanmaydi.

---

## Migratsiyalar

```bash
manage.py makemigrations
manage.py migrate
manage.py showmigrations
```

15 ta migratsiya fayli. Birinchisi (`core/0001`) PostgreSQL
kengaytmalarini o'rnatadi va qolganlaridan oldin ishlashi kerak.

### Boshlang'ich ma'lumot

```bash
manage.py seed_roles       # 25 ruxsat, 5 rol — idempotent
manage.py seed_catalog     # 14 viloyat, 79 tuman, 68 kategoriya, 40 brend, 96 xususiyat
manage.py seed_products --products 120   # demo (faqat development)
```

`seed_roles` va `seed_catalog` `update_or_create` ishlatadi —
qayta yurgizish xavfsiz va production'da ham ishlatiladi.

---

## Zaxira nusxa

```bash
# To'liq
pg_dump -U postgres -Fc ctsale > ctsale_$(date +%F).dump

# Faqat sxema
pg_dump -U postgres --schema-only ctsale > schema.sql

# Tiklash
pg_restore -U postgres -d ctsale --clean ctsale_2026-09-21.dump
```

Media fayllar bazada emas — `backend/media/` (yoki S3) alohida
zaxiralanadi. Jadvallar faqat yo'l va metama'lumot saqlaydi.
