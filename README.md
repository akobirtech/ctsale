# CT Sale

> IT texnika marketplace — noutbuk, videokarta, protsessor va komplektuvchilarni
> sotish va sotib olish uchun. Tasdiqlangan har bir e'lon avtomatik
> Telegram kanalga chiqadi.

**Stack:** Django 5 · DRF · PostgreSQL 16 · React 18 (Vite SSR) · Celery · Telegram Bot API

---

## Nima ishlaydi

| | |
|---|---|
| **Xaridor** | Qidiruv (opechatkaga chidamli), dinamik filtrlar, mahsulot sahifasi, sevimlilar, telefonni ochish, shikoyat |
| **Sotuvchi** | Telefon + OTP bilan ro'yxat, 4 qadamli e'lon sehrgari, rasm/video yuklash, statistika |
| **Moderator** | Navbat, tasdiqlash/rad etish (sabab bilan), ommaviy tasdiqlash |
| **Admin** | Dashboard, foydalanuvchilar, rollar, audit jurnali, Telegram boshqaruvi |
| **Telegram** | Tasdiqlangan e'lon kanalga avtomatik chiqadi, sotilganda post yangilanadi |
| **SEO** | SSR, 3 til, hreflang, JSON-LD, dinamik sitemap va robots.txt |

**Hajmi:** 79 API yo'li (108 operatsiya) · 33 model · 239 indeks · 457 backend + 61 frontend test (87% qamrov)

---

## Tez ishga tushirish

### Talablar

- Python 3.12+
- Node.js 20+
- PostgreSQL 16 (`pg_trgm` va `unaccent` kengaytmalari migratsiya orqali o'rnatiladi)
- Redis — **ixtiyoriy** (yo'q bo'lsa Celery vazifalari sinxron bajariladi)

### 1. Baza

```bash
createdb ctsale
# yoki: psql -U postgres -c "CREATE DATABASE ctsale WITH ENCODING 'UTF8';"
```

### 2. Backend

```bash
cd backend

python -m venv venv
venv/Scripts/python -m pip install -r requirements.txt   # Linux/macOS: venv/bin/python

cp .env.example .env
# .env ni to'ldiring — pastdagi "Muhit o'zgaruvchilari" bo'limiga qarang

venv/Scripts/python manage.py migrate
venv/Scripts/python manage.py seed_roles      # 25 ruxsat, 5 rol
venv/Scripts/python manage.py seed_catalog    # 14 viloyat, 68 kategoriya, 40 brend
venv/Scripts/python manage.py create_admin --phone "+998901234567" --role superadmin

venv/Scripts/python manage.py runserver
```

Backend: <http://127.0.0.1:8000> · API hujjati: <http://127.0.0.1:8000/api/v1/docs/>

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Sayt: <http://localhost:5173/uz>

> `npm run dev` SSR serverni ishga tushiradi (oddiy Vite dev server emas) va
> `/api` so'rovlarini backendga proksilaydi — CORS bilan ovora bo'lmaysiz.

### 4. Demo ma'lumot (ixtiyoriy)

```bash
cd backend
venv/Scripts/python manage.py seed_products --products 120
```

120 mahsulot, 20 sotuvchi, 20 xaridor va generatsiya qilingan rasmlar yaratadi.
Demo hisoblar paroli: `Demo#Parol2026`, telefonlari `+99890900xxxxx`.

### Ikkala serverni birga boshqarish

```bash
./dev.sh start     # ikkalasini ishga tushiradi
./dev.sh status    # holatini ko'rsatadi
./dev.sh stop      # to'xtatadi
./dev.sh restart
```

Windows'da `pkill` node/python jarayonlarini o'ldirmaydi va portlar band bo'lib
qoladi — shu skript buni PowerShell orqali to'g'ri bajaradi.

---

## Muhit o'zgaruvchilari

`.env.example` dan nusxa oling. Majburiylari:

| O'zgaruvchi | Izoh |
|---|---|
| `SECRET_KEY` | Django kaliti. `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"` |
| `JWT_SECRET` | JWT imzolash kaliti (alohida bo'lgani ma'qul) |
| `DATABASE_URL` | `postgres://user:parol@host:5432/ctsale` |
| `FRONTEND_URL` | Saytning to'liq manzili. Telegram posti va canonical URL shu yerdan quriladi |

Telegram uchun (ixtiyoriy — bo'lmasa mock rejimda ishlaydi):

| O'zgaruvchi | Izoh |
|---|---|
| `TELEGRAM_BOT_TOKEN` | @BotFather bergan token |
| `TELEGRAM_CHANNEL_ID` | `@kanal_nomi` yoki `-100xxxxxxxxxx` |

To'liq ro'yxat va sukut qiymatlari: `.env.example` va `config/settings/base.py`.

> **Sirlar hech qachon kodga yozilmaydi.** `.env` `.gitignore` da.
> `.env.example` da faqat kalit nomlari turadi.

---

## Testlar

```bash
cd backend
venv/Scripts/python -m pytest              # 457 test, ~22 s
venv/Scripts/python -m pytest --cov        # qamrov hisoboti

cd ../frontend
npm run build                              # eng muhim tekshiruv
```

Batafsil: [TESTING.md](TESTING.md)

---

## Loyiha tuzilishi

```
.
├── backend/
│   ├── config/settings/{base,dev,prod,test}.py
│   ├── apps/
│   │   ├── core/          abstract modellar, xatolar, middleware, utils
│   │   ├── accounts/      foydalanuvchi, OTP, JWT
│   │   ├── rbac/          rollar va ruxsatlar
│   │   ├── catalog/       kategoriya daraxti, brend, dinamik xususiyatlar
│   │   ├── products/      e'lon, holat mashinasi, qidiruv, filtrlar
│   │   ├── mediafiles/    rasm/video yuklash va optimizatsiya
│   │   ├── moderation/    moderatsiya navbati
│   │   ├── interactions/  sevimli, ko'rish, shikoyat
│   │   ├── notifications/ bildirishnomalar va kanallar
│   │   ├── telegrambot/   Telegram klient, shablon, publisher
│   │   ├── analytics/     audit jurnali, kunlik statistika
│   │   ├── seo/           sitemap, robots, JSON-LD, redirectlar
│   │   └── adminapi/      admin panel uchun jamlanmalar
│   └── tests/             457 test
├── frontend/
│   ├── server.js          SSR server (Express + Vite)
│   └── src/
│       ├── routes.jsx     marshrutlar va SSR ma'lumot yuklovchilari
│       ├── seo/Head.jsx   meta, hreflang, JSON-LD
│       ├── i18n/          uz / ru / en
│       ├── api/           endpointlar va axios klienti
│       ├── components/    ui, layout, product, filters, seller
│       └── pages/         bosh, katalog, mahsulot, auth, seller, admin
└── *.md                   hujjatlar
```

Har bir Django ilovasida: `models` → `services` (biznes logika) →
`serializers` → `views`. **Biznes qarorlar `services.py` da**, views'da emas —
shunda bir logikani API, Telegram bot va management command'dan chaqirish mumkin.

---

## Hujjatlar

| Fayl | Nima haqida |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Umumiy arxitektura, qatlamlar, texnik qarorlar va ularning sabablari |
| [API.md](API.md) | 87 endpoint, autentifikatsiya, xato formati, misollar |
| [DATABASE.md](DATABASE.md) | Sxema, bog'lanishlar, indekslar, dinamik xususiyatlar |
| [TELEGRAM.md](TELEGRAM.md) | Bot sozlash, kanal ulash, shablon, xatolarni bartaraf etish |
| [SECURITY.md](SECURITY.md) | Himoya choralari, tahdid modeli, production checklist |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Ubuntu va Docker orqali serverga chiqarish |
| [TESTING.md](TESTING.md) | Testlarni yurgizish, struktura, qoidalar |
| [ROADMAP.md](ROADMAP.md) | Bosqichlar va qabul mezonlari |
| [TASKS.md](TASKS.md) | Bajarilgan va qolgan ishlar |

---

## Foydali komandalar

```bash
# Katalog va rollar
manage.py seed_roles              # ruxsat/rollarni yaratadi (idempotent)
manage.py seed_catalog            # hudud, kategoriya, brend, xususiyatlar
manage.py create_admin --phone +998... --role superadmin

# Ma'lumot
manage.py seed_products --products 120 --fresh
manage.py recount                 # kategoriya/brend hisoblagichlarini tiklaydi

# Xizmat
manage.py check
manage.py migrate
manage.py spectacular --file schema.yml     # OpenAPI sxemasi
```

---

## Hozirgi holat

Ishlaydi: autentifikatsiya, RBAC, katalog, e'lonlar, media, qidiruv va filtrlar,
moderatsiya, Telegram avtomatizatsiyasi, sevimlilar, shikoyatlar,
bildirishnomalar, admin panel, SEO (SSR + sitemap + JSON-LD), 3 til.

Rejada: performance optimizatsiyasi, Docker/deployment, yakuniy QA va
Gemini AI orqali Telegram botdan e'lon yaratish.

Batafsil: [TASKS.md](TASKS.md)
