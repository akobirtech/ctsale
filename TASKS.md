# CT Sale — TASKS

> Doimiy progress tracker. Bajarilgan task hech qachon o'chirilmaydi, faqat `[x]` qilinadi.
> Oxirgi yangilanish: 2026-09-20

**Progress:** Phase 5 / 30 (auth + RBAC ishlaydi, katalog boshlandi)

---

## Phase 0 — Requirements & Analysis

- [x] 60 bo'limli savollar ro'yxati tayyorlandi
- [x] Foydalanuvchi javoblari olindi (DB, Telegram token, sayt nomi "CT Sale")
- [x] Qolgan qarorlar default tavsiyalar asosida qabul qilindi
- [x] PostgreSQL 16 mavjudligi tekshirildi (service: postgresql-x64-16, Running)
- [x] PostgreSQL ulanishi tekshirildi (user=postgres)
- [x] `ctsale` bazasi yaratildi
- [x] `pg_trgm` va `unaccent` kengaytmalari o'rnatildi
- [x] Telegram bot tokeni tekshirildi (@notbuk_sot_bot, )
- [x] ROADMAP.md yaratildi (project analysis + 31 phase)
- [x] TASKS.md yaratildi
- [x] ARCHITECTURE.md yaratildi
- [ ] Telegram kanal ID olinadi (foydalanuvchidan kutilmoqda — bloklamaydi)

---

## Phase 0.5 — Qo'shimcha majburiy talablar (2026-09-20 da qo'shildi)

Foydalanuvchi qo'shimcha talablar ro'yxatini yubordi. Arxitekturaga
ta'sir qilganlari migration qilishdan OLDIN kiritildi.

- [x] Argon2id parol hashlash yoqildi (PBKDF2 o'rniga)
- [x] `apps.seo` ilovasi yaratildi (SeoSettings, SeoRedirect, StaticPageSeo)
- [x] Content-Security-Policy + Permissions-Policy + COOP/CORP middleware
- [x] Xavfsiz fayl nomi generatsiyasi (path traversal himoyasi)
- [x] SEO-friendly rasm fayl nomlari (`slug-a7f3c1.webp`)
- [x] Product SEO maydonlari (seo_title/description/keywords, og_*, is_indexable)
- [x] `previous_slugs` — slug o'zgarganda 301 uchun
- [x] Til prefiksli URL arxitekturasi qaroriga ko'chirildi (`/uz/product/{slug}`)
- [x] `schema_availability` / `schema_condition` (JSON-LD uchun)
- [x] Google/Yandex/Bing verification kodlari `.env` ga ko'chirildi
- [ ] Vite SSR (React renderToString + Express) — Phase 17 da
- [ ] Dinamik robots.txt (baza asosida)
- [ ] Dinamik multilingual sitemap (/sitemap.xml, /sitemap-{uz,ru,en}.xml)
- [ ] hreflang + x-default barcha public sahifalarda
- [ ] JSON-LD: Product, Offer, BreadcrumbList, Organization, WebSite, SearchAction
- [ ] 301 redirect middleware (SeoRedirect modeli asosida)
- [ ] 410 Gone — o'chirilgan mahsulot uchun
- [ ] Multilingual 404 sahifasi
- [ ] Sotilgan mahsulot uchun SEO strategiyasi (200 + SoldOut)

**Qabul qilingan arxitektura qarori:** React + Vite saqlanadi, lekin
sof CSR o'rniga **Vite SSR** ishlatiladi. Sabab: talab #15 "product
ma'lumoti source HTML ichida bo'lsin" deydi. User-Agent bo'yicha
ajratish (crawler'ga boshqa kontent) ishlatilmaydi — Google buni
cloaking deb baholashi mumkin.

---

## Phase 1 — Project architecture & scaffolding

- [x] Loyiha papka strukturasi (backend / frontend / docs)
- [x] Python virtualenv yaratildi
- [x] requirements.txt yozildi
- [x] Barcha Python dependency'lar o'rnatildi (Django 5.1.6)
- [x] Django project `config` yaratildi
- [x] Settings bo'lindi: base / dev / prod
- [x] django-environ sozlandi
- [x] `.env` yaratildi (real qiymatlar bilan)
- [x] `.env.example` yaratildi (sirlarsiz)
- [x] `.gitignore` yaratildi
- [x] `apps/core` — BaseModel, TimeStampedModel, SoftDeleteModel, UUIDModel
- [x] `apps/core` — pagination, exception handler, response formatlar
- [x] REST_FRAMEWORK sozlamalari (auth, throttle, pagination, filter)
- [x] CORS sozlandi
- [x] drf-spectacular (OpenAPI) sozlandi
- [x] Health check endpoint `/api/v1/health/`
- [x] Celery ilovasi sozlandi (EAGER fallback bilan)
- [x] Logging sozlandi
- [x] `manage.py check` xatosiz o'tdi
- [x] `runserver` ishga tushdi va tekshirildi
- [x] git init + birinchi commit

---

## Phase 2 — Database & core models

- [x] PostgreSQL connection settings (psycopg3)
- [x] Baza ulanishi Django orqali tekshirildi
- [x] Abstract modellar yozildi
- [x] Audit maydonlari (created_by / updated_by)
- [x] Soft delete manager
- [x] Birinchi migration yaratildi va qo'llandi
- [ ] DATABASE.md yozildi

---

## Phase 3 — Authentication (JWT)

- [x] Custom User modeli (phone USERNAME_FIELD)
- [x] UserProfile / Shop profili
- [x] OTP modeli va generatsiya
- [x] OTP yuborish servisi (dev: konsol + Telegram)
- [x] Register endpoint
- [x] OTP verify endpoint
- [x] Login endpoint (JWT)
- [x] Refresh endpoint (httpOnly cookie + rotation)
- [x] Logout endpoint (blacklist)
- [x] `/me` endpoint
- [x] Parolni tiklash oqimi
- [x] Parol validatsiyasi va hashing
- [x] Auth throttling (login 5/min, register 3/soat)
- [x] Brute-force himoyasi (LoginAttempt, 10 urinish / 15 daqiqa)
- [x] Barcha xato xabarlari o'zbekchaga o'girildi (DRF + parol validatorlari)
- [ ] Auth testlari (pytest)

---

## Phase 4 — RBAC roles & permissions

- [x] Permission modeli (kod asosida)
- [x] Role modeli
- [x] Role-Permission bog'lanishi
- [x] User-Role bog'lanishi
- [x] `HasPermission` DRF permission class
- [x] `IsOwnerOrReadOnly` object permission
- [x] Default rollar seed (SUPERADMIN/ADMIN/MODERATOR/SUPPORT/USER)
- [ ] Permission matritsasi testlari

---

## Phase 5 — Catalog

- [ ] Category modeli (self-FK tree, slug, icon, order)
- [ ] Category tree API
- [ ] Brand modeli (logo, slug)
- [ ] AttributeDefinition modeli (type, unit, filterable, required)
- [ ] AttributeOption modeli (select/multiselect uchun)
- [ ] Kategoriya bo'yicha atribut merosi
- [ ] Catalog admin API (CRUD)
- [ ] Catalog public API
- [ ] Catalog testlari

---

## Phase 6 — Product system

- [ ] Product modeli (barcha maydonlar)
- [ ] Ishlatilgan mahsulot maydonlari
- [ ] Status choices + transition validatsiyasi
- [ ] specs JSONB + GIN index
- [ ] Slug avtomatik generatsiya (unique)
- [ ] Spec validatsiyasi (AttributeDefinition ga qarab)
- [ ] Product CRUD API (seller)
- [ ] Product public API (list/detail)
- [ ] Submit / Sold / Reserve / Archive / Renew action'lari
- [ ] E'lon muddati (expires_at) va Celery expiry task
- [ ] Product testlari

---

## Phase 7 — Media system

- [ ] ProductImage modeli
- [ ] ProductVideo modeli
- [ ] MIME / magic-bytes validatsiya
- [ ] Hajm va son limitlari
- [ ] Upload API (multipart)
- [ ] Celery: rasm optimizatsiya (WebP + 3 o'lcham)
- [ ] EXIF tozalash
- [ ] is_primary va order boshqaruvi
- [ ] Video validatsiya + poster
- [ ] Media o'chirish (fayl bilan)
- [ ] Aniq xato xabarlari (o'zbekcha)
- [ ] Media testlari

---

## Phase 8 — Search

- [ ] search_vector maydoni + GIN index
- [ ] Vektorni yangilash (signal/save)
- [ ] Full-text search endpoint
- [ ] Trigram fallback (opechatka)
- [ ] Autocomplete endpoint
- [ ] Qidiruv tarixi (SearchQuery log)
- [ ] Search testlari

---

## Phase 9 — Filters & sorting

- [ ] ProductFilterSet (django-filter)
- [ ] Narx oralig'i / holat / brend / manzil filtrlari
- [ ] Dinamik spec filtrlari (JSONB)
- [ ] Facet count endpoint
- [ ] 6 xil sorting
- [ ] Pagination
- [ ] Filter testlari

---

## Phase 10 — Moderation

- [ ] ModerationTask modeli
- [ ] Reject sabablari ro'yxati
- [ ] Moderatsiya navbati API
- [ ] Approve action
- [ ] Reject action (sabab + izoh)
- [ ] Bulk approve
- [ ] Muhim maydon o'zgarganda qayta moderatsiya
- [ ] Moderation testlari

---

## Phase 11 — Favorites / Compare / Reports

- [ ] Favorite modeli + API
- [ ] favorites_count denormalizatsiya
- [ ] Compare API
- [ ] Report modeli (6 sabab) + API
- [ ] Admin report ko'rish
- [ ] Testlar

---

## Phase 12 — Notifications

- [ ] Notification modeli
- [ ] NotificationType enum va shablonlar
- [ ] In-app API (list / unread count / mark read)
- [ ] Telegram kanali orqali yuborish
- [ ] Email backend (dev: konsol)
- [ ] User notification sozlamalari
- [ ] Testlar

---

## Phase 13 — Telegram

- [ ] TelegramSettings modeli (admin boshqaradi)
- [ ] TelegramPost modeli (pending/published/failed)
- [ ] Bot API client (requests)
- [ ] Post shablon renderer
- [ ] sendPhoto / sendMediaGroup / sendVideo
- [ ] Inline tugma "Saytda ko'rish"
- [ ] APPROVED signal -> Celery publish task
- [ ] Retry + xato saqlash
- [ ] SOLD -> post tahrirlash
- [ ] Mock rejim (token yo'q bo'lsa)
- [ ] Bot handlerlari (/start, qidiruv, mening e'lonlarim)
- [ ] Admin panelda qayta jo'natish
- [ ] TELEGRAM.md hujjati
- [ ] Telegram testlari (mock)

---

## Phase 14 — Analytics & audit

- [ ] ProductView modeli (unique 24h)
- [ ] PhoneReveal hisoblagichi
- [ ] AuditLog modeli
- [ ] Audit signal/mixin
- [ ] Dashboard statistika endpointi
- [ ] Testlar

---

## Phase 15 — Admin API

- [ ] Admin users endpoint
- [ ] Admin products endpoint
- [ ] Admin moderation endpoint
- [ ] Admin reports endpoint
- [ ] Admin telegram endpoint
- [ ] Admin audit endpoint
- [ ] Admin stats endpoint
- [ ] Bulk actions
- [ ] Permission testlari

---

## Phase 16 — Mock data

- [ ] Kategoriya daraxti seed (25+)
- [ ] Brendlar seed (30+)
- [ ] Atributlar seed (kategoriyalar bo'yicha)
- [ ] Userlar seed (40)
- [ ] Sotuvchilar seed (20)
- [ ] ~120 mahsulot seed
- [ ] Demo rasmlar (ochiq manba yoki SVG placeholder)
- [ ] `manage.py seed` komandasi
- [ ] Seed tekshiruvi

---

## Phase 17 — Frontend foundation

- [ ] Vite + React scaffold
- [ ] Tailwind sozlandi
- [ ] Design tokenlar (rang, typography, spacing, radius, shadow)
- [ ] Dark mode
- [ ] Router
- [ ] API client + interceptor
- [ ] Auth store
- [ ] TanStack Query
- [ ] i18n (uz/ru/en)
- [ ] `npm run build` toza

---

## Phase 18 — Frontend components

- [ ] Navbar
- [ ] SearchBar (debounce + autocomplete)
- [ ] CategoryMenu (mega menu)
- [ ] ProductCard
- [ ] ProductGrid
- [ ] ProductGallery + Lightbox
- [ ] VideoPlayer
- [ ] FilterSidebar
- [ ] FilterDrawer (mobil)
- [ ] Pagination
- [ ] Price
- [ ] Badge
- [ ] Modal
- [ ] Toast
- [ ] LoadingSkeleton
- [ ] EmptyState
- [ ] ErrorState
- [ ] Footer
- [ ] BottomNav (mobil)

---

## Phase 19 — Home page

- [ ] Hero + qidiruv
- [ ] Kategoriyalar bloki
- [ ] Tanlangan mahsulotlar
- [ ] Yangi mahsulotlar
- [ ] Ommabop mahsulotlar
- [ ] Ishlatilgan mahsulotlar
- [ ] CTA bloki
- [ ] Footer
- [ ] Responsive tekshiruv

---

## Phase 20 — Catalog page

- [ ] Katalog layout
- [ ] URL-sinxron filtrlar
- [ ] Sorting
- [ ] Pagination
- [ ] Skeleton loading
- [ ] Empty state
- [ ] Mobil filter drawer
- [ ] Responsive tekshiruv

---

## Phase 21 — Product detail page

- [ ] Gallery + lightbox
- [ ] Video player
- [ ] Sarlavha / narx / holat
- [ ] Spec jadvali
- [ ] Tavsif
- [ ] Sotuvchi kartasi
- [ ] Telefonni ko'rsatish
- [ ] Share
- [ ] Report modal
- [ ] O'xshash mahsulotlar
- [ ] Ko'rishlar / sevimlilar
- [ ] Responsive tekshiruv

---

## Phase 22 — Auth pages & profile

- [ ] Register sahifasi + OTP
- [ ] Login sahifasi
- [ ] Parolni tiklash
- [ ] Profil sahifasi
- [ ] Avatar yuklash
- [ ] Sevimlilar sahifasi
- [ ] Bildirishnomalar sahifasi
- [ ] Sozlamalar

---

## Phase 23 — Seller cabinet

- [ ] E'lon yaratish wizard (4 qadam)
- [ ] Dinamik spec forma
- [ ] Media drag & drop
- [ ] Mening e'lonlarim (status bo'yicha)
- [ ] E'lon tahrirlash
- [ ] Statistika
- [ ] Do'kon profili
- [ ] Rad etilgan e'lon sababi ko'rinishi

---

## Phase 24 — Admin panel

- [ ] Admin layout + sidebar
- [ ] Dashboard + chartlar
- [ ] Moderatsiya navbati
- [ ] Mahsulotlar jadvali (filtr/qidiruv/bulk)
- [ ] Foydalanuvchilar
- [ ] Rollar va ruxsatlar
- [ ] Kategoriya CRUD
- [ ] Atribut CRUD
- [ ] Brend CRUD
- [ ] Telegram sozlamalari + postlar
- [ ] Shikoyatlar
- [ ] Audit log
- [ ] Confirmation modal + toast

---

## Phase 25 — SEO

- [ ] Dinamik meta teglar
- [ ] Open Graph + Twitter card
- [ ] Canonical
- [ ] JSON-LD (Product, Offer, BreadcrumbList, Organization)
- [ ] sitemap.xml
- [ ] robots.txt
- [ ] Clean URL `/products/{slug}`
- [ ] Bot uchun prerender/meta injection

---

## Phase 26 — Security

- [ ] CORS / CSRF sozlamalari
- [ ] Security headerlar
- [ ] Rate limiting (barcha kritik endpoint)
- [ ] Brute-force himoya
- [ ] Fayl yuklash xavfsizligi
- [ ] Telefon raqam himoyasi
- [ ] JWT xavfsizligi
- [ ] Secrets menejment
- [ ] IDOR / privilege escalation tekshiruvi
- [ ] SECURITY.md

---

## Phase 27 — Testing

- [ ] pytest konfiguratsiyasi
- [ ] Auth testlari
- [ ] Permission testlari
- [ ] Product CRUD testlari
- [ ] Media testlari
- [ ] Search/filter testlari
- [ ] Moderation testlari
- [ ] Telegram testlari
- [ ] Frontend Vitest testlari
- [ ] TESTING.md

---

## Phase 28 — Performance

- [ ] Query optimizatsiya (select_related/prefetch_related)
- [ ] DB indexlar audit
- [ ] Caching (Redis yoki locmem)
- [ ] Frontend code splitting
- [ ] Lazy loading rasmlar
- [ ] Bundle analizi

---

## Phase 29 — Deployment

- [ ] docker-compose.yml
- [ ] Dockerfile (backend / frontend)
- [ ] nginx konfiguratsiyasi
- [ ] gunicorn + systemd
- [ ] celery + systemd
- [ ] DEPLOYMENT.md
- [ ] .env.example to'liq

---

## Phase 30 — FINAL QA

- [ ] Frontend build
- [ ] Backend tests
- [ ] API tests
- [ ] Authentication test
- [ ] Role test
- [ ] Product CRUD
- [ ] Media upload
- [ ] Multiple images
- [ ] Video upload
- [ ] Search
- [ ] Filters
- [ ] Favorites
- [ ] Seller
- [ ] Admin
- [ ] Moderation
- [ ] Telegram bot
- [ ] Telegram channel
- [ ] Telegram auto publish
- [ ] Error handling
- [ ] Responsive
- [ ] Security
- [ ] Performance
- [ ] SEO
- [ ] Documentation
