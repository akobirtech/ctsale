# CT Sale — ARCHITECTURE

---

## 1. Overall architecture

```
                         +---------------------+
                         |     Telegram        |
                         |  Bot + Channel      |
                         +----------+----------+
                                    ^
                                    | Bot API (HTTPS)
                                    |
  +----------+      +---------------+---------------+      +--------------+
  | Browser  |<---->|   Nginx (reverse proxy/SSL)   |<---->|  React SPA   |
  | (SPA)    | HTTPS|   /api -> gunicorn            | static| (Vite build) |
  +----------+      |   /    -> static SPA          |      +--------------+
                    |   /media -> media fayllar     |
                    +---------------+---------------+
                                    |
                            +-------+--------+
                            |  Django + DRF  |
                            |   (gunicorn)   |
                            +---+--------+---+
                                |        |
                 +--------------+        +--------------+
                 |                                      |
         +-------+--------+                    +--------+-------+
         |  PostgreSQL 16 |                    |     Redis      |
         |  (pg_trgm,     |                    | broker + cache |
         |   unaccent)    |                    +--------+-------+
         +----------------+                             |
                                                +-------+-------+
                                                | Celery worker |
                                                | Celery beat   |
                                                +---------------+
```

**Prinsip:** backend — faqat JSON API. Frontend — mustaqil SPA. Ikkalasi `/api/v1/` shartnomasi orqali bog'langan.

---

## 2. Backend architecture

### 2.1 Papka strukturasi

```
backend/
├── config/
│   ├── settings/
│   │   ├── base.py        # umumiy sozlamalar
│   │   ├── dev.py         # lokal development
│   │   ├── prod.py        # production
│   │   └── test.py        # testlar
│   ├── urls.py            # /api/v1/ router
│   ├── celery.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── core/              # abstract modellar, utils, pagination, exceptions
│   ├── accounts/          # User, profile, OTP, JWT auth
│   ├── rbac/              # Role, Permission, permission classlari
│   ├── catalog/           # Category, Brand, AttributeDefinition
│   ├── products/          # Product, spec validatsiya, status machine
│   ├── mediafiles/        # ProductImage, ProductVideo, optimizatsiya
│   ├── moderation/        # ModerationTask, approve/reject
│   ├── interactions/      # Favorite, Compare, Report, ProductView
│   ├── notifications/     # Notification, kanallar
│   ├── telegrambot/       # TelegramSettings, TelegramPost, client, bot
│   ├── analytics/         # AuditLog, dashboard aggregatlari
│   └── adminapi/          # /api/v1/admin/* endpointlari
├── media/                 # yuklangan fayllar (dev)
├── static/
├── tests/
├── manage.py
└── requirements.txt
```

### 2.2 Har bir app ichidagi qatlamlar

```
app/
├── models.py       # faqat ma'lumot strukturasi + oddiy metodlar
├── managers.py     # QuerySet / Manager
├── serializers.py  # I/O validatsiya va shakl
├── services.py     # BUSINESS LOGIC shu yerda (views'da emas)
├── selectors.py    # murakkab o'qish so'rovlari
├── permissions.py  # DRF permission classlari
├── filters.py      # django-filter
├── tasks.py        # Celery tasklari
├── signals.py
├── views.py        # ingichka: serializer -> service -> response
└── urls.py
```

**Qoida:** view faqat HTTP bilan ishlaydi. Har qanday biznes qaror — `services.py` ichida. Bu testlashni va keyinchalik boshqa kanaldan (Telegram bot, management command) chaqirishni osonlashtiradi.

---

## 3. Database architecture

### 3.1 Abstract modellar (`apps/core/models.py`)

| Model | Beradi |
|---|---|
| `TimeStampedModel` | `created_at`, `updated_at` |
| `UUIDModel` | `id` = UUIDv4 (tashqi ko'rinadigan obyektlar uchun) |
| `SoftDeleteModel` | `is_deleted`, `deleted_at`, `objects` / `all_objects` |
| `AuditableModel` | `created_by`, `updated_by` |
| `BaseModel` | Yuqoridagilarning birlashmasi |

### 3.2 Asosiy jadvallar

```
User 1---1 UserProfile
User 1---* Product (seller)
User *---* Role (UserRole)
Role *---* Permission (RolePermission)

Category 1---* Category (parent, self-FK)
Category 1---* AttributeDefinition
AttributeDefinition 1---* AttributeOption
Category 1---* Product
Brand    1---* Product

Product 1---* ProductImage
Product 1---* ProductVideo
Product 1---1 ModerationTask (oxirgisi)
Product 1---* Favorite
Product 1---* Report
Product 1---* ProductView
Product 1---* TelegramPost
```

### 3.3 Indexlar

| Jadval | Index | Maqsad |
|---|---|---|
| products | `GIN(search_vector)` | full-text search |
| products | `GIN(specs jsonb_path_ops)` | spec filtrlash |
| products | `GIN(title gin_trgm_ops)` | opechatkaga chidamli qidiruv |
| products | `(status, published_at DESC)` | katalog ro'yxati |
| products | `(category_id, status, price)` | kategoriya + narx filtri |
| products | `UNIQUE(slug)` | SEO URL |
| favorites | `UNIQUE(user_id, product_id)` | takrorlanmaslik |
| product_views | `(product_id, created_at)` | statistika |
| audit_log | `(actor_id, created_at DESC)` | audit qidiruv |

### 3.4 Specification arxitekturasi (gibrid EAV + JSONB)

- **Sxema:** `AttributeDefinition` — admin panelda boshqariladigan meta-ma'lumot
  (`code`, `label_uz/ru/en`, `data_type`, `unit`, `is_required`, `is_filterable`, `order`, `category`).
- **Qiymat:** `Product.specs` — JSONB, kalit = `AttributeDefinition.code`.

```json
{
  "cpu": "Intel Core i7-13700H",
  "ram_gb": 16,
  "storage_gb": 512,
  "gpu": "RTX 4060",
  "screen_inch": 16.0,
  "refresh_hz": 165,
  "os": "Windows 11"
}
```

**Nega gibrid:** EAV o'qishda sekin (har spec uchun JOIN), sof JSONB esa boshqarib bo'lmaydigan.
Gibrid — admin yangi maydon qo'sha oladi (EAV afzalligi), o'qish bitta qatordan bo'ladi (JSONB afzalligi).

---

## 4. Authentication architecture

```
Register(phone, password)
  -> User(is_active=False, is_phone_verified=False)
  -> OTP(code=6 raqam, ttl=5 daqiqa, attempts=0)
  -> yuborish: dev=konsol/Telegram, prod=SMS provayder

Verify(phone, code)
  -> tekshirish (ttl, attempts<=5)
  -> User.is_phone_verified=True, is_active=True
  -> access + refresh qaytadi

Login(phone, password)
  -> access  (15 daqiqa) -> JSON javobda -> frontend XOTIRADA saqlaydi
  -> refresh (7 kun)     -> httpOnly + Secure + SameSite=Lax COOKIE

Refresh
  -> cookie'dagi refresh -> yangi access + YANGI refresh (rotation)
  -> eski refresh blacklist'ga

Logout -> refresh blacklist + cookie o'chirish
```

**Nega access tokenni localStorage'da saqlamaymiz:** XSS bo'lsa localStorage o'qiladi.
Xotirada saqlash + httpOnly refresh cookie — sahifa yangilanganda `/refresh` chaqirib sessiya tiklanadi.

---

## 5. Permission architecture (RBAC)

```
User --* UserRole *-- Role --* RolePermission *-- Permission(code)
```

Permission kodlari `resurs.harakat` shaklida:

```
product.view_any     product.create      product.edit_any     product.delete_any
product.approve      product.reject      product.feature
user.view            user.ban            user.change_role
category.manage      attribute.manage    brand.manage
telegram.manage      telegram.publish
report.view          report.resolve
audit.view           stats.view
```

Default rollar:

| Rol | Permissionlar |
|---|---|
| `SUPERADMIN` | `*` (barchasi) |
| `ADMIN` | product.*, category.*, brand.*, attribute.*, telegram.*, stats.view, user.view |
| `MODERATOR` | product.view_any, product.approve, product.reject, report.view, report.resolve |
| `SUPPORT` | user.view, product.view_any, report.view |
| `USER` | (yo'q — o'z obyektiga egalik orqali ishlaydi) |

Tekshirish ikki bosqichli: **permission class** (harakat darajasi) + **object permission** (egalik darajasi).

---

## 6. Media architecture

```
POST /api/v1/products/{id}/images/  (multipart)
  |
  +-> 1. Kengaytma tekshiruvi     (.jpg .jpeg .png .webp)
  +-> 2. MIME tekshiruvi          (Content-Type)
  +-> 3. Magic bytes tekshiruvi   (haqiqiy fayl turi)
  +-> 4. Hajm tekshiruvi          (<= 10 MB)
  +-> 5. Son tekshiruvi           (<= 10 rasm/e'lon)
  +-> 6. Pillow bilan ochish      (buzuq fayl aniqlanadi)
  |
  +-> ProductImage saqlanadi (original)
  +-> Celery: process_image(image_id)
        +-> EXIF metadata tozalanadi (GPS!)
        +-> WebP ga konvertatsiya
        +-> thumb  300px
        +-> medium 800px
        +-> large  1600px
        +-> is_processed = True
```

Video: `.mp4 .webm`, <= 50 MB, <= 2 ta/e'lon. Transcoding yo'q, faqat validatsiya + poster frame.

**Storage abstraksiyasi:** `DEFAULT_FILE_STORAGE` `.env` orqali.
Dev — lokal disk, Production — S3-compatible (`django-storages`). Kod o'zgarmaydi.

---

## 7. Telegram architecture

```
apps/telegrambot/
├── models.py       TelegramSettings (singleton), TelegramPost
├── client.py       TelegramClient — Bot API wrapper (requests, retry, timeout)
├── templates.py    PostTemplateRenderer — {title} {price} ... o'zgaruvchilar
├── services.py     publish_product(), update_post_as_sold(), delete_post()
├── tasks.py        Celery: publish_product_to_telegram(product_id)
├── bot.py          Bot handlerlari (/start, qidiruv, mening e'lonlarim)
└── views.py        webhook + admin API
```

### Post oqimi

```
Product.status -> APPROVED
   |
   +-- signal(post_save) --> publish_product_to_telegram.delay(product.id)
                               |
                               +-> TelegramSettings.auto_publish tekshiriladi
                               +-> TelegramPost(status=PENDING) yaratiladi
                               +-> caption = render(template, product)
                               +-> media tanlanadi:
                               |     1 rasm  -> sendPhoto
                               |     2+ rasm -> sendMediaGroup (max 10)
                               |     video   -> sendVideo
                               +-> inline tugma: [Saytda ko'rish] -> {FRONTEND_URL}/products/{slug}
                               |
                               +-- OK   -> status=PUBLISHED, message_id saqlanadi
                               +-- XATO -> status=FAILED, error_message
                                            retry: 3 marta (60s, 300s, 900s)
```

### Mock rejim

`TELEGRAM_BOT_TOKEN` bo'sh bo'lsa yoki `TELEGRAM_MOCK=True` bo'lsa:
API chaqirilmaydi, render qilingan post `TelegramPost.rendered_payload` ga yoziladi,
`status=PUBLISHED`, `message_id=0`. Butun oqim testlanadi, hech narsa jo'natilmaydi.

### Xavfsizlik

- Token faqat `.env` da. `.gitignore` da. Kodda hech qachon yo'q.
- Frontend'ga hech qachon uzatilmaydi (admin API faqat `is_configured: true/false` qaytaradi).
- Webhook `secret_token` header bilan tekshiriladi.

---

## 8. Frontend architecture

```
frontend/src/
├── main.jsx
├── App.jsx
├── api/
│   ├── client.js         # axios instance + interceptorlar
│   ├── auth.js  products.js  catalog.js  admin.js ...
├── components/
│   ├── ui/               # Button, Input, Modal, Toast, Badge, Skeleton ...
│   ├── product/          # ProductCard, ProductGrid, Gallery, SpecTable
│   ├── filters/          # FilterSidebar, FilterDrawer, PriceRange
│   └── layout/           # Navbar, Footer, BottomNav, Container
├── pages/
│   ├── Home  Catalog  ProductDetail  Auth  Profile
│   ├── seller/           # Dashboard, ProductForm, MyProducts
│   └── admin/            # Dashboard, Moderation, Users, Categories, Telegram
├── hooks/                # useAuth, useDebounce, useFilters, useMediaQuery
├── store/                # auth store (zustand)
├── styles/               # tokens.css, index.css
├── i18n/                 # uz.json, ru.json, en.json
└── utils/                # format.js (narx, sana), validators.js
```

### Ma'lumot oqimi

```
Komponent -> TanStack Query hook -> api/*.js -> axios client -> /api/v1/*
                    ^                              |
                    |                       401 -> /auth/refresh -> qayta urinish
                    +-- cache, loading, error holatlari
```

### Design system (tokenlar)

| Token | Qiymat |
|---|---|
| Accent | `#4F46E5` (indigo-600) |
| Neutral | slate shkalasi |
| Radius | 8px (kichik) / 12px (karta) / 16px (modal) |
| Shadow | 3 daraja, juda yumshoq |
| Font | Inter (fallback: system-ui) |
| Spacing | 4px bazali shkala |
| Breakpoint | 360 / 640 / 768 / 1024 / 1280 / 1536 |

Dark mode — CSS o'zgaruvchilari `[data-theme]` orqali, `prefers-color-scheme` hisobga olinadi.

---

## 9. Deployment architecture

```
Ubuntu 22.04 server
├── nginx                  :80/:443  SSL (certbot)
│    ├── /            -> /var/www/ctsale/frontend/dist  (SPA, try_files)
│    ├── /api/        -> proxy_pass 127.0.0.1:8000
│    ├── /media/      -> alias /var/www/ctsale/media
│    └── /static/     -> alias /var/www/ctsale/static
├── gunicorn (systemd)     :8000  config.wsgi
├── celery worker (systemd)
├── celery beat (systemd)
├── postgresql             :5432 (faqat localhost)
└── redis                  :6379 (faqat localhost)
```

Muqobil: `docker-compose.yml` — `backend`, `frontend`, `postgres`, `redis`, `celery`, `celery-beat`, `nginx`.

### Muhit o'zgaruvchilari

Barcha sirlar `.env` da. `.env.example` da faqat kalit nomlari.
Production'da `DEBUG=False`, `ALLOWED_HOSTS` aniq, `SECURE_*` sozlamalari yoqilgan.

---

## 10. Asosiy texnik qarorlar va sabablari

| Qaror | Sabab |
|---|---|
| PostgreSQL FTS (Elasticsearch emas) | 100k e'longacha yetarli, +1 servis va +RAM talab qilmaydi |
| Spec uchun JSONB + meta jadval | Admin boshqaruvi + tez o'qish; sof EAV sekin, sof JSONB boshqarilmaydi |
| Refresh cookie'da, access xotirada | XSS'da token o'g'irlanishining oldini oladi |
| Business logic `services.py` da | Testlash oson, bir logikani API/bot/command'dan chaqirish mumkin |
| Celery EAGER fallback | Redis bo'lmaganda ham dev muhiti ishlaydi |
| MPTT o'rniga oddiy self-FK | Kategoriyalar soni kichik; ortiqcha dependency kerak emas |
| Telegram mock rejim | Real token/kanal bo'lmaganda ham butun oqim testlanadi |
| SPA + bot uchun meta injection | Vite stack'i saqlanadi, SEO ham yechiladi |
