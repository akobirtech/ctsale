# Graph Report - items sell  (2026-09-21)

## Corpus Check
- 191 files · ~53,826 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 1, .example 1, .css 1)

## Summary
- 1361 nodes · 2743 edges · 139 communities (75 shown, 33 thin omitted)
- Extraction: 88% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 315 edges (avg confidence: 0.94)
- Token cost: 140,238 input · 0 output

## Community Hubs (Navigation)
- SEO App: Redirects & Indexing
- Interactions: Favorites, Views, Reports
- Product API Views & Search
- Accounts: OTP & Login Attempts
- Frontend Page Components
- Architecture Decision Records
- Seed & Admin Management Commands
- Product Model & Serializers
- Frontend Layout & Filter UI
- Auth Flow & Deployment Architecture
- Catalog Filtering & Faceting
- Denormalized Counters & Audit Base
- Notifications Delivery
- Catalog Seed Data & Models
- Product Status State Machine
- User & ShopProfile Models
- Moderation Task Model
- Frontend App Shell & Hydration
- Product Card & Gallery UI
- Auth Serializers & Throttling
- Uzbek Password Validators
- Telegram Bot API Client
- Navbar, Search & i18n
- Analytics: Audit Log & Daily Stats
- Catalog API Endpoints
- Catalog Serializers
- Moderation Queue Views
- Telegram Publishing Service
- Telegram Client & Post Models
- Frontend Package Manifest
- Catalog Seeding Command
- Category Tree API
- Soft-Delete Model Layer
- Safe Media Paths & Migrations
- Media Upload Views & Limits
- Frontend API Client & Endpoints
- Form Fields & Toast UI
- User Profile Serializers
- Category Hierarchy Model
- RBAC Permission Classes
- Telegram Celery Tasks
- Frontend Dev Dependencies
- Media File Serializers
- Magic-Bytes File Validation
- Security Headers Middleware
- Frontend Runtime Dependencies
- Attribute Definition Schema
- ProductImage & ProductVideo Models
- Demo Product Seeder
- Registration & Password Reset
- Image Optimization Celery Tasks
- Media Routing & Mixins
- SSR Express Server
- Health Check Endpoint
- Password Change Flow
- Localized DRF Error Messages
- Product Filter Set
- Django Settings Environments
- Frontend Build Scripts
- Token Refresh & Logout Views
- SSR and SEO Strategy Decisions
- Notification Preferences
- Saved Search & Query Log
- Unified API Exception Handler
- Custom User Manager
- Pagination Classes
- Product QuerySet Scopes
- CT Sale Brand Mark
- Spec Validation Against Schema
- Celery App Bootstrap
- Multilingual URL & Sitemap
- Telegram Bot User Model
- Telegram HTML Spec Rendering
- Telegram Inline Button Links
- Django manage.py Entry
- Skeleton Loading UI
- Vite Build Config
- Design Tokens & Web Font
- Accounts App Config
- OTP Resend Endpoint
- AdminAPI App Config
- Analytics App Config
- Catalog App Config
- Interactions App Config
- Mediafiles App Config
- Moderation App Config
- Notifications App Config
- Products App Config
- RBAC App Config
- SEO App Config
- Telegrambot App Config
- Media Query Hooks
- Analytics Initial Migration
- Catalog Initial Migration
- Interactions Initial Migration
- Report Reason Migration
- Moderation Initial Migration
- Notifications Initial Migration
- Products Initial Migration
- Product Audit Fields Migration
- RBAC Initial Migration
- SEO Initial Migration
- Sold Product Indexing Migration
- Telegram Initial Migration
- ASGI Entry Point
- Root URL Router
- WSGI Entry Point
- Django & DRF Dependencies

## God Nodes (most connected - your core abstractions)
1. `Product` - 49 edges
2. `ProductViewSet` - 47 edges
3. `useI18n()` - 46 edges
4. `BusinessError` - 45 edges
5. `TimeStampedModel` - 42 edges
6. `Category` - 35 edges
7. `User` - 31 edges
8. `ProductStatus` - 27 edges
9. `useHead()` - 27 edges
10. `ProductCardSerializer` - 24 edges

## Surprising Connections (you probably didn't know these)
- `Magic-Bytes File Validation` --semantically_similar_to--> `Safe SEO-Friendly Filename Generation`  [INFERRED] [semantically similar]
  ARCHITECTURE.md → TASKS.md
- `SPA + Bot Meta Injection for SEO` --semantically_similar_to--> `No User-Agent Based Content Splitting`  [INFERRED] [semantically similar]
  ARCHITECTURE.md → TASKS.md
- `djangorestframework-simplejwt 5.4.0` --implements--> `JWT Auth Flow (memory access + httpOnly refresh)`  [INFERRED]
  backend/requirements.txt → ARCHITECTURE.md
- `Authentication Lifecycle` --conceptually_related_to--> `JWT Auth Flow (memory access + httpOnly refresh)`  [INFERRED]
  ROADMAP.md → ARCHITECTURE.md
- `Security Hardening Phase` --references--> `JWT Auth Flow (memory access + httpOnly refresh)`  [INFERRED]
  ROADMAP.md → ARCHITECTURE.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Phone-OTP + JWT Authentication Flow** — architecture_otp_verification, architecture_jwt_auth_flow, architecture_refresh_token_rotation, architecture_axios_refresh_interceptor, tasks_argon2id_hashing, tasks_brute_force_protection, roadmap_authentication_lifecycle [INFERRED 0.85]
- **Approval-to-Telegram Publication Flow** — roadmap_product_lifecycle, roadmap_moderation_lifecycle, architecture_telegram_publishing, architecture_telegram_mock_mode, architecture_media_pipeline, backend_requirements_celery, tasks_telegram_real_channel_verified [INFERRED 0.85]
- **SSR + Structured Data SEO Stack** — tasks_vite_ssr_decision, tasks_seo_app, tasks_json_ld_structured_data, tasks_dynamic_sitemap_robots, tasks_language_prefixed_urls, frontend_index_ssr_placeholders, roadmap_seo_requirements [INFERRED 0.85]
- **Dependency-free vector brand mark: indigo rounded square + centered CT text in system-ui** — frontend_public_favicon_ct_sale_favicon_mark, frontend_public_favicon_brand_indigo_4f46e5, frontend_public_favicon_ct_monogram, frontend_public_favicon_system_ui_font_stack, frontend_public_favicon_rounded_square_app_icon_pattern [INFERRED 0.85]

## Communities (139 total, 33 thin omitted)

### Community 0 - "SEO App: Redirects & Indexing"
Cohesion: 0.07
Nodes (48): Sahifa qidiruv tizimlari indeksiga tushsinmi? Sotilgan e'lon ham indekslanadi:…, Frontend `<head>` uchun tayyor ma'lumot (hreflang, OG, JSON-LD)., Meta, SEO konfiguratsiyasi, redirectlar va indeksatsiya nazorati. robots.txt va…, Eski URL -> yangi URL. Slug o'zgarganda SEO vaznini yo'qotmaslik uchun., Statik sahifalar (bosh sahifa, yordam, shartlar) uchun meta ma'lumot., Admin panelidan boshqariladigan sayt darajasidagi SEO sozlamalari., RedirectType (+40 more)

### Community 1 - "Interactions: Favorites, Views, Reports"
Cohesion: 0.06
Nodes (33): Favorite, Meta, PhoneReveal, ProductView, Foydalanuvchi va mahsulot o'rtasidagi harakatlar: sevimlilar, ko'rishlar,…, Mahsulot ko'rishlari. Bir foydalanuvchi/IP 24 soat ichida qayta ochsa yangi…, Telefon raqam ochilgani — sotuvchi uchun eng qimmatli metrika., Report (+25 more)

### Community 2 - "Product API Views & Search"
Cohesion: 0.08
Nodes (16): _hash_ip(), ProductViewSet, serialize(), action, Ro'yxatdagi qaysi mahsulot sevimlida — bitta so'rovda. Har karta uchun alohida…, Slug o'zgargan bo'lsa eski slug ham topilsin (301 uchun)., Ko'rishni hisoblash — 24 soat ichida takrorlanmaydi., Yaratgandan keyin to'liq obyektni qaytaramiz. Frontendga darhol `slug` kerak… (+8 more)

### Community 3 - "Accounts: OTP & Login Attempts"
Cohesion: 0.11
Nodes (30): Migration, LoginAttempt, OTPCode, OTPPurpose, Foydalanuvchi, do'kon profili va OTP modellari. Identifikator sifatida telefon…, Bir martalik tasdiqlash kodi. Kodning o'zi emas, SHA-256 hash'i saqlanadi: baza…, Brute-force aniqlash uchun kirish urinishlari jurnali., _assign_default_role() (+22 more)

### Community 4 - "Frontend Page Components"
Cohesion: 0.12
Nodes (26): AdminDashboardPage(), ModerationPage(), FavoritesPage(), NotFoundPage(), ProfilePage(), RegisterPage(), ProductFormPage(), SellerProductsPage() (+18 more)

### Community 5 - "Architecture Decision Records"
Cohesion: 0.06
Nodes (35): Abstract Base Models (TimeStamped/UUID/SoftDelete/Auditable), Celery EAGER Fallback, Core Relational Schema (User/Product/Category/Telegram), Hybrid EAV + JSONB Specification Architecture, GIN / Composite Index Strategy, Magic-Bytes File Validation, Media Upload and Optimization Pipeline, PostgreSQL Full-Text Search (not Elasticsearch) (+27 more)

### Community 6 - "Seed & Admin Management Commands"
Cohesion: 0.10
Nodes (19): Demo foydalanuvchilar va mahsulotlarni yaratadi. Rasmlar Pillow bilan…, R, Ruxsat kodlari va standart rollar. Bu yagona manba: yangi ruxsat qo'shish uchun…, Command, atomic, BaseCommand, Admin hisobini yaratadi yoki mavjudiga rol beradi., Command (+11 more)

### Community 7 - "Product Model & Serializers"
Cohesion: 0.08
Nodes (17): Condition, Currency, ProductManager, Mahsulot (e'lon) modeli va uning holat mashinasi., build_spec_display(), Meta, _option_label(), PriceMixin (+9 more)

### Community 8 - "Frontend Layout & Filter UI"
Cohesion: 0.18
Nodes (18): FilterPanel(), ScrollableOptions(), BottomNav(), Footer(), Layout(), ProductGrid(), EmptyState(), ErrorState() (+10 more)

### Community 9 - "Auth Flow & Deployment Architecture"
Cohesion: 0.07
Nodes (27): 401 Refresh-and-Retry Interceptor, CT Sale Overall Architecture, Deployment Stack (nginx/gunicorn/celery/systemd), Frontend Data Flow (TanStack Query → axios → /api/v1), JSON-only API Contract (/api/v1/), JWT Auth Flow (memory access + httpOnly refresh), Phone OTP Verification, Refresh Token Rotation and Blacklist (+19 more)

### Community 10 - "Catalog Filtering & Faceting"
Cohesion: 0.12
Nodes (18): AttributeType, apply_sort(), apply_spec_filters(), build_facets(), _is_number(), _numeric_compare(), Katalog filtrlari va saralash. Dinamik xususiyat filtrlari…, JSONB ichidagi sonni taqqoslash. PostgreSQL JSONB soni raqam sifatida… (+10 more)

### Community 11 - "Denormalized Counters & Audit Base"
Cohesion: 0.08
Nodes (12): Command, BaseCommand, Denormalizatsiya qilingan hisoblagichlarni qayta hisoblaydi. Mahsulot statusi…, AuditableModel, Kim yaratgani va kim oxirgi o'zgartirgani., Product, Til prefiksli to'liq URL: https://domain/uz/product/slug, Canonical URL — standart til (uz). (+4 more)

### Community 12 - "Notifications Delivery"
Cohesion: 0.15
Nodes (16): Meta, Notification, NotificationChannel, Meta, NotificationPreferenceSerializer, NotificationSerializer, _deliver(), mark_all_read() (+8 more)

### Community 13 - "Catalog Seed Data & Models"
Cohesion: 0.13
Nodes (18): Katalogning boshlang'ich ma'lumotlari. Seed komandasi shu yerdan o'qiydi. Admin…, Hudud, kategoriya, brend va xususiyatlarni bazaga yozadi (idempotent)., AttributeOption, Brand, District, Meta, Katalog: hudud, kategoriya daraxti, brend va dinamik atributlar. Spec…, SELECT / MULTISELECT turidagi xususiyat uchun variantlar. (+10 more)

### Community 14 - "Product Status State Machine"
Cohesion: 0.19
Nodes (24): InvalidStatusTransition, ProductStatus, approve_product(), _assert_transition(), _audit(), build_seo_metadata(), change_status(), _close_moderation_task() (+16 more)

### Community 15 - "User & ShopProfile Models"
Cohesion: 0.11
Nodes (12): AbstractBaseUser, Meta, +998901234567 -> +998 90 *** ** 67, RBAC tekshiruvi — Django permissionlaridan alohida., Do'kon / kompaniya sifatida sotuvchi profili (ixtiyoriy)., ShopProfile, User, PhoneField (+4 more)

### Community 16 - "Moderation Task Model"
Cohesion: 0.13
Nodes (13): Meta, ModerationStatus, ModerationTask, Har bir moderatsiyaga yuborish uchun alohida yozuv. Tarix saqlanadi: e'lon bir…, Sotuvchiga ko'rsatiladigan to'liq sabab., RejectReasonCode, BulkApproveSerializer, Meta (+5 more)

### Community 17 - "Frontend App Shell & Hydration"
Cohesion: 0.15
Nodes (14): App(), createQueryClient(), getQueryClient(), PageLoader(), initial, BACKSLASH, render(), serializeState() (+6 more)

### Community 18 - "Product Card & Gallery UI"
Cohesion: 0.18
Nodes (15): ProductCard(), ProductGallery(), Badge(), conditionTone(), TONES, useToast(), ProductPage(), revealPhone() (+7 more)

### Community 19 - "Auth Serializers & Throttling"
Cohesion: 0.19
Nodes (14): AnonRateThrottle, LoginSerializer, OTPVerifySerializer, PasswordResetConfirmSerializer, LoginThrottle, OTPThrottle, Auth endpointlari uchun so'rov chegaralari. Tezlik qiymatlari…, RegisterThrottle (+6 more)

### Community 20 - "Uzbek Password Validators"
Cohesion: 0.10
Nodes (9): Parol validatorlari — o'zbekcha xabarlar bilan. Django'ning standart…, Eng ko'p ishlatiladigan parollarni rad etadi., Kamida bitta harf va bitta raqam bo'lishini talab qiladi. Maxsus belgi majburiy…, Parol telefon raqam yoki ismga o'xshash bo'lmasin., UzCommonPasswordValidator, UzComplexityValidator, UzMinimumLengthValidator, UzNumericPasswordValidator (+1 more)

### Community 21 - "Telegram Bot API Client"
Cohesion: 0.15
Nodes (5): _brief(), Bir nechta rasm. Telegram bu usulda reply_markup qabul qilmaydi., Logda uzun matnlarni qisqartirish., Sozlanmagan bo'lsa yoki majburan mock yoqilgan bo'lsa., TelegramClient

### Community 22 - "Navbar, Search & i18n"
Cohesion: 0.16
Nodes (14): Navbar(), useDebounce(), DICTIONARIES, I18nContext, I18nProvider(), isSupported(), langFromPath(), LANGUAGE_LABELS (+6 more)

### Community 23 - "Analytics: Audit Log & Daily Stats"
Cohesion: 0.13
Nodes (16): AuditAction, AuditLog, DailyStat, Meta, Audit jurnali va kunlik statistika., Kim, nima qildi, qachon, qayerdan. O'zgartirib bo'lmaydigan jurnal: faqat…, Kunlik yig'ma ko'rsatkichlar. Dashboard har safar million qatorni sanamasligi…, diff_instance() (+8 more)

### Community 24 - "Catalog API Endpoints"
Cohesion: 0.15
Nodes (12): BrandSerializer, BrandViewSet, Katalog endpointlari. O'qish hammaga ochiq (SEO va mehmon foydalanuvchilar…, O'qish hammaga, o'zgartirish esa `write_permission` egasiga. `public_actions` —…, Viloyatlar va tumanlar., ReadWritePermissionMixin, RegionViewSet, P (+4 more)

### Community 25 - "Catalog Serializers"
Cohesion: 0.23
Nodes (11): AttributeDefinitionSerializer, AttributeOptionSerializer, CategoryBriefSerializer, CategorySerializer, DistrictSerializer, _language(), Meta, Katalog serializerlari. Ko'p tilli maydonlar (`name_uz/ru/en`) frontendga ikki… (+3 more)

### Community 26 - "Moderation Queue Views"
Cohesion: 0.20
Nodes (8): BusinessError, Biznes qoidasi buzilganda — servis qatlamidan otiladi., ModerationViewSet, action, Vazifani o'ziga biriktiradi — ikki moderator bitta e'lonni bir vaqtda ko'rib…, Moderatorlar uchun navbat. `/api/v1/moderation/queue/` — kutayotgan e'lonlar…, Ko'rib chiqilmagan e'lonlar — eng eskisi birinchi. Navbat FIFO: sotuvchi kutish…, Moderator ko'rish uchun mahsulotning to'liq ko'rinishi.

### Community 27 - "Telegram Publishing Service"
Cohesion: 0.16
Nodes (14): format_price(), 12500000 -> '12 500 000 so'm, Yagona (singleton) sozlamalar yozuvi. Token .env dan o'qiladi; bu yerda faqat…, TelegramSettings, _absolute_media_url(), publish_product(), Mahsulotni kanalga joylaydi va TelegramPost yozuvini qaytaradi., Kanal ID: avval admin panelidagi qiymat, keyin `.env`. (+6 more)

### Community 28 - "Telegram Client & Post Models"
Cohesion: 0.19
Nodes (14): get_client(), Telegram Bot API klienti. Token faqat `settings.TELEGRAM_BOT_TOKEN` dan (ya'ni…, Telegram API xato qaytardi yoki javob bermadi., TelegramError, Telegram bot va kanal integratsiyasi. Bot token hech qachon bu modellarda…, TelegramPostStatus, delete_post(), mark_post_sold() (+6 more)

### Community 29 - "Frontend Package Manifest"
Cohesion: 0.12
Nodes (16): name, private, type, version, autoprefixer, cross-env, eslint, jsdom (+8 more)

### Community 30 - "Catalog Seeding Command"
Cohesion: 0.22
Nodes (5): Command, atomic, BaseCommand, make_unique_slug(), Kirill/lotin matndan takrorlanmas slug yasaydi. python-slugify kirillchani…

### Community 31 - "Category Tree API"
Cohesion: 0.17
Nodes (7): CategoryTreeSerializer, Rekursiv daraxt. `children` oldindan yuklangan bo'lishi kutiladi., CategoryViewSet, action, Kategoriya uchun xususiyatlar (ota kategoriyalardan meros bilan). E'lon…, Butun daraxtni bitta so'rovda qaytaradi. Barcha kategoriyalar bir marta…, method_decorator

### Community 32 - "Soft-Delete Model Layer"
Cohesion: 0.14
Nodes (6): AllObjectsManager, Odatiy `objects` faqat o'chirilmaganlarni qaytaradi., O'chirish o'rniga belgilash — audit va tiklash imkoniyati uchun., SoftDeleteManager, SoftDeleteModel, SoftDeleteQuerySet

### Community 33 - "Safe Media Paths & Migrations"
Cohesion: 0.19
Nodes (12): build_media_path(), products/<uuid>/images/<xavfsiz-nom> ko'rinishidagi yo'l. owner_id UUID…, Xavfsiz va SEO uchun mazmunli fayl nomi yasaydi. "../../etc/passwd.jpg" kabi…, safe_media_filename(), Migration, Migration, product_image_path(), product_poster_path() (+4 more)

### Community 34 - "Media Upload Views & Limits"
Cohesion: 0.17
Nodes (7): ImageReorderSerializer, Drag & drop natijasi: [{id, order}, ...], check_image_limit(), ProductImageViewSet, action, atomic, Bir yoki bir nechta rasm yuklash. Fayllar `images` kaliti bilan yuboriladi (bir…

### Community 35 - "Frontend API Client & Endpoints"
Cohesion: 0.19
Nodes (10): api, refreshAccessToken(), setAccessToken(), setUnauthorizedHandler(), auth, catalog, media, moderation (+2 more)

### Community 36 - "Form Fields & Toast UI"
Cohesion: 0.21
Nodes (10): fieldErrors(), Field(), PhoneField(), ICONS, ToastContext, ToastProvider(), TONES, LoginPage() (+2 more)

### Community 37 - "User Profile Serializers"
Cohesion: 0.21
Nodes (7): Meta, PublicSellerSerializer, Foydalanuvchining o'zi uchun to'liq profil., Sotuvchi kartasi — telefon raqam bu yerda YO'Q. Raqam faqat alohida, cheklangan…, UserSerializer, UserUpdateSerializer, MeView

### Community 38 - "Category Hierarchy Model"
Cohesion: 0.17
Nodes (5): Category, O'zi + barcha avlodlari — katalogda 'ota kategoriya' tanlanganda., O'z atributlari + ota kategoriyalardan meros olganlari. Masalan "Elektronika"…, Ko'p darajali kategoriya daraxti (self-FK). Kategoriyalar soni kichik…, CategoryWriteSerializer

### Community 39 - "RBAC Permission Classes"
Cohesion: 0.15
Nodes (9): HasPermission, IsOwner, IsOwnerOrReadOnly, IsStaff, Faqat egasi — o'qish uchun ham., Ko'rinish `required_permission` atributini e'lon qiladi. class…, Admin panelga kirish: xodim roli yoki superuser., O'qish hammaga, o'zgartirish faqat egasiga (yoki ruxsati borga). (+1 more)

### Community 40 - "Telegram Celery Tasks"
Cohesion: 0.23
Nodes (10): t.me havolasi (faqat public kanal uchun)., Kanalga yuborilgan (yoki yuborilmoqchi bo'lgan) har bir post., TelegramPost, _bump_retry_count(), mark_telegram_post_sold(), publish_product_to_telegram(), shared_task, Telegram Celery tasklari. Redis bo'lmasa CELERY_TASK_ALWAYS_EAGER=True bilan… (+2 more)

### Community 41 - "Frontend Dev Dependencies"
Cohesion: 0.15
Nodes (13): devDependencies, autoprefixer, cross-env, eslint, jsdom, postcss, tailwindcss, @tailwindcss/postcss (+5 more)

### Community 42 - "Media File Serializers"
Cohesion: 0.26
Nodes (4): Meta, ProductImageSerializer, ProductVideoSerializer, Rasm — barcha o'lchamlari bilan. Frontend `srcset` qurishi uchun uchala o'lcham…

### Community 43 - "Magic-Bytes File Validation"
Cohesion: 0.27
Nodes (10): check_video_limit(), detect_image_type(), detect_video_type(), _extension(), _human_size(), Fayl yuklash validatsiyasi. Uch qatlamli tekshiruv, chunki har biri alohida…, Fayl boshidan haqiqiy rasm turini aniqlaydi., Rasmni tekshiradi. Xato bo'lsa nima qilish kerakligini aytadi. (+2 more)

### Community 44 - "Security Headers Middleware"
Cohesion: 0.20
Nodes (5): LastSeenMiddleware, Xavfsizlik headerlari va yengil foydalanuvchi kuzatuvi., Foydalanuvchining oxirgi faolligini kuniga bir marta yangilaydi. Har so'rovda…, Django SecurityMiddleware qamramaydigan headerlarni qo'shadi. CSP, Permissions-…, SecurityHeadersMiddleware

### Community 45 - "Frontend Runtime Dependencies"
Cohesion: 0.18
Nodes (11): dependencies, axios, compression, express, lucide-react, react, react-dom, react-router-dom (+3 more)

### Community 46 - "Attribute Definition Schema"
Cohesion: 0.22
Nodes (5): AttributeDefinition, Kategoriyaga bog'langan xususiyat sxemasi. `code` — Product.specs JSONB…, AttributeDefinitionWriteSerializer, AttributeViewSet, Xususiyat sxemasi — asosan admin uchun.

### Community 47 - "ProductImage & ProductVideo Models"
Cohesion: 0.22
Nodes (5): Meta, ProductImage, ProductVideo, Ro'yxatlarda medium, bo'lmasa original., Media serializerlari.

### Community 48 - "Demo Product Seeder"
Cohesion: 0.29
Nodes (4): Command, atomic, BaseCommand, _weighted()

### Community 49 - "Registration & Password Reset"
Cohesion: 0.28
Nodes (7): PasswordResetRequestSerializer, RegisterSerializer, _debug_otp(), PasswordResetRequestView, Dev rejimida kodni javobga qo'shamiz — SMS provayder yo'q. DEBUG=False…, RegisterView, extend_schema

### Community 50 - "Image Optimization Celery Tasks"
Cohesion: 0.31
Nodes (8): _base_name(), cleanup_product_media(), process_product_image(), shared_task, Rasm optimizatsiyasi (Celery). Yuklash so'rovi tez tugashi uchun og'ir ish shu…, O'chirilgan yozuvlarning fayllarini diskdan tozalaydi., Nisbatni saqlab kichraytiradi. Kattalashtirilmaydi., _resize()

### Community 51 - "Media Routing & Mixins"
Cohesion: 0.33
Nodes (4): Media yo'llari mahsulot ostida joylashadi: /api/v1/products/{slug}/images/…, ProductMediaMixin, ProductVideoViewSet, Media yuklash endpointlari. Barcha yo'llar mahsulotga bog'langan:…

### Community 52 - "SSR Express Server"
Cohesion: 0.22
Nodes (5): app, __dirname, port, compression, express

### Community 53 - "Health Check Endpoint"
Cohesion: 0.25
Nodes (5): api_view, health(), Tizim holati endpointlari., Deploy va monitoring uchun: baza ishlayaptimi?, permission_classes

### Community 54 - "Password Change Flow"
Cohesion: 0.29
Nodes (3): PasswordChangeSerializer, _validate_password_strength(), PasswordChangeView

### Community 55 - "Localized DRF Error Messages"
Cohesion: 0.25
Nodes (5): CoreConfig, AppConfig, apply(), DRF va Django standart xato xabarlarini o'zbekchaga o'girish. Nega gettext…, Xabarlarni o'rnatadi. Bir necha marta chaqirilsa ham zararsiz.

### Community 56 - "Product Filter Set"
Cohesion: 0.25
Nodes (4): Meta, ProductFilter, Kategoriya va uning barcha ichki kategoriyalari., Bir nechta brend: `?brand=asus,msi`

### Community 57 - "Django Settings Environments"
Cohesion: 0.25
Nodes (4): CT Sale — umumiy sozlamalar. Muhitga bog'liq farqlar dev.py / prod.py / test.py…, Lokal development sozlamalari., Production sozlamalari., Test sozlamalari — tez va tashqi servislarsiz.

### Community 58 - "Frontend Build Scripts"
Cohesion: 0.25
Nodes (8): scripts, build, build:client, build:server, dev, lint, preview, test

### Community 59 - "Token Refresh & Logout Views"
Cohesion: 0.33
Nodes (5): APIView, _clear_refresh_cookie(), LogoutView, Cookie'dagi refresh token orqali yangi access oladi. Refresh rotation yoqilgan:…, RefreshView

### Community 60 - "SSR and SEO Strategy Decisions"
Cohesion: 0.33
Nodes (7): SPA + Bot Meta Injection for SEO, entry-client.jsx Hydration Entry, SSR Injection Placeholders (app-head/app-html/app-state), SEO Requirements (meta, JSON-LD, sitemap, prerender), JSON-LD Structured Data Set, No User-Agent Based Content Splitting, Vite SSR Instead of Pure CSR

### Community 61 - "Notification Preferences"
Cohesion: 0.29
Nodes (4): NotificationPreference, NotificationType, Bildirishnomalar: sayt ichi + Telegram + Email., Foydalanuvchi qaysi kanaldan xabar olishni xohlaydi.

### Community 62 - "Saved Search & Query Log"
Cohesion: 0.29
Nodes (5): Meta, Saqlangan qidiruv — mos e'lon chiqqanda xabar berish uchun., Qidiruv so'rovlari jurnali — autocomplete takliflari va tahlil uchun., SavedSearch, SearchQueryLog

### Community 63 - "Unified API Exception Handler"
Cohesion: 0.47
Nodes (5): APIException, api_exception_handler(), _first_message(), Yagona xato formati. Frontend har doim bir xil shaklni oladi, shuning uchun…, Ichma-ich joylashgan DRF xatolaridan birinchi o'qiladigan matnni oladi.

### Community 65 - "Pagination Classes"
Cohesion: 0.47
Nodes (4): LargePagination, SmallPagination, StandardPagination, PageNumberPagination

### Community 66 - "Product QuerySet Scopes"
Cohesion: 0.33
Nodes (3): ProductQuerySet, Saytda ko'rinadigan e'lonlar., Sotuvga ochiq e'lonlar (sotilgan/band emas).

### Community 67 - "CT Sale Brand Mark"
Cohesion: 0.47
Nodes (6): Brand Indigo #4F46E5, CT Monogram (brand initials lettermark), CT Sale Brand Identity, CT Sale Favicon Mark (rounded indigo square with white CT), Rounded-Square App Icon Pattern (rx=7 on 32x32 viewBox), system-ui Font Stack for Icon Lettering

### Community 68 - "Spec Validation Against Schema"
Cohesion: 0.40
Nodes (3): _coerce_spec_value(), `specs` ni kategoriya sxemasiga solishtiradi va tozalaydi. Sxemada yo'q…, validate_specs()

### Community 69 - "Celery App Bootstrap"
Cohesion: 0.40
Nodes (3): debug_task(), Celery ilovasi. Redis mavjud bo'lmasa .env dagi CELERY_TASK_ALWAYS_EAGER=True…, task

### Community 70 - "Multilingual URL & Sitemap"
Cohesion: 0.40
Nodes (5): python-slugify 8.0.4, Dynamic Multilingual Sitemap and robots.txt, Language-Prefixed URL Architecture (/uz/product/{slug}), previous_slugs and 301 Redirects, apps.seo (SeoSettings, SeoRedirect, StaticPageSeo)

### Community 71 - "Telegram Bot User Model"
Cohesion: 0.50
Nodes (3): Meta, Bot bilan muloqot qilgan foydalanuvchilar (bildirishnoma yuborish uchun)., TelegramBotUser

### Community 72 - "Telegram HTML Spec Rendering"
Cohesion: 0.50
Nodes (4): _escape(), Kartada ko'rsatiladigan xususiyatlardan qisqa qator yasaydi., Telegram HTML rejimi uchun ekranlash. Telegram faqat `<`, `>` va `&`…, _render_specs()

### Community 73 - "Telegram Inline Button Links"
Cohesion: 0.50
Nodes (4): is_public_url(), Inline tugma — faqat havola ochiq bo'lganda., Telegram ochа oladigan URL mi? Telegram localhost/127.0.0.1 va boshqa ichki…, _reply_markup()

### Community 74 - "Django manage.py Entry"
Cohesion: 0.50
Nodes (3): main(), Django's command-line utility for administrative tasks., Run administrative tasks.

### Community 77 - "Design Tokens & Web Font"
Cohesion: 0.67
Nodes (3): Design System Tokens, Inter Web Font Preconnect, theme-color #4F46E5 Meta

## Ambiguous Edges - Review These
- `Deployment Stack (nginx/gunicorn/celery/systemd)` → `whitenoise 6.9.0`  [AMBIGUOUS]
  backend/requirements.txt · relation: conceptually_related_to

## Knowledge Gaps
- **116 isolated node(s):** `Migration`, `Migration`, `AuditAction`, `Migration`, `Migration` (+111 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 585 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **33 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Deployment Stack (nginx/gunicorn/celery/systemd)` and `whitenoise 6.9.0`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `TimeStampedModel` connect `Catalog Seed Data & Models` to `SEO App: Redirects & Indexing`, `Interactions: Favorites, Views, Reports`, `Safe Media Paths & Migrations`, `Accounts: OTP & Login Attempts`, `Category Hierarchy Model`, `Seed & Admin Management Commands`, `Telegram Bot User Model`, `Telegram Celery Tasks`, `Notifications Delivery`, `Attribute Definition Schema`, `User & ShopProfile Models`, `ProductImage & ProductVideo Models`, `Moderation Task Model`, `Analytics: Audit Log & Daily Stats`, `Telegram Publishing Service`, `Telegram Client & Post Models`, `Notification Preferences`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `Product` connect `Denormalized Counters & Audit Base` to `SEO App: Redirects & Indexing`, `Interactions: Favorites, Views, Reports`, `Product API Views & Search`, `Seed & Admin Management Commands`, `Product Model & Serializers`, `Telegram Celery Tasks`, `Catalog Filtering & Faceting`, `Catalog Seed Data & Models`, `Product Status State Machine`, `Moderation Task Model`, `Demo Product Seeder`, `Media Routing & Mixins`, `Catalog Seeding Command`, `Product Filter Set`, `Saved Search & Query Log`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `BusinessError` connect `Moderation Queue Views` to `Interactions: Favorites, Views, Reports`, `Media Upload Views & Limits`, `Accounts: OTP & Login Attempts`, `Spec Validation Against Schema`, `Product API Views & Search`, `Catalog Filtering & Faceting`, `Magic-Bytes File Validation`, `Product Status State Machine`, `Moderation Task Model`, `Auth Serializers & Throttling`, `Media Routing & Mixins`, `Token Refresh & Logout Views`, `Unified API Exception Handler`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 17 inferred relationships involving `Product` (e.g. with `Command` and `CompareViewSet`) actually correct?**
  _`Product` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `ProductViewSet` (e.g. with `Category` and `BusinessError`) actually correct?**
  _`ProductViewSet` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `BusinessError` (e.g. with `confirm_password_reset()` and `confirm_registration()`) actually correct?**
  _`BusinessError` has 14 INFERRED edges - model-reasoned connections that need verification._