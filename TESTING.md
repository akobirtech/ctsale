# CT Sale — TESTING

## Qisqacha

```bash
cd backend

venv/Scripts/python -m pytest                 # hammasi (~18 s)
venv/Scripts/python -m pytest -q              # qisqa chiqish
venv/Scripts/python -m pytest tests/test_auth.py   # bitta fayl
venv/Scripts/python -m pytest -k "telegram"   # nom bo'yicha
venv/Scripts/python -m pytest --cov           # qamrov bilan
venv/Scripts/python -m pytest -x --lf         # birinchi xatoda to'xta, oxirgi yiqilganlarni qayta
```

Linux/macOS'da `venv/bin/python`.

**Hozirgi holat: 359 test, 87% qamrov, ~19 soniya.**

---

## Nima uchun shunday qurilgan

### Test bazasi alohida

`config/settings/test.py` ishlatiladi. Unda:

| Sozlama | Sabab |
|---|---|
| `TELEGRAM_MOCK` / bo'sh token | Testlar hech qachon tarmoqqa chiqmaydi |
| `CELERY_TASK_ALWAYS_EAGER` | Rasm optimizatsiyasi va Telegram posti sinxron bajariladi |
| `MD5PasswordHasher` | Argon2 har bir foydalanuvchi uchun ~100 ms — 300+ testda bu daqiqalarga aylanardi |
| `MEDIA_ROOT` = vaqtinchalik papka | Loyihaning `media/` katalogi iflos bo'lmaydi |
| `DEFAULT_THROTTLE_RATES` = `None` | Throttle testlar orasida "oqib" o'tardi |
| `locmem` email backend | `mail.outbox` orqali tekshiriladi |

### Throttle nima uchun `None`

`DEFAULT_THROTTLE_CLASSES` ni bo'shatish yetarli emas: ayrim view'lar
o'z `throttle_classes` ini aniq ko'rsatadi (login, OTP, media). Tezlikni
`None` qilish har qanday throttle'ni ishlamas holga keltiradi.

Bundan tashqari `conftest.py` da `autouse` fixture har test oldidan
keshni tozalaydi — aks holda throttle tarixi va katalog keshi testlar
orasida saqlanib, natija **ishga tushirish tartibiga bog'liq** bo'lib
qolardi.

### PostgreSQL kengaytmalari

`apps/core/migrations/0001_postgres_extensions.py` `pg_trgm` va
`unaccent` ni yaratadi. Test bazasi har safar noldan quriladi, shuning
uchun ularni qo'lda yaratib bo'lmaydi — aks holda trigram qidiruvi
(opechatkaga chidamlilik) testlarda ishlamasdi.

---

## Struktura

```
backend/tests/
├── conftest.py                       fixturelar
├── test_auth.py                      34  ro'yxat, OTP, kirish, sessiya, parol
├── test_rbac.py                      34  rollar, ruxsat matritsasi, egalik
├── test_products.py                  48  CRUD, validatsiya, holat mashinasi
├── test_media.py                     22  MIME/magic bytes, limitlar, WebP
├── test_search_filters.py            35  full-text, trigram, JSONB filtr, facet
├── test_moderation.py                24  navbat, approve/reject, bulk
├── test_telegram.py                  31  shablon, usul tanlash, mock, xatolar
├── test_interactions_seo.py          38  sevimli, shikoyat, JSON-LD, sitemap
├── test_admin_api.py                 29  statistika, ban, audit, Telegram admin
├── test_notifications_seo_services.py 25 kanallar, hreflang, schema
├── test_performance.py                24  so'rovlar soni, kesh izolyatsiyasi
└── test_seo_redirects.py              15  301/302/410, eski slug, resolve
```

### So'rovlar sonini o'lchash

`backend/perf_audit.py` asosiy endpointlarda SQL so'rovlar sonini va
javob vaqtini ko'rsatadi:

```bash
cd backend
venv/Scripts/python perf_audit.py
```

```
ENDPOINT                    SO'ROV      VAQT  HOLAT
Bosh sahifa bloklari             8       58ms    200
Katalog (24 ta)                  3       25ms    200
Kategoriya + facet              10       21ms    200
Mahsulot sahifasi                8       10ms    200
```

`tests/test_performance.py` esa shu o'lchovni **qulflab qo'yadi**:
serializerga N+1 keltiradigan maydon qo'shilsa test yiqiladi.
Eng muhimi `test_catalog_does_not_scale_with_result_count` — 5 ta
va 20 ta natija uchun so'rovlar soni deyarli bir xil bo'lishi kerak.

### Fixturelar (`conftest.py`)

| Fixture | Beradi |
|---|---|
| `api` | Autentifikatsiyasiz `APIClient` |
| `auth_client` | `auth_client(user)` — o'sha foydalanuvchi nomidan klient |
| `roles` | 25 ruxsat + 5 rol (`seed_roles` bilan bir xil) |
| `user` `seller` `moderator` `admin` `superadmin` | Tayyor aktyorlar |
| `region` `district` `brand` `category` | Katalog; `category` ota+bola va meros oladigan xususiyat bilan |
| `product_payload` | API'ga yuboriladigan to'g'ri tana |
| `make_product` | `make_product(seller, status=..., **overrides)` |
| `image_file` | Haqiqiy JPEG (magic bytes bilan) |
| `fake_image_file` | `.jpg` kengaytmali, lekin ichi matn |

---

## Yozish qoidalari

**Bitta test — bitta xulq.** Test nomi nima tekshirilayotganini aytadi,
`test_it_works` emas.

**Arrange → Act → Assert**, bo'sh qator bilan ajratilgan:

```python
def test_other_reason_requires_comment(self, auth_client, moderator, pending_task):
    response = auth_client(moderator).post(
        f"/api/v1/moderation/{pending_task.id}/reject/",
        {"reason_code": RejectReasonCode.OTHER},
        format="json",
    )

    assert response.status_code == 400
    assert "comment" in response.data["error"]["details"]
```

**Nima uchun muhimligi tushunarsiz bo'lsa — izoh yoziladi:**

```python
def test_error_does_not_reveal_whether_phone_exists(self, api, user):
    """Xato xabari ikkala holatda bir xil bo'lishi kerak — aks holda
    raqamlarni tekshirib chiqish mumkin bo'lardi."""
```

**Tashqi servislar hech qachon chaqirilmaydi.** Telegram uchun
`FakeClient` chaqiruvlarni yozib boradi:

```python
class FakeClient(TelegramClient):
    def call(self, method, payload=None, files=None):
        self.calls.append((method, payload))
        return {"ok": True, "result": {"message_id": 777}}
```

---

## Testlar topgan haqiqiy nuqsonlar

Bu ro'yxat testlar nima uchun yozilganini ko'rsatadi — barchasi
avval ishlab turgan kodda bor edi.

| Nuqson | Oqibati |
|---|---|
| **OTP urinishlar hisoblagichi rollback bo'lardi** | `verify_otp` `@transaction.atomic` ichida chaqirilgani uchun xato otilganda increment bekor bo'lardi. Ya'ni **6 raqamli kodni cheksiz marta taxmin qilish** mumkin edi. Tekshiruv tranzaksiyadan tashqariga chiqarildi. |
| **`settings` nomli action DRF atributini yashirardi** | `TelegramAdminViewSet.settings` `APIView.settings` ni bosib o'tgan → xato ishlovchisi ishlamay, 500 qaytarardi. `url_path` saqlab, metod nomi o'zgartirildi. |
| **`reveal-phone` mehmonlarga yopiq edi** | Endpointning butun maqsadi mehmon telefonni ko'ra olishi edi, lekin u `public_actions` ro'yxatiga kirmay 401 qaytarardi. |
| **Sotuvchi o'z qoralamasini ocholmasdi** | Detail endpoint faqat ommaviy holatlarni ko'rsatardi → tahrirlashdan oldin ko'rib bo'lmasdi. |
| **`reorder` JSON qabul qilmasdi** | Media view'lari faqat `multipart` parserga sozlangan, frontend esa JSON yuboradi → drag&drop tartiblash 415 bilan yiqilardi. |
| **Telegram havolasida til prefiksi yo'q edi** | `/product/x` → 404, chunki haqiqiy yo'l `/uz/product/x`. Avval "tuzatilgan" deb hisoblangan, lekin almashtirish qo'llanmagan ekan — test ushladi. |
| **`similar` endpointi 500 qaytarardi** | `Decimal * float` — TypeError. Har bir mahsulot sahifasidagi "o'xshash e'lonlar" bo'limi butunlay ishlamasdi. Endpoint umuman sinalmagan edi. |
| **Katalogda N+1** | Har bir mahsulot kartasi uchun kategoriya xususiyatlari qaytadan so'ralardi: bosh sahifa **104 ta** SQL so'rovi yuborardi. |
| **Moderatsiya vazifalari tartibi noaniq edi** | Rad etilgan e'lon darhol qayta yuborilsa ikki vazifa bir xil vaqt tamg'asini olardi va qaysi biri "oxirgi" ekani tasodifga bog'liq bo'lardi. |

---

## Qamrov

```bash
venv/Scripts/python -m pytest --cov --cov-report=html
# natija: backend/htmlcov/index.html
```

Umumiy: **87%**. Modul bo'yicha eng muhimlari:

| Modul | Qamrov |
|---|---|
| `notifications/services` | 100% |
| `adminapi/views` | 98% |
| `accounts/services` | 96% |
| `mediafiles/views` | 94% |
| `moderation/views` | 93% |
| `products/services` | 90% |
| `seo/services` | 91% |
| `products/views` | 85% |

Qamrovga kirmaydiganlar (`.coveragerc`): migratsiyalar, `seed_*`
komandalari, `apps.py`.

---

## Frontend testlari

```bash
cd frontend
npm test            # Vitest
npm run build       # eng muhim tekshiruv: build yiqilmasligi
```

Frontend tomonda hozircha build va tiplar tekshiruvi asosiy himoya.
Komponent testlari Phase 27 ning qolgan qismida qo'shiladi.

---

## CI uchun

```bash
cd backend
venv/Scripts/python -m pytest --cov --cov-fail-under=80 -q
cd ../frontend
npm ci && npm run build
```

`--cov-fail-under=80` qamrov pasayib ketsa build'ni yiqitadi.
