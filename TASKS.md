# CT Sale — TASKS

> Doimiy progress tracker. Bajarilgan task hech qachon o'chirilmaydi, faqat `[x]` qilinadi.
> Oxirgi yangilanish: 2026-09-20

**Progress:** Phase 29 / 30 (hujjatlar va deployment tayyor; qolgani: performance, final QA, Gemini AI)

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
- [x] Telegram kanal ID olindi va ulandi (@notbuk_sot / -1004327935486)

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
- [x] Vite SSR (React renderToString + Express) — Phase 17 da
- [x] Dinamik robots.txt (baza asosida)
- [x] Dinamik multilingual sitemap (/sitemap.xml, /sitemap-{uz,ru,en}.xml)
- [x] hreflang + x-default barcha public sahifalarda
- [x] JSON-LD: Product, Offer, BreadcrumbList, Organization, WebSite, SearchAction
- [ ] 301 redirect middleware (SeoRedirect modeli asosida)
- [ ] 410 Gone — o'chirilgan mahsulot uchun
- [x] Multilingual 404 sahifasi
- [x] Sotilgan mahsulot uchun SEO strategiyasi (200 + SoldOut)

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
- [x] DATABASE.md yozildi

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
- [x] Auth testlari (pytest)

---

## Phase 4 — RBAC roles & permissions

- [x] Permission modeli (kod asosida)
- [x] Role modeli
- [x] Role-Permission bog'lanishi
- [x] User-Role bog'lanishi
- [x] `HasPermission` DRF permission class
- [x] `IsOwnerOrReadOnly` object permission
- [x] Default rollar seed (SUPERADMIN/ADMIN/MODERATOR/SUPPORT/USER)
- [x] `manage.py create_admin` komandasi
- [x] RBAC real HTTP orqali tekshirildi (403 -> rol berilgach 201)
- [x] Permission matritsasi testlari

---

## Phase 5 — Catalog

- [x] Category modeli (self-FK tree, slug, icon, order)
- [x] Category tree API
- [x] Brand modeli (logo, slug)
- [x] AttributeDefinition modeli (type, unit, filterable, required)
- [x] AttributeOption modeli (select/multiselect uchun)
- [x] Kategoriya bo'yicha atribut merosi
- [x] Catalog admin API (CRUD)
- [x] Catalog public API
- [x] Catalog testlari

---

## Phase 6 — Product system

- [x] Product modeli (barcha maydonlar)
- [x] Ishlatilgan mahsulot maydonlari
- [x] Status choices + transition validatsiyasi
- [x] specs JSONB + GIN index
- [x] Slug avtomatik generatsiya (unique)
- [x] Spec validatsiyasi (AttributeDefinition ga qarab)
- [x] Product CRUD API (seller)
- [x] Product public API (list/detail)
- [x] Submit / Sold / Reserve / Archive / Renew action'lari
- [x] E'lon muddati (expires_at) va Celery expiry task
- [x] Product testlari

---

## Phase 7 — Media system

- [x] ProductImage modeli
- [x] ProductVideo modeli
- [x] MIME / magic-bytes validatsiya
- [x] Hajm va son limitlari
- [x] Upload API (multipart)
- [x] Celery: rasm optimizatsiya (WebP + 3 o'lcham)
- [x] EXIF tozalash
- [x] is_primary va order boshqaruvi
- [x] Video validatsiya + poster
- [x] Media o'chirish (fayl bilan)
- [x] Aniq xato xabarlari (o'zbekcha)
- [x] Media testlari

---

## Phase 8 — Search

- [x] search_vector maydoni + GIN index
- [x] Vektorni yangilash (signal/save)
- [x] Full-text search endpoint
- [x] Trigram fallback (opechatka)
- [x] Autocomplete endpoint
- [x] Qidiruv tarixi (SearchQuery log)
- [x] Search testlari

---

## Phase 9 — Filters & sorting

- [x] ProductFilterSet (django-filter)
- [x] Narx oralig'i / holat / brend / manzil filtrlari
- [x] Dinamik spec filtrlari (JSONB)
- [x] Facet count endpoint
- [x] 6 xil sorting
- [x] Pagination
- [x] Filter testlari

---

## Phase 10 — Moderation

- [x] ModerationTask modeli
- [x] Reject sabablari ro'yxati
- [x] Moderatsiya navbati API
- [x] Approve action
- [x] Reject action (sabab + izoh)
- [x] Bulk approve
- [x] Muhim maydon o'zgarganda qayta moderatsiya
- [x] Moderation testlari

---

## Phase 11 — Favorites / Compare / Reports

- [x] Favorite modeli + API
- [x] favorites_count denormalizatsiya
- [x] Compare API
- [x] Report modeli (6 sabab) + API
- [x] Admin report ko'rish
- [x] Testlar

---

## Phase 12 — Notifications

- [x] Notification modeli
- [x] NotificationType enum va shablonlar
- [x] In-app API (list / unread count / mark read)
- [x] Telegram kanali orqali yuborish
- [x] Email backend (dev: konsol)
- [x] User notification sozlamalari
- [x] Testlar

---

## Phase 13 — Telegram

- [x] TelegramSettings modeli (admin boshqaradi)
- [x] TelegramPost modeli (pending/published/failed)
- [x] Bot API client (requests)
- [x] Post shablon renderer
- [x] sendPhoto / sendMediaGroup / sendVideo
- [x] Inline tugma "Saytda ko'rish"
- [x] APPROVED signal -> Celery publish task
- [x] Retry + xato saqlash
- [x] SOLD -> post tahrirlash
- [x] Mock rejim (token yo'q bo'lsa)
- [x] HAQIQIY kanalga post yuborildi va tekshirildi (t.me/notbuk_sot/4)
- [x] Ochiq bo'lmagan URL (localhost) uchun chidamli fallback
- [ ] Bot handlerlari (/start, qidiruv, mening e'lonlarim)
- [ ] Admin panelda qayta jo'natish
- [x] TELEGRAM.md hujjati
- [x] Telegram testlari (mock)

---

## Phase 14 — Analytics & audit

- [x] ProductView modeli (unique 24h)
- [x] PhoneReveal hisoblagichi
- [x] AuditLog modeli
- [x] Audit signal/mixin
- [x] Dashboard statistika endpointi
- [x] Testlar

---

## Phase 15 — Admin API

- [x] Admin users endpoint
- [ ] Admin products endpoint
- [x] Admin moderation endpoint
- [x] Admin reports endpoint
- [x] Admin telegram endpoint
- [x] Admin audit endpoint
- [x] Admin stats endpoint
- [x] Bulk actions
- [x] Permission testlari

---

## Phase 16 — Mock data

- [x] Kategoriya daraxti seed (25+)
- [x] Brendlar seed (30+)
- [x] Atributlar seed (kategoriyalar bo'yicha)
- [x] O'zbekiston hududlari seed (14 viloyat / 79 tuman)
- [x] Userlar seed (40)
- [x] Sotuvchilar seed (20)
- [x] ~120 mahsulot seed
- [x] Demo rasmlar (ochiq manba yoki SVG placeholder)
- [x] `manage.py seed` komandasi
- [x] Seed tekshiruvi
- [x] `manage.py recount` - hisoblagichlarni tiklash

---

## Phase 17 — Frontend foundation

- [x] Vite + React scaffold
- [x] Tailwind sozlandi
- [x] Design tokenlar (rang, typography, spacing, radius, shadow)
- [x] Dark mode
- [x] Router
- [x] API client + interceptor
- [x] Auth store
- [x] TanStack Query
- [x] i18n (uz/ru/en)
- [x] `npm run build` toza

---

## Phase 18 — Frontend components

- [x] Navbar
- [x] SearchBar (debounce + autocomplete)
- [ ] CategoryMenu (mega menu)
- [x] ProductCard
- [x] ProductGrid
- [x] ProductGallery + Lightbox
- [x] VideoPlayer
- [x] FilterSidebar
- [x] FilterDrawer (mobil)
- [x] Pagination
- [x] Price
- [x] Badge
- [x] Modal
- [x] Toast
- [x] LoadingSkeleton
- [x] EmptyState
- [x] ErrorState
- [x] Footer
- [x] BottomNav (mobil)

---

## Phase 19 — Home page

- [x] Hero + qidiruv
- [x] Kategoriyalar bloki
- [x] Tanlangan mahsulotlar
- [x] Yangi mahsulotlar
- [x] Ommabop mahsulotlar
- [x] Ishlatilgan mahsulotlar
- [x] CTA bloki
- [x] Footer
- [ ] Responsive tekshiruv

---

## Phase 20 — Catalog page

- [x] Katalog layout
- [x] URL-sinxron filtrlar
- [x] Sorting
- [x] Pagination
- [x] Skeleton loading
- [x] Empty state
- [x] Mobil filter drawer
- [ ] Responsive tekshiruv

---

## Phase 21 — Product detail page

- [x] Gallery + lightbox
- [x] Video player
- [x] Sarlavha / narx / holat
- [x] Spec jadvali
- [x] Tavsif
- [x] Sotuvchi kartasi
- [x] Telefonni ko'rsatish
- [x] Share
- [ ] Report modal
- [x] O'xshash mahsulotlar
- [x] Ko'rishlar / sevimlilar
- [ ] Responsive tekshiruv

---

## Phase 22 — Auth pages & profile

- [x] Register sahifasi + OTP
- [x] Login sahifasi
- [x] Parolni tiklash
- [x] Profil sahifasi
- [ ] Avatar yuklash
- [x] Sevimlilar sahifasi
- [ ] Bildirishnomalar sahifasi
- [x] Sozlamalar

---

## Phase 23 — Seller cabinet

- [x] E'lon yaratish wizard (4 qadam)
- [x] Dinamik spec forma
- [x] Media drag & drop
- [x] Mening e'lonlarim (status bo'yicha)
- [x] E'lon tahrirlash
- [ ] Statistika
- [ ] Do'kon profili
- [x] Rad etilgan e'lon sababi ko'rinishi

---

## Phase 24 — Admin panel

- [x] Admin layout + sidebar
- [x] Dashboard + chartlar
- [x] Moderatsiya navbati
- [ ] Mahsulotlar jadvali (filtr/qidiruv/bulk)
- [x] Foydalanuvchilar
- [x] Rollar va ruxsatlar
- [ ] Kategoriya CRUD
- [ ] Atribut CRUD
- [ ] Brend CRUD
- [x] Telegram sozlamalari + postlar
- [ ] Shikoyatlar
- [x] Audit log
- [x] Confirmation modal + toast

---

## Phase 25 — SEO

- [x] Dinamik meta teglar
- [x] Open Graph + Twitter card
- [x] Canonical
- [x] JSON-LD (Product, Offer, BreadcrumbList, Organization)
- [x] sitemap.xml
- [x] robots.txt
- [x] Clean URL `/products/{slug}`
- [x] Bot uchun prerender/meta injection

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
- [x] SECURITY.md

---

## Phase 27 — Testing

- [x] pytest konfiguratsiyasi
- [x] Auth testlari
- [x] Permission testlari
- [x] Product CRUD testlari
- [x] Media testlari
- [x] Search/filter testlari
- [x] Moderation testlari
- [x] Telegram testlari
- [ ] Frontend Vitest testlari
- [x] TESTING.md

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

- [x] docker-compose.yml
- [x] Dockerfile (backend / frontend)
- [x] nginx konfiguratsiyasi
- [x] gunicorn + systemd
- [x] celery + systemd
- [x] DEPLOYMENT.md
- [x] .env.example to'liq

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
