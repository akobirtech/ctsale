# CT Sale — SECURITY

Bu hujjat loyihada **amalda qilingan** himoya choralarini va ularning
sabablarini yozib qo'yadi. Har bir band kodga yoki testga bog'langan.

---

## Autentifikatsiya

### Parollar

**Argon2id** — OWASP tavsiya qiladigan algoritm.

```python
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",   # yangi parollar
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",   # eskilarini o'qish
    ...
]
```

Ro'yxat tartibi muhim: birinchisi yangi parollar uchun, qolganlari
eski hashlarni tekshirib, kirish paytida jimgina Argon2 ga ko'chirish
uchun.

O'zbekcha validatorlar (`apps/accounts/validators.py`): eng kam 8
belgi, harf + raqam, keng tarqalgan parollar ro'yxati, telefon/ismga
o'xshashlik tekshiruvi.

### Tokenlar

| Token | Qayerda | Muddati |
|---|---|---|
| Access | Javob tanasida → frontend **xotirada** saqlaydi | 15 daqiqa |
| Refresh | `httpOnly` + `SameSite=Lax` cookie | 7 kun |

> **Nega localStorage emas:** XSS bo'lganda localStorage darhol
> o'qiladi va token o'g'irlanadi. Xotiradagi token sahifa yangilanganda
> yo'qoladi, sessiya esa httpOnly cookie orqali tiklanadi — JavaScript
> uni ko'ra olmaydi.

Refresh **rotation**: har chaqiruvda yangi refresh beriladi, eskisi
blacklist'ga tushadi. O'g'irlangan eski token ishlamaydi.

Parol o'zgarganda **barcha qurilmalardagi sessiyalar yopiladi**.

### OTP

- Kod SHA-256 hash ko'rinishida saqlanadi — baza sizib chiqsa ham
  amaldagi kodlar foydasiz
- 5 daqiqa amal qiladi
- 5 ta noto'g'ri urinishdan keyin kod kuyadi
- Qayta yuborish 60 soniya kutadi
- Bir vaqtda faqat bitta amaldagi kod

> **Tuzatilgan nuqson:** `verify_otp` avval `@transaction.atomic`
> ichida chaqirilardi. Xato otilganda tranzaksiya rollback qilib,
> urinishlar hisoblagichini ham bekor qilardi — ya'ni 6 raqamli kodni
> **cheksiz marta taxmin qilish** mumkin edi. Tekshiruv tranzaksiyadan
> tashqariga chiqarildi (`tests/test_auth.py::test_too_many_attempts_burns_the_code`).

### Hisob oshkorligi

Kirish xatosi **raqam mavjudligini bildirmaydi** — mavjud va mavjud
bo'lmagan raqam uchun xabar bir xil. Parol tiklash so'rovi ham raqam
topilmasa `200` qaytaradi. Aks holda endpoint raqamlarni tekshirib
chiqish vositasiga aylanardi.

---

## Avtorizatsiya

### RBAC

```
User ──< UserRole >── Role ──< RolePermission >── Permission(code)
```

25 ruxsat, `resurs.harakat` shaklida (`product.approve`).
Tekshiruv ikki bosqichli:

1. **Harakat darajasi** — foydalanuvchida kerakli permission bormi
2. **Obyekt darajasi** — bu aynan uning obyektimi

```python
class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if user_has_permission(request.user, P.PRODUCT_EDIT_ANY):
            return True
        return obj.seller_id == request.user.id
```

### Huquqlarni oshirishning oldini olish

| Chora | Sabab |
|---|---|
| `admin` rolida `role.manage` **yo'q** | Administrator o'ziga huquq qo'shib ola olmasligi kerak |
| Superuser'ni bloklab bo'lmaydi | Tizimga kirish butunlay yo'qolib qolmasin |
| O'zini bloklab bo'lmaydi | Tasodifiy o'zini chiqarib yuborishning oldini oladi |
| Noma'lum rol kodi rad etiladi | Yozuv xatosi jimgina ruxsatsiz hisob yaratmasin |
| Bloklangan foydalanuvchi ruxsatlarini yo'qotadi | `user_has_permission` `ban_is_active` ni tekshiradi |

Bularning har biri `tests/test_rbac.py` da tekshiriladi.

### Anonim va ruxsatsiz farqi

| Holat | Kod |
|---|---|
| Token yo'q | `401` — kim ekaningiz noma'lum |
| Token bor, ruxsat yo'q | `403` — kimligingiz ma'lum, lekin mumkin emas |

---

## Kirish ma'lumotlarini tekshirish

### So'rov chegaralari

| Amal | Chegara |
|---|---|
| Kirish | 5 / daqiqa |
| Ro'yxatdan o'tish | 3 / soat |
| OTP | 5 / soat |
| E'lon yaratish | 10 / kun |
| Media yuklash | 30 / soat |
| Telefon ochish | 30 / soat |
| Shikoyat | 10 / kun |

### Brute-force himoyasi

Throttling so'rov **sonini** cheklaydi. Bundan tashqari bitta hisobga
qaratilgan hujum alohida aniqlanadi: `LoginAttempt` jadvalida 15
daqiqada 10 ta muvaffaqiyatsiz urinish bo'lsa hisob vaqtincha
bloklanadi.

### SQL in'ektsiya

Barcha so'rovlar Django ORM orqali — parametrlanган. Xom SQL
ishlatilmaydi. JSONB filtrlari ham ORM `__` operatorlari bilan
quriladi.

**Dinamik xususiyat filtrlari alohida himoyalangan:** `spec_<kod>`
parametrlari faqat kategoriya sxemasida mavjud va `is_filterable`
bo'lgan kodlar uchun qabul qilinadi. Foydalanuvchi ixtiyoriy JSONB
yo'li bo'ylab so'rov yubora olmaydi.

### XSS

- API faqat JSON qaytaradi, HTML render qilmaydi
- React matnni avtomatik ekranlaydi
- `dangerouslySetInnerHTML` loyihada **umuman ishlatilmaydi**
- SSR ma'lumoti `<script type="application/json">` ichida uzatiladi
  (JS kodi sifatida emas) — `</script` ketma-ketligi to'siladi
- Telegram postida `<`, `>`, `&` ekranlanadi

### Massiv tayinlash (mass assignment)

Serializer `fields` ro'yxati oq ro'yxat vazifasini bajaradi.
`status`, `seller`, `views_count`, `is_featured` kabi maydonlar yozish
serializerida umuman yo'q — ularni faqat servis qatlami o'zgartiradi.

`specs` JSONB ham tozalanadi: sxemada yo'q kalitlar saqlanmaydi.

---

## Fayl yuklash

### Uch qatlamli tekshiruv

```
1. Kengaytma    (.jpg .jpeg .png .webp)     — foydalanuvchi o'zgartira oladi
2. MIME turi    (Content-Type)              — brauzer yuboradi, soxtalashtirish oson
3. Magic bytes  (fayl boshidagi imzo)       — eng ishonchli qatlam
```

Qo'shimcha: Pillow bilan ochib ko'riladi (buzuq fayl aniqlanadi),
o'lcham tekshiriladi (200×200 dan kichik va 12000 piksel dan katta rad
etiladi).

### Limitlar

| | |
|---|---|
| Rasm | 10 ta × 10 MB |
| Video | 2 ta × 50 MB |
| `DATA_UPLOAD_MAX_MEMORY_SIZE` | 55 MB |

### Path traversal

Foydalanuvchi bergan fayl nomi **butunlay tashlab yuboriladi**.
Yangi nom mahsulot slug'i + tasodifiy qism + oq ro'yxatdagi
kengaytmadan quriladi:

```
"../../../etc/passwd.jpg"  →  "asus-rog-strix-g16-abdb35.jpg"
```

Yo'l: `products/<uuid>/images/<xavfsiz-nom>` — UUID papka nomi ham
taxmin qilib bo'lmaydigan.

Test: `tests/test_media.py::test_path_traversal_attempt_is_neutralised`.

### EXIF

Rasm qayta ishlanganda EXIF metama'lumoti **tozalanadi** — telefon
suratlaridagi GPS koordinatalari e'lon bilan birga tarqalmasin.

---

## Maxfiylik

### Telefon raqamlar

Telefon raqam **ro'yxat va mahsulot sahifasi javoblarida yo'q**.
Sotuvchi kartasida faqat niqoblangan ko'rinish: `+998 90 *** ** 67`.

To'liq raqam faqat `/products/{slug}/reveal-phone/` orqali, soatiga 30
marta chegarasi bilan beriladi. Har ochilish qayd etiladi.

Bu e'lonlarni ommaviy yig'ib, raqamlar bazasini tuzishni qiyinlashtiradi.

### IP manzillar

`ProductView` va `PhoneReveal` jadvallarida IP **ochiq saqlanmaydi**:

```python
ip_hash = sha256(SECRET_KEY[:16] + ip)
```

Takrorni aniqlash uchun yetarli, lekin bazadan IP'larni tiklab
bo'lmaydi.

### Audit jurnali

Maxfiy maydonlar jurnalga tushmaydi — `password`, `token`,
`code_hash`, `secret` so'zlarini o'z ichiga olgan maydonlar
avtomatik filtrlanadi (`apps/analytics/services._sanitize`).

---

## HTTP headerlar

`apps/core/middleware.SecurityHeadersMiddleware` har javobga qo'yadi:

| Header | Qiymat |
|---|---|
| `Content-Security-Policy` | `frame-ancestors 'none'`, `object-src 'none'`, `base-uri 'self'` va boshqalar |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=(), payment=(), usb=()` |
| `Cross-Origin-Opener-Policy` | `same-origin` |
| `Cross-Origin-Resource-Policy` | `cross-origin` (media boshqa domendan yuklanadi) |
| `Cache-Control` | Autentifikatsiyalangan API javoblariga `no-store, private` |

`Server` headeri **nginx darajasida** yashiriladi (`server_tokens off`
va `proxy_hide_header Server`). Django middleware buni qila olmaydi:
headerni HTTP server middleware ishlagandan keyin qo'yadi. Shu sababli
development serverida (`runserver`) u ko'rinib turadi — bu kutilgan
holat, productionda esa yashirin.

Production'da qo'shimcha (`config/settings/prod.py`):

```python
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
```

### CORS

```python
CORS_ALLOWED_ORIGINS = [...]   # aniq ro'yxat
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # productionda
```

Cookie bilan ishlagani uchun `*` ishlatib bo'lmaydi.

### CSRF

API JWT bilan ishlaydi va `SameSite=Lax` cookie ishlatadi, shuning
uchun klassik CSRF vektori yopiq. Django admin va session
autentifikatsiyasi uchun `CsrfViewMiddleware` yoqilgan holda qoladi.

---

## Sirlar

| Qoida | Holati |
|---|---|
| Barcha sirlar `.env` da | ✅ |
| `.env` `.gitignore` da | ✅ |
| `.env.example` da faqat kalit nomlari | ✅ |
| Bot tokeni API javobiga chiqmaydi | ✅ `is_configured` bayrog'i beriladi |
| `SECRET_KEY` va `JWT_SECRET` alohida | ✅ |
| Xato javoblarida ichki ma'lumot yo'q | ✅ Tafsilot logga, foydalanuvchiga umumiy xabar |

```bash
# Repozitoriyda sir yo'qligini tekshirish
git grep -iE "(api[_-]?key|secret|password|token)\s*=\s*['\"][A-Za-z0-9]{16,}"
```

---

## Xato ishlovchisi

Kutilmagan xato yuz berganda foydalanuvchi **hech qanday ichki
ma'lumot ko'rmaydi**:

```json
{
  "error": {
    "code": "server_error",
    "message": "Serverda kutilmagan xatolik yuz berdi. Biroz o'tib qaytadan urinib ko'ring.",
    "details": {}
  }
}
```

To'liq traceback faqat `logs/ctsale.log` ga yoziladi.

---

## Tahdid modeli

| Tahdid | Chora |
|---|---|
| Parol brute-force | Throttle (5/daq) + `LoginAttempt` (10/15 daq) + Argon2 |
| OTP brute-force | 5 urinish, hash saqlash, 5 daqiqalik muddat |
| Token o'g'irlash (XSS) | httpOnly refresh, xotiradagi access, CSP |
| Token qayta ishlatish | Rotation + blacklist |
| Huquqlarni oshirish | `admin` da `role.manage` yo'q, superuser himoyasi |
| Raqamlarni yig'ish | Telefon faqat alohida endpointdan, chegara bilan |
| Hisob mavjudligini aniqlash | Bir xil xato xabarlari |
| Zararli fayl yuklash | Magic bytes + Pillow + limitlar |
| Path traversal | Fayl nomi butunlay qayta quriladi |
| SQL in'ektsiya | ORM, spec filtrlari oq ro'yxatda |
| Spam e'lonlar | Moderatsiya, `product_create` chegarasi |
| Ommaviy shikoyat | Bitta user — bitta shikoyat (unique cheklov) |
| GPS oshkorligi | EXIF tozalanadi |

---

## Production checklist

```
[ ] DEBUG=False
[ ] SECRET_KEY va JWT_SECRET yangi, kamida 50 belgi
[ ] ALLOWED_HOSTS aniq domen (yulduzcha emas)
[ ] DJANGO_SETTINGS_MODULE=config.settings.prod
[ ] HTTPS sertifikat o'rnatilgan, SECURE_SSL_REDIRECT=True
[ ] REFRESH_COOKIE_SECURE=True
[ ] CORS_ALLOWED_ORIGINS aniq ro'yxat
[ ] PostgreSQL faqat localhost'da (yoki VPC ichida)
[ ] Redis faqat localhost'da, parol bilan
[ ] .env fayl huquqlari 600, egasi ilova foydalanuvchisi
[ ] Django admin (/django-admin/) yopilgan yoki IP bo'yicha cheklangan
[ ] /api/v1/docs/ productionda yopilgan yoki himoyalangan
[ ] SEO_ALLOW_INDEXING=False — staging nusxasida
[ ] Zaxira nusxa sozlangan va TIKLASH sinab ko'rilgan
[ ] logs/ katalogi rotatsiya bilan, disk to'lib qolmasin
[ ] Telegram tokeni yangilangan (agar biror joyga tushgan bo'lsa)
[ ] pytest yashil: venv/bin/python -m pytest
```

### Tekshirish

```bash
cd backend
DJANGO_SETTINGS_MODULE=config.settings.prod venv/bin/python manage.py check --deploy
```

---

## Zaifliklar haqida xabar berish

Zaiflik topsangiz uni ommaviy issue sifatida ochmang. Loyiha egasiga
to'g'ridan-to'g'ri yozing va tuzatilgunicha tafsilotlarni oshkor
qilmang.

---

## Tekshirilgan nuqsonlar tarixi

Testlar yozilganda topilgan va tuzatilgan xavfsizlikka aloqador
muammolar:

| Nuqson | Oqibat |
|---|---|
| OTP urinishlar hisoblagichi rollback bo'lardi | Kodni cheksiz taxmin qilish mumkin edi |
| `settings` nomli action DRF atributini yashirgan | Xato ishlovchisi ishlamay qolgan, 500 javoblarda ichki ma'lumot chiqishi mumkin edi |

Ikkalasi ham `tests/` da qayd etilgan va regressiya bo'lmasligi
tekshiriladi.
