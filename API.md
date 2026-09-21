# CT Sale — API

Barcha endpointlar `/api/v1/` ostida. Javoblar JSON.

Interaktiv hujjat (server ishlab turganda):
- Swagger UI — `/api/v1/docs/`
- ReDoc — `/api/v1/redoc/`
- OpenAPI sxemasi — `/api/v1/schema/`

---

## Autentifikatsiya

```
Authorization: Bearer <access_token>
```

**Access token** — 15 daqiqa, javob tanasida qaytadi. Frontend uni faqat
xotirada saqlaydi.

**Refresh token** — 7 kun, `httpOnly` cookie'da (`ctsale_refresh`,
`path=/api/v1/auth/`). JavaScript uni o'qiy olmaydi. Access token
muddati tugasa `/auth/refresh/` chaqiriladi; har chaqiruvda yangi
refresh beriladi va eskisi bekor qilinadi (rotation + blacklist).

> Nega localStorage emas: XSS bo'lganda localStorage darhol o'qiladi.
> Xotira + httpOnly cookie juftligi bu xavfni yo'qotadi.

---

## Xato formati

Barcha xatolar bir xil shaklda keladi:

```json
{
  "error": {
    "code": "invalid_specs",
    "message": "Xususiyatlarda xatolik bor. «Protsessor» to'ldirilishi shart.",
    "details": {
      "cpu": "«Protsessor» to'ldirilishi shart.",
      "ram_gb": "«Operativ xotira» to'ldirilishi shart."
    }
  }
}
```

| Maydon | Izoh |
|---|---|
| `code` | Dasturiy ishlov berish uchun barqaror kod |
| `message` | Foydalanuvchiga ko'rsatish uchun tayyor o'zbekcha matn |
| `details` | Maydon darajasidagi xatolar (formaga ulash uchun) |

### Status kodlari

| Kod | Qachon |
|---|---|
| `200` / `201` | Muvaffaqiyat |
| `400` | Validatsiya yoki biznes qoidasi buzilgan |
| `401` | Token yo'q yoki yaroqsiz (**kim ekaningiz noma'lum**) |
| `403` | Kimligingiz ma'lum, lekin ruxsat yo'q |
| `404` | Topilmadi |
| `409` | Ziddiyat (takroriy shikoyat, boshqa moderator olib qo'ygan) |
| `410` | E'lon butunlay o'chirilgan (qidiruv tizimlari uchun signal) |
| `429` | So'rov chegarasi (`details.retry_after` — necha soniya kutish) |
| `500` | Server xatosi. Tafsilot logga yoziladi, javobda umumiy xabar |

### So'rov chegaralari

| Amal | Chegara |
|---|---|
| Kirish | 5 / daqiqa |
| Ro'yxatdan o'tish | 3 / soat |
| OTP | 5 / soat |
| Qidiruv | 60 / daqiqa |
| E'lon yaratish | 10 / kun |
| Media yuklash | 30 / soat |
| Telefon ochish | 30 / soat |
| Shikoyat | 10 / kun |
| Anonim (umumiy) | 120 / daqiqa |

Bundan tashqari bitta hisobga qaratilgan hujumni aniqlash uchun
**brute-force himoyasi**: 15 daqiqada 10 ta muvaffaqiyatsiz kirish
urinishi hisobni vaqtincha bloklaydi.

---

## Sahifalash

Ro'yxat qaytaradigan endpointlar:

```json
{
  "count": 121,
  "page": 1,
  "pages": 6,
  "page_size": 24,
  "next": "http://.../products/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

`?page=2&page_size=50` (eng ko'pi 100).

---

## Til

Ko'p tilli maydonlar `?lang=uz|ru|en` bilan boshqariladi (standart `uz`).
Noma'lum til yuborilsa standart tilga qaytariladi.

---

# Endpointlar

## Auth — `/api/v1/auth/`

| Metod | Yo'l | Izoh |
|---|---|---|
| POST | `register/` | Ro'yxatdan o'tish, OTP yuboradi |
| POST | `verify/` | OTP tasdiqlash → tokenlar |
| POST | `resend-otp/` | Kodni qayta yuborish (60 s kutish) |
| POST | `login/` | Kirish |
| POST | `refresh/` | Yangi access (cookie orqali) |
| POST | `logout/` | Refresh bekor qilinadi |
| GET PATCH | `me/` | Profil |
| POST | `password/change/` | Parol o'zgartirish |
| POST | `password/reset/` | Tiklash so'rovi |
| POST | `password/reset/confirm/` | Kod + yangi parol |

### Ro'yxatdan o'tish

```http
POST /api/v1/auth/register/
Content-Type: application/json

{
  "phone": "+998901234567",
  "password": "Kuchli#Parol9",
  "password_confirm": "Kuchli#Parol9",
  "first_name": "Akobir"
}
```

```json
{
  "detail": "Tasdiqlash kodi yuborildi.",
  "phone": "+998901234567",
  "expires_in": 300
}
```

Telefon raqam qanday yozilsa ham `+998XXXXXXXXX` ga keltiriladi.
`DEBUG=True` bo'lsa javobga `debug_code` qo'shiladi (SMS provayder
ulanmagan bo'lsa test qilish uchun); productionda hech qachon.

### Tasdiqlash

```http
POST /api/v1/auth/verify/
{"phone": "+998901234567", "code": "123456"}
```

```json
{
  "access": "eyJhbGciOi...",
  "expires_in": 900,
  "user": {
    "id": "...", "phone": "+998901234567", "full_name": "Akobir",
    "is_phone_verified": true,
    "roles": ["user"],
    "permissions": []
  }
}
```

Kod 5 daqiqa amal qiladi, 5 marta noto'g'ri kiritilsa kuyadi.

### Xavfsizlik xatti-harakati

- Kirish xatosi **raqam mavjudligini oshkor qilmaydi**: mavjud va mavjud
  bo'lmagan raqam uchun xabar bir xil.
- Parol tiklash so'rovi ham shunday: raqam topilmasa ham `200` qaytadi.
- Parol o'zgarganda **barcha qurilmalardagi sessiyalar yopiladi**,
  joriy qurilmaga yangi juftlik beriladi.

---

## Katalog

| Metod | Yo'l | Kirish | Izoh |
|---|---|---|---|
| GET | `categories/tree/` | ochiq | Butun daraxt, bitta so'rovda |
| GET | `categories/{slug}/` | ochiq | Bitta kategoriya + breadcrumbs |
| GET | `categories/{slug}/attributes/` | ochiq | Xususiyatlar (meros bilan) |
| POST PATCH DELETE | `categories/` | `category.manage` | |
| GET | `brands/` `brands/popular/` | ochiq | |
| GET | `regions/?with_districts=true` | ochiq | Viloyat va tumanlar |
| GET | `attributes/?category={slug}` | ochiq | Xususiyat sxemasi |

### Xususiyatlar merosi

`/categories/gaming-noutbuklar/attributes/` ota kategoriyalardagi
xususiyatlarni ham qaytaradi. Masalan `warranty_months` "Noutbuklar"
da e'lon qilingan bo'lsa, "Gaming noutbuklar" ham oladi.

```json
[
  {
    "code": "ram_gb",
    "label": "Operativ xotira",
    "data_type": "integer",
    "unit": "GB",
    "is_required": true,
    "is_filterable": true,
    "min_value": "2.00",
    "max_value": "256.00",
    "options": []
  },
  {
    "code": "os",
    "label": "Operatsion tizim",
    "data_type": "select",
    "options": [
      {"value": "win11", "label": "Windows 11"},
      {"value": "linux", "label": "Linux"}
    ]
  }
]
```

E'lon formasi shu ro'yxat asosida quriladi — admin yangi xususiyat
qo'shsa frontend kodi o'zgarmaydi.

---

## Mahsulotlar — `/api/v1/products/`

| Metod | Yo'l | Kirish |
|---|---|---|
| GET | `products/` | ochiq |
| GET | `products/{slug}/` | ochiq |
| GET | `products/search/?q=` | ochiq |
| GET | `products/autocomplete/?q=` | ochiq |
| GET | `products/featured/` | ochiq |
| GET | `products/{slug}/similar/` | ochiq |
| POST | `products/{slug}/reveal-phone/` | ochiq |
| GET | `products/my/` | egasi |
| POST | `products/` | tasdiqlangan telefon |
| PATCH DELETE | `products/{slug}/` | egasi yoki `product.edit_any` |
| POST | `products/{slug}/submit/` | egasi |
| POST | `products/{slug}/mark-sold/` | egasi |
| POST | `products/{slug}/renew/` | egasi |
| POST | `products/{slug}/status/` | egasi (approve/reject — moderator) |

### Filtrlar

```
?category=gaming-noutbuklar
?brand=asus,msi
?condition=new,like_new
?price_min=5000000&price_max=20000000
?region=toshkent-shahri
?is_new=true
?has_warranty=true
?is_exchange_possible=true
?with_video=true
?include_sold=true
?sort=newest|oldest|price_asc|price_desc|popular|most_viewed
?facets=true
```

### Dinamik xususiyat filtrlari

Kategoriya berilganda `spec_<kod>` filtrlari ishlaydi:

```
?category=gaming-noutbuklar&spec_ram_gb_min=16&spec_ram_gb_max=32
?category=gaming-noutbuklar&spec_os=win11,linux
```

| Shakl | Ma'nosi |
|---|---|
| `spec_ram_gb=16` | Aniq moslik |
| `spec_ram_gb_min=16` | Kamida |
| `spec_ram_gb_max=32` | Ko'pi bilan |
| `spec_os=win11,linux` | Ro'yxatdan biri |

> Faqat kategoriya sxemasida mavjud va `is_filterable` bo'lgan kodlar
> qabul qilinadi. Bu ixtiyoriy JSONB yo'li bo'ylab so'rov yuborishning
> oldini oladi. Noma'lum kod yoki noto'g'ri son jimgina e'tiborsiz
> qoldiriladi — butun so'rov yiqilmaydi.

### Facetlar

`?facets=true` filtr variantlari yonidagi sonlarni qaytaradi:

```json
{
  "facets": {
    "condition": [{"value": "good", "label": "Yaxshi holatda", "count": 34}],
    "brand": [{"value": "asus", "label": "ASUS", "count": 12}],
    "region": [...],
    "price": {"min": 450000, "max": 30000000},
    "specs": [
      {"code": "ram_gb", "label": "Operativ xotira", "type": "range",
       "unit": "GB", "min": 8, "max": 64},
      {"code": "os", "label": "Operatsion tizim", "type": "choice",
       "options": [{"value": "win11", "label": "Windows 11", "count": 18}]}
    ]
  }
}
```

### Qidiruv

`/products/search/?q=rtx 4060`

Avval PostgreSQL full-text (sarlavha vazni `A`, model `B`, tavsif `C`).
Natija bo'lmasa trigram o'xshashligiga o'tadi — shuning uchun
`noutbukk` ham topadi. Umuman natija bo'lmasa `suggestions` qaytadi.

### E'lon yaratish

```http
POST /api/v1/products/
{
  "title": "ASUS ROG Strix G16 gaming noutbuk",
  "description": "8 oy ishlatilgan, ideal holatda...",
  "category": 2,
  "brand": 1,
  "region": 1,
  "price": 12500000,
  "currency": "UZS",
  "is_negotiable": true,
  "condition": "good",
  "specs": {"cpu": "Intel Core i7-13650HX", "ram_gb": 16, "storage_gb": 1000}
}
```

Javob — to'liq mahsulot obyekti (`slug` bilan; rasm yuklash uchun kerak).

Validatsiya qoidalari:
- Sarlavha ≥ 10 belgi, tavsif ≥ 20 belgi
- Narx majburiy, agar `is_negotiable` yoki `price_on_request` belgilanmagan bo'lsa
- Faqat "barg" kategoriya (ichki bo'limi borlari rad etiladi)
- `condition: "new"` bo'lsa ishlatilgan mahsulot maydonlari rad etiladi
- `specs` kategoriya sxemasiga solishtiriladi; sxemada yo'q kalitlar tashlab yuboriladi

### Holat mashinasi

```
DRAFT ──submit──> PENDING ──approve──> APPROVED ──┬──> SOLD
  ^                 │                      │      ├──> RESERVED
  │                 └──reject──> REJECTED  │      ├──> ARCHIVED
  └────edit─────────────────────┘          └──────┴──> EXPIRED
```

Ruxsat etilmagan o'tish `400 invalid_status_transition` qaytaradi.
`product.force_status` ruxsati borlar qoidani chetlab o'ta oladi.

Tasdiqlangan e'londa sarlavha, narx, tavsif, holat, kategoriya, brend
yoki xususiyatlar o'zgarsa — e'lon **avtomatik qayta moderatsiyaga**
tushadi. Manzil izohi kabi mayda o'zgarishlar tushmaydi.

### Telefonni ochish

```http
POST /api/v1/products/{slug}/reveal-phone/
```

```json
{"phone": "+998901234567", "name": "Akobir", "telegram": "username"}
```

Telefon raqam **ro'yxat va mahsulot sahifasi javoblarida yo'q** — faqat
shu endpoint orqali, chegara bilan beriladi. Sotuvchi kartasida
niqoblangan ko'rinishi turadi (`+998 90 *** ** 67`). Bir IP 24 soat
ichida takror ochsa hisoblanmaydi.

---

## Media — `/api/v1/products/{slug}/`

| Metod | Yo'l |
|---|---|
| GET POST | `images/` |
| DELETE | `images/{id}/` |
| POST | `images/{id}/set-primary/` |
| POST | `images/reorder/` |
| GET POST | `videos/` |
| DELETE | `videos/{id}/` |

```http
POST /api/v1/products/{slug}/images/
Content-Type: multipart/form-data

images: <fayl>
images: <fayl>
```

Limitlar: 10 rasm × 10 MB (JPG/PNG/WebP), 2 video × 50 MB (MP4/WebM).

Uch qatlamli tekshiruv: kengaytma → MIME → **magic bytes**. Kengaytmasi
`.jpg`, ichi matn bo'lgan fayl rad etiladi.

Yuklangach Celery rasmni WebP ga o'tkazadi (thumb 300 / medium 800 /
large 1600) va EXIF ma'lumotini tozalaydi — telefon rasmlaridagi GPS
koordinatalari saqlanib qolmasin.

Fayl nomi mahsulot slug'idan yasaladi:
`asus-rog-strix-g16-rtx-4060-abdb35.webp`.

---

## Moderatsiya — `/api/v1/moderation/`

| Metod | Yo'l | Ruxsat |
|---|---|---|
| GET | `queue/` | `product.approve` yoki `product.view_any` |
| GET | `stats/` | — |
| GET | `{id}/preview/` | — |
| POST | `{id}/claim/` | — |
| POST | `{id}/approve/` | `product.approve` |
| POST | `{id}/reject/` | `product.reject` |
| POST | `bulk-approve/` | `product.approve` |

Navbat FIFO — sotuvchi kutish vaqti taxmin qilinadigan bo'lsin.

```http
POST /api/v1/moderation/{id}/reject/
{"reason_code": "bad_photos", "comment": "Rasmlar xira", "internal_note": "..."}
```

`reason_code` majburiy. `other` tanlansa `comment` ham majburiy.
`internal_note` faqat xodimlarga ko'rinadi, sotuvchiga bormaydi.

Tasdiqlash quyidagilarni birdaniga bajaradi: e'lon `APPROVED` bo'ladi,
muddat qo'yiladi, SEO maydonlari to'ldiriladi, sotuvchiga bildirishnoma
ketadi, Telegram posti navbatga qo'yiladi, audit yoziladi.

---

## Sevimlilar, taqqoslash, shikoyatlar

| Metod | Yo'l | Kirish | Izoh |
|---|---|---|---|
| GET | `favorites/` | kirgan | Ro'yxat |
| POST | `favorites/toggle/` | kirgan | `{"slug": "..."}` — qo'shadi yoki olib tashlaydi |
| GET | `favorites/ids/` | kirgan | Faqat IDlar (katalogda yurakchalarni belgilash uchun) |
| GET | `compare/items/?slugs=a,b,c` | **ochiq** | Taqqoslash mehmonlarga ham |
| GET | `reports/reasons/` | kirgan | 8 ta sabab |
| POST | `reports/` | kirgan | Shikoyat yuborish |
| GET | `reports/` | `report.view` | Xodimlar uchun ro'yxat |
| POST | `reports/{id}/resolve/` | `report.resolve` | Qaror |

O'z e'loniga shikoyat qilish bloklanadi. Takroriy shikoyat `409`.

---

## Bildirishnomalar — `/api/v1/notifications/`

| Metod | Yo'l |
|---|---|
| GET | `notifications/` (`?unread=true`) |
| GET | `notifications/unread-count/` |
| POST | `notifications/{id}/read/` |
| POST | `notifications/read-all/` |
| GET PATCH | `notifications/preferences/` |

Sayt ichidagi yozuv har doim yaratiladi. Telegram va email
foydalanuvchi sozlamasiga qarab qo'shimcha ravishda yuboriladi —
tashqi kanal uzilsa ham xabar saytda ko'rinadi.

---

## Admin — `/api/v1/admin/`

| Metod | Yo'l | Ruxsat |
|---|---|---|
| GET | `dashboard/stats/` | xodim |
| GET | `dashboard/chart/?days=30` | xodim |
| GET | `users/` | `user.view` |
| GET | `users/roles/` | `user.change_role` |
| POST | `users/{id}/ban/` | `user.ban` |
| POST | `users/{id}/unban/` | `user.ban` |
| POST | `users/{id}/verify-seller/` | `user.verify_seller` |
| POST | `users/{id}/roles/` | `user.change_role` |
| GET | `products/` | `product.view_any` |
| GET | `products/{id}/` | `product.view_any` |
| POST | `products/{id}/feature/` | `product.feature` |
| POST | `products/{id}/force-status/` | `product.force_status` |
| POST | `products/{id}/restore/` | `product.delete_any` |
| DELETE | `products/{id}/` | `product.delete_any` |
| POST | `products/bulk/` | amalga qarab |
| GET | `audit/` | `audit.view` |
| GET | `telegram/` | `telegram.manage` |
| GET PATCH | `telegram/settings/` | `telegram.manage` |
| POST | `telegram/{id}/republish/` | `telegram.manage` |

Botga ulanish havolasi (admin emas, oddiy foydalanuvchi uchun):

```http
POST /api/v1/telegram/link-token/
```

```json
{ "token": "...", "url": "https://t.me/bot?start=...", "expires_in_minutes": 30 }
```

Kod bir martalik. Webhook `/telegram/webhook/` da — u Telegram
serveri uchun, shuning uchun `/api/v1/` ostida emas va
`X-Telegram-Bot-Api-Secret-Token` bilan himoyalangan.

Bloklashda sabab majburiy. Superuser'ni va o'zini bloklash mumkin emas.
Telegram sozlamalari javobida **bot tokeni hech qachon bo'lmaydi** —
faqat `is_configured` bayrog'i.

### E'lonlar jadvali

Ommaviy `/products/` dan farqi: qoralama, rad etilgan va o'chirilgan
e'lonlar ham ko'rinadi. Filtrlar: `status` (vergul bilan bir nechta),
`search` (sarlavha / slug / sotuvchi raqami), `category`, `seller`,
`featured=true`, `deleted=true`. Javobga `status_counts` qo'shiladi —
jadval ustidagi hisoblagichlar uchun.

Tasdiqlash va rad etish bu yerda **yo'q**: ular `/moderation/` da,
chunki u yerda navbat, tarix va bildirishnoma mantiqi bor.

```http
POST /api/v1/admin/products/bulk/
{ "action": "archive", "ids": ["..."] }
```

| `action` | Kerakli ruxsat |
|---|---|
| `feature` / `unfeature` | `product.feature` |
| `archive` | `product.edit_any` |
| `delete` | `product.delete_any` |

Bir so'rovda ko'pi bilan 100 ta e'lon. Ro'yxatni ko'rish huquqi
ommaviy amalga ruxsat bermaydi — har bir amal o'z kodini talab qiladi.
O'chirish har doim yumshoq (`is_deleted`), `restore/` qaytaradi.

---

## Ruxsat kodlari

```
product.view_any    product.edit_any     product.delete_any
product.approve     product.reject       product.feature
product.force_status

user.view           user.edit            user.ban
user.change_role    user.verify_seller

category.manage     brand.manage         attribute.manage
location.manage

telegram.manage     telegram.publish
report.view         report.resolve
audit.view          stats.view           seo.manage
role.manage         settings.manage
```

Standart rollar:

| Rol | Ruxsatlar |
|---|---|
| `superadmin` | Barchasi (25) |
| `admin` | 21 — katalog, e'lonlar, Telegram, statistika. **`role.manage` yo'q** |
| `moderator` | 6 — tasdiqlash/rad etish, shikoyatlar |
| `support` | 3 — ko'rish huquqi |
| `user` | 0 — o'z obyektlariga egalik orqali ishlaydi |

`admin` da ataylab `role.manage` yo'q: aks holda administrator o'ziga
huquqlarni ko'paytirib olishi mumkin bo'lardi.

---

## SEO yo'llari (API ostida emas)

| Yo'l | Izoh |
|---|---|
| `/robots.txt` | Dinamik, admin sozlamalaridan |
| `/sitemap.xml` | Indeks |
| `/sitemap-{uz,ru,en}.xml` | Til bo'yicha indeks |
| `/sitemap-pages-{lang}.xml` | Statik sahifalar |
| `/sitemap-categories-{lang}.xml` | Kategoriyalar (bo'shlari tushmaydi) |
| `/sitemap-products-{lang}-{n}.xml` | Mahsulotlar, har birida hreflang |

Mahsulot sahifasi javobidagi `seo` bloki: `title`, `description`,
`canonical`, `robots`, `hreflang[]`, `og`, `twitter`, `jsonld[]`
(`Product` + `BreadcrumbList`).

### Eski manzillar — 301 / 410

Manzil o'zgarganda eski URL indeksda qolaveradi. U 404 bersa sahifa
yig'gan SEO vazni yo'qoladi, shuning uchun javob doim aniq bo'ladi:

| Holat | Javob |
|---|---|
| Slug o'zgargan (`previous_slugs`) | `301` yangi manzilga |
| `SeoRedirect` jadvalidagi yo'l | `301` yoki `302` |
| Mahsulot o'chirilgan (soft delete) | `410 Gone` |
| Hech qachon bo'lmagan manzil | `404` |

Qaror bitta joyda — `apps/seo/redirects.py` — va uni uch tomon
ishlatadi: `SeoRedirectMiddleware` (backend yo'llari), SSR server
(sahifa 404 chiqqanda) va `ProductViewSet` (API 410).

```http
GET /api/v1/seo/resolve/?path=/uz/product/eski-slug
```

```json
{ "redirect": "/uz/product/yangi-slug", "status": 301 }
```

Bu endpoint SSR server uchun: oddiy sahifalarda chaqirilmaydi, faqat
render 404 bergan holatda. Til prefiksi javobda saqlanadi.

---

## Salomatlik

```http
GET /api/v1/health/
```

```json
{
  "status": "ok",
  "service": "CT Sale",
  "version": "1.0.0",
  "checks": {"database": "ok", "telegram_configured": true}
}
```

Baza javob bermasa `503` qaytaradi — monitoring va deploy tekshiruvi uchun.
