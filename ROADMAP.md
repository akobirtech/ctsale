# CT Sale — ROADMAP

> IT texnika marketplace (kompyuter, noutbuk, komplektuvchi) — O'zbekiston bozori uchun.
> Stack: **Django 5 + DRF + PostgreSQL 16 + React + Vite + Tailwind + Celery/Redis + Telegram Bot API**

---

## 0. PROJECT ANALYSIS

### 0.1 Loyiha maqsadi

IT texnikani (yangi va ishlatilgan) sotish/sotib olish uchun **e'lonlar marketplace** (classifieds).
Sayt to'lovga aralashmaydi — xaridor sotuvchi bilan to'g'ridan-to'g'ri bog'lanadi.
Barcha tasdiqlangan e'lon avtomatik **Telegram kanalga** post qilinadi (asosiy trafik kanali).

### 0.2 Asosiy userlar

| Rol | Kim | Asosiy maqsad |
|---|---|---|
| **Guest** | Ro'yxatdan o'tmagan | Qidirish, ko'rish, telefon olish |
| **Buyer** | Ro'yxatdan o'tgan user | Sevimlilar, taqqoslash, shikoyat, saqlangan qidiruv |
| **Seller** | E'lon joylagan user | E'lon CRUD, media, statistika, do'kon profili |
| **Moderator** | Xodim | E'lonlarni tasdiqlash/rad etish, shikoyatlar |
| **Support** | Xodim | Foydalanuvchilar bilan ishlash, shikoyatlar |
| **Admin** | Xodim | Kategoriya/brend/atribut, Telegram, statistika |
| **Superadmin** | Egasi | Rollar, permissionlar, tizim sozlamalari |

### 0.3 Buyer flow

```
Home -> (search | category | filter) -> Catalog -> Product detail
   -> Gallery/Video -> Specs -> Seller card -> [Telefonni ko'rsatish] -> Qo'ng'iroq/Telegram
   -> (Favorite | Compare | Share | Report)
```

### 0.4 Seller flow

```
Register (telefon + OTP) -> Profil to'ldirish -> [+ E'lon joylash]
   -> Kategoriya tanlash -> Dinamik spec forma -> Rasm/video yuklash -> Narx/holat/manzil
   -> DRAFT saqlash yoki Moderatsiyaga yuborish
   -> PENDING_MODERATION -> (APPROVED -> Telegram post | REJECTED -> sabab + tahrirlash)
   -> Statistika (ko'rishlar, sevimlilar, telefon ochilishi)
   -> SOLD deb belgilash | Uzaytirish | Arxivlash
```

### 0.5 Admin flow

```
Login (/admin) -> Dashboard (KPI + chartlar)
   -> Moderatsiya navbati -> Product preview -> Approve / Reject(sabab)
   -> Approve -> Celery task -> Telegram kanalga post -> TelegramPost(status=published)
   -> Kategoriya/Atribut/Brend boshqaruvi
   -> Userlar / rollar / ban
   -> Shikoyatlar -> qaror
   -> Telegram sozlamalari (shablon, kanal, auto-publish)
   -> Audit log
```

### 0.6 Product lifecycle

```
DRAFT --submit--> PENDING_MODERATION --approve--> APPROVED --+--> SOLD
  ^                     |                            |        +--> RESERVED --> APPROVED|SOLD
  |                     +--reject--> REJECTED        |        +--> ARCHIVED (seller)
  +------edit-----------------------------+          |        +--> EXPIRED (30 kun, Celery)
                                                     +--edit(muhim maydon)--> PENDING_MODERATION
```

### 0.7 Moderation lifecycle

```
Product.submit() -> ModerationTask(status=pending, assignee=null)
   -> Moderator oladi (assignee=me, status=in_review)
   -> Approve: Product.APPROVED + published_at + expires_at + AuditLog + Notification + TelegramTask
   -> Reject: Product.REJECTED + reason + comment + AuditLog + Notification
   -> Seller tahrirlaydi -> qayta PENDING
```

### 0.8 Telegram lifecycle

```
Product APPROVED
   -> signal -> publish_product_to_telegram.delay(product_id)
   -> TelegramPost(status=PENDING) yaratiladi
   -> Shablon render (title, price, condition, specs, location, url)
   -> Media: 1 rasm=sendPhoto | 2+=sendMediaGroup | video=sendVideo
   -> OK   -> status=PUBLISHED, message_id saqlanadi
   -> XATO -> status=FAILED, error saqlanadi, 3 marta retry (exponential backoff)
   -> Product SOLD -> editMessageCaption("SOTILDI")
   -> Admin panelda: qayta jo'natish / o'chirish
```

### 0.9 Media lifecycle

```
Upload (multipart) -> MIME + hajm + kengaytma validatsiya (magic bytes)
   -> ProductImage/ProductVideo yaratiladi
   -> Celery: process_image -> EXIF tozalash -> WebP -> 3 o'lcham (thumb/medium/large)
   -> is_primary tanlash, order (drag&drop)
   -> Video: hajm + davomiylik + MIME validatsiya, poster frame
   -> O'chirish: soft delete -> fayl fonda o'chiriladi
```

### 0.10 Authentication lifecycle

```
Register(phone) -> OTP yuboriladi (dev: konsol/Telegram) -> verify -> User(is_phone_verified)
Login(phone,password) -> access(15 daqiqa, memory) + refresh(7 kun, httpOnly cookie)
Refresh -> yangi access + refresh rotation + eski refresh blacklist
Logout -> refresh blacklist + cookie o'chirish
Parolni tiklash -> OTP -> yangi parol -> barcha refresh blacklist
```

---

## PHASES

Har bir Phase: **maqsad -> vazifalar -> texnik ishlar -> acceptance criteria -> test criteria**

---

### Phase 0 — Requirements & Analysis
- **Maqsad:** Talablarni aniqlash, qarorlarni qayd etish.
- **Vazifalar:** 60 ta savol -> javoblar -> qarorlar jadvali.
- **Texnik:** ROADMAP.md, TASKS.md, ARCHITECTURE.md yaratish.
- **Acceptance:** Barcha qarorlar hujjatlashtirilgan.
- **Test:** Hujjatlar mavjud va o'qiladi.

### Phase 1 — Project architecture & scaffolding
- **Maqsad:** Backend/frontend skeleti, muhit sozlamalari.
- **Vazifalar:** venv, Django project, apps strukturasi, .env, git init.
- **Texnik:** `config/settings/{base,dev,prod}.py`, `apps/core` (BaseModel, TimeStamped, SoftDelete), django-environ.
- **Acceptance:** `manage.py check` xatosiz; `runserver` ko'tariladi.
- **Test:** `/api/v1/health/` -> 200 OK.

### Phase 2 — Database & core models
- **Maqsad:** PostgreSQL ulanish, baza abstraksiyalari.
- **Vazifalar:** DB connection, BaseModel, audit maydonlari, indexlar.
- **Texnik:** psycopg3, pg_trgm/unaccent, `UUIDModel`, `TimeStampedModel`, `SoftDeleteModel`, `AuditableModel`.
- **Acceptance:** `migrate` muvaffaqiyatli.
- **Test:** `dbshell` ulanadi, jadvallar mavjud.

### Phase 3 — Authentication (JWT)
- **Maqsad:** Telefon asosida ro'yxat/kirish.
- **Vazifalar:** Custom User (phone USERNAME_FIELD), OTP, JWT, cookie refresh.
- **Texnik:** SimpleJWT, rotation + blacklist, httpOnly cookie, throttling.
- **Acceptance:** register/verify/login/refresh/logout/me endpointlari ishlaydi.
- **Test:** pytest — auth testlari; noto'g'ri OTP, muddati o'tgan token, rate limit.

### Phase 4 — RBAC roles & permissions
- **Maqsad:** Granular ruxsatlar tizimi.
- **Vazifalar:** Role, Permission, RolePermission modellari; DRF permission classlari.
- **Texnik:** `HasPermission('product.approve')`, obyekt darajasida `IsOwnerOrReadOnly`.
- **Acceptance:** 5 ta default rol seed qilinadi; ruxsatsiz endpoint 403.
- **Test:** Har rol uchun matritsa testi (kirish/rad).

### Phase 5 — Catalog (categories, brands, attributes)
- **Maqsad:** Dinamik kategoriya daraxti va spec arxitekturasi.
- **Vazifalar:** Category (self-FK tree), Brand, AttributeDefinition, AttributeOption.
- **Texnik:** slug, tree helpers, `is_filterable`, `is_required`, data types (text/int/decimal/bool/select/multiselect).
- **Acceptance:** Admin yangi kategoriya + atribut qo'sha oladi, forma avtomatik o'zgaradi.
- **Test:** Tree endpoint, atributlar kategoriya bo'yicha meros oladi.

### Phase 6 — Product system
- **Maqsad:** E'lon CRUD + status mashinasi.
- **Vazifalar:** Product modeli, specs JSONB, status transitions, ishlatilgan mahsulot maydonlari.
- **Texnik:** GIN index (specs, search_vector), slug generatsiya, `quantity`, `is_negotiable`, `price_on_request`, `is_exchange_possible`, `expires_at`.
- **Acceptance:** Seller e'lon yaratadi -> PENDING; noto'g'ri status o'tishi bloklanadi.
- **Test:** CRUD, permission, status machine, validatsiya testlari.

### Phase 7 — Media system
- **Maqsad:** Professional rasm/video tizimi.
- **Vazifalar:** Upload API, validatsiya, optimizatsiya, tartiblash, primary.
- **Texnik:** magic-bytes MIME check, 10 rasm x 10MB, 2 video x 50MB, WebP + 3 o'lcham, Celery.
- **Acceptance:** Rasm yuklanadi, thumbnail yaratiladi, tartib o'zgaradi.
- **Test:** Katta fayl -> aniq xato xabari; soxta MIME -> rad; limitdan oshiq -> rad.

### Phase 8 — Search
- **Maqsad:** Tez va bardoshli qidiruv.
- **Vazifalar:** Full-text search, trigram (opechatka), autocomplete, qidiruv tarixi.
- **Texnik:** `SearchVectorField` + GIN, `SearchRank`, `TrigramSimilarity`.
- **Acceptance:** "asus rog" -> tegishli natijalar; "asuss" -> ham topadi.
- **Test:** 120 mock e'londa relevantlik va < 200ms javob.

### Phase 9 — Filters & sorting
- **Maqsad:** Dinamik filtrlash.
- **Vazifalar:** Kategoriya/narx/brend/holat/manzil/sotuvchi + dinamik spec filtrlari; 6 xil sorting.
- **Texnik:** django-filter + JSONB so'rovlari, facet count.
- **Acceptance:** Kategoriya tanlanganda faqat o'sha kategoriya filtrlari chiqadi.
- **Test:** Kombinatsiyalangan filtr + pagination + sort testlari.

### Phase 10 — Moderation
- **Maqsad:** Moderatsiya navbati.
- **Vazifalar:** ModerationTask, approve/reject, sabablar ro'yxati, qayta moderatsiya.
- **Texnik:** Bulk approve, assignment, muhim maydon o'zgarishini aniqlash.
- **Acceptance:** Approve -> Telegram task; Reject -> sabab + notification.
- **Test:** To'liq lifecycle testi.

### Phase 11 — Favorites / Compare / Reports
- **Maqsad:** Xaridor vositalari.
- **Vazifalar:** Favorite, Compare, Report (6 sabab).
- **Texnik:** Unique constraint, denormalized `favorites_count`.
- **Acceptance:** Sevimli qo'shiladi/o'chiriladi, shikoyat adminda ko'rinadi.
- **Test:** Takroriy sevimli -> 1 ta yozuv; anonim -> 401.

### Phase 12 — Notifications
- **Maqsad:** Ko'p kanalli bildirishnoma.
- **Vazifalar:** Notification modeli, in-app + Telegram + Email; o'qilgan/o'qilmagan.
- **Texnik:** `NotificationType` enum, shablonlar, Celery jo'natish, user sozlamalari.
- **Acceptance:** Approve/Reject -> user bildirishnoma oladi.
- **Test:** Har event uchun notification yaratilishi.

### Phase 13 — Telegram bot & channel automation
- **Maqsad:** Avtomatik kanal posti + bot.
- **Vazifalar:** TelegramSettings, TelegramPost, shablon renderer, publisher, bot handlerlari.
- **Texnik:** Bot API (requests), sendPhoto/sendMediaGroup/sendVideo, inline tugma, retry, mock rejim.
- **Acceptance:** APPROVED -> kanalga post; SOLD -> post tahrirlanadi.
- **Test:** Mock API bilan unit testlar + real kanalda qo'lda tekshirish.

### Phase 14 — Analytics & audit log
- **Maqsad:** Statistika va nazorat.
- **Vazifalar:** ProductView (unique/IP), AuditLog, dashboard aggregatlari.
- **Texnik:** Vaqt seriyali so'rovlar, indexlar, kunlik aggregatsiya taski.
- **Acceptance:** Dashboard raqamlari to'g'ri; admin harakati log qilinadi.
- **Test:** Ko'rish hisoblagichi takrorlanmaydi (24h TTL).

### Phase 15 — Admin API
- **Maqsad:** React admin panel uchun backend.
- **Vazifalar:** `/api/v1/admin/*` — users, products, moderation, reports, telegram, audit, stats.
- **Texnik:** Bulk actions, filtr, qidiruv, pagination, permission tekshiruvi.
- **Acceptance:** Barcha admin endpointlari himoyalangan.
- **Test:** Oddiy user admin endpointga -> 403.

### Phase 16 — Mock data / seeding
- **Maqsad:** Real ko'rinishdagi demo ma'lumot.
- **Vazifalar:** 25 kategoriya, 30 brend, 40 user, 20 sotuvchi, ~120 e'lon, rasmlar.
- **Texnik:** `seed` management command, ochiq manbalardan rasm + SVG fallback.
- **Acceptance:** `manage.py seed` — sayt to'la ko'rinadi.
- **Test:** Barcha status/kategoriya/holat qamrab olingan.

### Phase 17 — Frontend foundation
- **Maqsad:** Vite + Tailwind + design system.
- **Vazifalar:** Vite scaffold, Tailwind config, design tokenlar, router, API client, auth store.
- **Texnik:** axios interceptor (401 -> refresh), TanStack Query, dark mode, i18n (uz/ru/en).
- **Acceptance:** `npm run build` xatosiz; dark mode ishlaydi.
- **Test:** Build + lint toza.

### Phase 18 — Frontend core components
- **Maqsad:** Qayta ishlatiladigan komponentlar.
- **Vazifalar:** Navbar, SearchBar, CategoryMenu, ProductCard, ProductGrid, Gallery, VideoPlayer, FilterSidebar, FilterDrawer, Pagination, Price, Badge, Modal, Toast, Skeleton, EmptyState, ErrorState, Footer, BottomNav.
- **Texnik:** A11y (klaviatura, ARIA), responsive, skeleton loading.
- **Acceptance:** Barcha komponentlar mobil va desktopda to'g'ri.
- **Test:** Vitest — muhim komponentlar; browserda vizual tekshiruv.

### Phase 19 — Home page
- **Maqsad:** Konversiyaga yo'naltirilgan bosh sahifa.
- **Vazifalar:** Hero+search, kategoriyalar, tanlangan/yangi/ommabop/ishlatilgan bloklari, CTA, footer.
- **Acceptance:** Mobil 360px da muammosiz, LCP maqbul.
- **Test:** Browser + responsive tekshiruv.

### Phase 20 — Catalog / search / filter pages
- **Maqsad:** Katalog sahifasi.
- **Vazifalar:** URL-sinxron filtrlar, drawer (mobil), sorting, pagination, natija yo'q holati.
- **Acceptance:** Filtr URL'da saqlanadi, sahifa yangilanganda tiklanadi.
- **Test:** Deep-link, orqaga tugmasi, debounce.

### Phase 21 — Product detail page
- **Maqsad:** Professional mahsulot sahifasi.
- **Vazifalar:** Gallery+lightbox, video, spec jadvali, sotuvchi kartasi, telefon ochish, share, report, o'xshash mahsulotlar.
- **Acceptance:** Barcha ma'lumot ko'rinadi, telefon rate-limit bilan ochiladi.
- **Test:** Browser flow testi.

### Phase 22 — Auth pages & profile
- **Maqsad:** Kirish/ro'yxat/profil.
- **Vazifalar:** Register+OTP, login, parol tiklash, profil, avatar, sozlamalar.
- **Acceptance:** Token avtomatik yangilanadi, sahifa yangilanganda sessiya saqlanadi.
- **Test:** To'liq auth flow browserda.

### Phase 23 — Seller cabinet
- **Maqsad:** Sotuvchi kabineti.
- **Vazifalar:** E'lon yaratish sehrgari (wizard), media drag&drop, mening e'lonlarim, statistika, do'kon profili.
- **Acceptance:** E'lon yaratish 4 qadamda tugaydi, DRAFT saqlanadi.
- **Test:** Yaratish -> moderatsiya -> tasdiqlash oqimi.

### Phase 24 — Admin panel (React)
- **Maqsad:** Qulay admin interfeysi.
- **Vazifalar:** Dashboard+chartlar, moderatsiya navbati, jadval (filtr/qidiruv/bulk), userlar, kategoriya/atribut CRUD, Telegram, shikoyat, audit.
- **Acceptance:** O'chirishdan oldin tasdiqlash; barcha amallar toast bilan.
- **Test:** Browserda to'liq admin flow.

### Phase 25 — SEO
- **Maqsad:** Public sahifalar qidiruv tizimlariga tayyor.
- **Vazifalar:** Dinamik meta, OG, Twitter card, canonical, JSON-LD (Product/Offer/BreadcrumbList), sitemap.xml, robots.txt, prerender.
- **Acceptance:** Bot User-Agent uchun to'liq meta qaytadi.
- **Test:** curl bilan meta tekshiruvi, structured data validatsiya.

### Phase 26 — Security hardening
- **Maqsad:** Production darajasidagi xavfsizlik.
- **Vazifalar:** CORS/CSRF, rate limit, brute-force, fayl xavfsizligi, secrets, security headers, permission audit.
- **Acceptance:** SECURITY.md checklisti toza.
- **Test:** Maqsadli xavfsizlik testlari (IDOR, privilege escalation, upload bypass).

### Phase 27 — Testing
- **Maqsad:** Avtomatik testlar.
- **Vazifalar:** pytest (~70% backend), Vitest (frontend), API smoke suite.
- **Acceptance:** Barcha testlar yashil.
- **Test:** `pytest` + `npm test` + `npm run build`.

### Phase 28 — Performance
- **Maqsad:** Tezlik.
- **Vazifalar:** select_related/prefetch, indexlar, caching, pagination, lazy loading, code splitting, rasm optimizatsiya.
- **Acceptance:** Katalog so'rovi kam sonli SQL query; bundle maqbul hajmda.
- **Test:** Query count testlari, build analizi.

### Phase 29 — Deployment
- **Maqsad:** Serverga chiqarish hujjati.
- **Vazifalar:** DEPLOYMENT.md, nginx/gunicorn/systemd/celery konfiglari, docker-compose, SSL.
- **Acceptance:** Hujjat bo'yicha toza serverda ko'tarish mumkin.
- **Test:** Konfiglar sintaksis tekshiruvi.

### Phase 30 — Final QA
- **Maqsad:** Yakuniy tekshiruv.
- **Vazifalar:** FINAL QA checklisti (TASKS.md oxirida).
- **Acceptance:** Barcha band `[x]`.
- **Test:** Browserda to'liq end-to-end oqim.
