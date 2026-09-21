# CT Sale — DEPLOYMENT

Ikki yo'l: **Docker Compose** (tezroq) yoki **Ubuntu'ga qo'lda**
(nazorat ko'proq). Ikkalasi ham bir xil natijaga olib keladi.

```
Internet → Nginx (:443, SSL)
             ├── /            → SSR server (:5173, Node)
             ├── /api/        → Gunicorn (:8000, Django)
             ├── /media/      → fayllar
             ├── /static/     → fayllar
             └── /robots.txt, /sitemap*.xml → Gunicorn
                                  ↓
                        PostgreSQL 16 · Redis
                                  ↑
                      Celery worker · Celery beat
```

Frontend SSR **Node jarayoni** talab qiladi — u sahifani serverda
render qiladi (crawler to'liq HTML ko'rishi uchun). Statik build
yetarli emas.

---

## A. Docker Compose

### Talablar

- Docker 24+ va Docker Compose v2
- Domen A-yozuvi serverga yo'naltirilgan

### Qadamlar

```bash
git clone <repo> /opt/ctsale
cd /opt/ctsale

cp backend/.env.example backend/.env
nano backend/.env          # pastdagi "Production .env" bo'limiga qarang

docker compose build
docker compose up -d

# Boshlang'ich ma'lumot
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_roles
docker compose exec backend python manage.py seed_catalog
docker compose exec backend python manage.py collectstatic --noinput
docker compose exec backend python manage.py create_admin \
    --phone "+998901234567" --role superadmin
```

Tekshirish:

```bash
docker compose ps
curl http://localhost/api/v1/health/
docker compose logs -f backend
```

### Servislar

| Servis | Nima qiladi |
|---|---|
| `postgres` | Baza (volume: `pgdata`) |
| `redis` | Celery brokeri va kesh |
| `backend` | Gunicorn (Django) |
| `celery` | Rasm optimizatsiyasi, Telegram postlari |
| `celery-beat` | Muddati tugagan e'lonlar, kunlik statistika |
| `frontend` | SSR server (Node) |
| `nginx` | Reverse proxy, SSL, statik fayllar |

### Yangilash

```bash
cd /opt/ctsale
git pull
docker compose build backend frontend
docker compose up -d
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --noinput
```

---

## B. Ubuntu 22.04 / 24.04 — qo'lda

### 1. Tizim paketlari

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv python3-pip \
    postgresql postgresql-contrib redis-server nginx git \
    build-essential libpq-dev libjpeg-dev zlib1g-dev certbot python3-certbot-nginx

# Node 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Foydalanuvchi va kod

```bash
sudo adduser --system --group --home /opt/ctsale ctsale
sudo -u ctsale git clone <repo> /opt/ctsale/app
cd /opt/ctsale/app
```

### 3. Baza

```bash
sudo -u postgres psql <<'SQL'
CREATE USER ctsale WITH PASSWORD 'KUCHLI_PAROL_SHU_YERGA';
CREATE DATABASE ctsale OWNER ctsale ENCODING 'UTF8';
ALTER ROLE ctsale SET client_encoding TO 'utf8';
ALTER ROLE ctsale SET timezone TO 'Asia/Tashkent';
SQL
```

`pg_trgm` va `unaccent` kengaytmalari migratsiya orqali o'rnatiladi —
qo'lda yaratish shart emas.

PostgreSQL faqat localhost'da tinglasin:

```bash
sudo nano /etc/postgresql/16/main/postgresql.conf
# listen_addresses = 'localhost'
sudo systemctl restart postgresql
```

### 4. Backend

```bash
cd /opt/ctsale/app/backend
sudo -u ctsale python3.12 -m venv venv
sudo -u ctsale venv/bin/pip install -r requirements.txt
sudo -u ctsale venv/bin/pip install gunicorn

sudo -u ctsale cp .env.example .env
sudo -u ctsale nano .env          # to'ldiring
sudo chmod 600 .env

sudo -u ctsale venv/bin/python manage.py migrate
sudo -u ctsale venv/bin/python manage.py collectstatic --noinput
sudo -u ctsale venv/bin/python manage.py seed_roles
sudo -u ctsale venv/bin/python manage.py seed_catalog
sudo -u ctsale venv/bin/python manage.py create_admin --phone "+998..." --role superadmin
```

### 5. Frontend

```bash
cd /opt/ctsale/app/frontend
sudo -u ctsale npm ci
sudo -u ctsale npm run build
```

### 6. Systemd

Konfiguratsiyalar `deploy/systemd/` da tayyor:

```bash
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ctsale-backend ctsale-frontend ctsale-celery ctsale-celery-beat

sudo systemctl status ctsale-backend
```

### 7. Nginx va SSL

```bash
sudo cp deploy/nginx/ctsale.conf /etc/nginx/sites-available/ctsale
sudo nano /etc/nginx/sites-available/ctsale     # domen nomini o'zgartiring
sudo ln -s /etc/nginx/sites-available/ctsale /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

sudo certbot --nginx -d domain.uz -d www.domain.uz
```

Certbot SSL sozlamalarini o'zi qo'shadi va sertifikatni avtomatik
yangilaydi.

### 8. Fayrvol

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

---

## Production `.env`

```ini
DJANGO_SETTINGS_MODULE=config.settings.prod
DEBUG=False

SECRET_KEY=<yangi, kamida 50 belgi>
JWT_SECRET=<alohida yangi kalit>
ALLOWED_HOSTS=domain.uz,www.domain.uz

SITE_NAME=CT Sale
FRONTEND_URL=https://domain.uz

DATABASE_URL=postgres://ctsale:PAROL@127.0.0.1:5432/ctsale

CORS_ALLOWED_ORIGINS=https://domain.uz,https://www.domain.uz
CSRF_TRUSTED_ORIGINS=https://domain.uz,https://www.domain.uz

REFRESH_COOKIE_SECURE=True
REFRESH_COOKIE_SAMESITE=Lax
SECURE_SSL_REDIRECT=True

REDIS_URL=redis://127.0.0.1:6379/0
CELERY_TASK_ALWAYS_EAGER=False
USE_REDIS_CACHE=True

TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_CHANNEL_ID=@kanal_nomi
TELEGRAM_WEBHOOK_SECRET=<tasodifiy satr>

SEO_ALLOW_INDEXING=True
GOOGLE_SITE_VERIFICATION=
YANDEX_VERIFICATION=

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DEFAULT_FROM_EMAIL=CT Sale <noreply@domain.uz>
```

Kalit yaratish:

```bash
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

> **Staging serverda `SEO_ALLOW_INDEXING=False`** qo'ying — aks holda
> test nusxasi Google indeksiga tushib, asosiy saytga duplicate
> content sifatida zarar yetkazadi.

---

## Deploy'dan oldingi tekshiruv

```bash
cd backend
DJANGO_SETTINGS_MODULE=config.settings.prod venv/bin/python manage.py check --deploy
venv/bin/python -m pytest -q

cd ../frontend
npm run build
```

[SECURITY.md](SECURITY.md) dagi production checklistini ham ko'rib chiqing.

---

## Zaxira nusxa

### Kunlik skript

`deploy/backup.sh` tayyor. Cron'ga qo'shish:

```bash
sudo cp deploy/backup.sh /usr/local/bin/ctsale-backup
sudo chmod +x /usr/local/bin/ctsale-backup
sudo crontab -e
```

```cron
0 3 * * * /usr/local/bin/ctsale-backup >> /var/log/ctsale-backup.log 2>&1
```

Skript bazani `pg_dump -Fc` bilan va `media/` ni `tar.gz` bilan
zaxiralaydi, 14 kundan eski nusxalarni o'chiradi.

> **Tiklashni sinab ko'ring.** Sinalmagan zaxira — zaxira emas.

```bash
pg_restore -U ctsale -d ctsale --clean /opt/ctsale/backups/db_2026-09-21.dump
tar -xzf /opt/ctsale/backups/media_2026-09-21.tar.gz -C /opt/ctsale/app/backend/
```

---

## Monitoring

### Salomatlik

```bash
curl https://domain.uz/api/v1/health/
```

Baza javob bermasa `503` qaytaradi — uptime monitoring shu yo'lni
kuzatishi kerak.

### Loglar

```bash
sudo journalctl -u ctsale-backend -f
sudo journalctl -u ctsale-celery -f
tail -f /opt/ctsale/app/backend/logs/ctsale.log
sudo tail -f /var/log/nginx/error.log
```

`logs/ctsale.log` 5 MB dan oshganda avtomatik rotatsiya qilinadi
(3 ta eski fayl saqlanadi).

### Nimani kuzatish kerak

| Ko'rsatkich | Chegara |
|---|---|
| `/api/v1/health/` | 200 bo'lmasa ogohlantirish |
| Disk bandligi | 80% dan oshsa — media tez o'sadi |
| `TelegramPost` `failed` soni | Admin panelda ko'rinadi |
| Moderatsiya navbati | Uzoq kutish — sotuvchilar ketib qoladi |
| PostgreSQL ulanishlar soni | `max_connections` ga yaqinlashmasin |

---

## Yangilash

```bash
cd /opt/ctsale/app
sudo -u ctsale git pull

# Backend
cd backend
sudo -u ctsale venv/bin/pip install -r requirements.txt
sudo -u ctsale venv/bin/python manage.py migrate
sudo -u ctsale venv/bin/python manage.py collectstatic --noinput

# Frontend
cd ../frontend
sudo -u ctsale npm ci
sudo -u ctsale npm run build

sudo systemctl restart ctsale-backend ctsale-frontend ctsale-celery ctsale-celery-beat
```

Uzilishsiz yangilash uchun Gunicorn'ni qayta ishga tushirish o'rniga
`HUP` signali yuborish mumkin:

```bash
sudo systemctl reload ctsale-backend
```

---

## Redis'siz ishlatish

Redis majburiy emas. `.env` da:

```ini
CELERY_TASK_ALWAYS_EAGER=True
USE_REDIS_CACHE=False
```

Bunda rasm optimizatsiyasi va Telegram posti **so'rov ichida
sinxron** bajariladi. Kam trafikda bu yetarli, lekin rasm yuklash
sekinroq bo'ladi va Telegram xatolari qayta urinilmaydi.

`ctsale-celery` va `ctsale-celery-beat` servislarini yoqmang.

---

## Keng tarqalgan muammolar

### 502 Bad Gateway

Gunicorn yoki SSR server ishlamayapti.

```bash
sudo systemctl status ctsale-backend ctsale-frontend
sudo journalctl -u ctsale-backend -n 50
```

### Statik fayllar yuklanmayapti

```bash
sudo -u ctsale venv/bin/python manage.py collectstatic --noinput
ls -la /opt/ctsale/app/backend/staticfiles/
```

Nginx `alias` yo'li to'g'riligini va `www-data` o'qiy olishini tekshiring.

### Rasm yuklanmayapti (413)

Nginx `client_max_body_size` 60 MB bo'lishi kerak (video uchun).
Konfiguratsiyada bor, lekin tekshirib ko'ring.

### Telegram posti ketmayapti

[TELEGRAM.md](TELEGRAM.md) dagi "Xatolarni bartaraf etish" bo'limiga
qarang. Eng ko'p uchraydigani: `FRONTEND_URL` `https://` bilan
boshlanmagan yoki bot kanalda administrator emas.

### SSR sahifa 500 qaytaryapti

```bash
sudo journalctl -u ctsale-frontend -n 50
```

Odatda backend javob bermayotganidan. SSR server `/api` ni backendga
proksilaydi — `API_URL` muhit o'zgaruvchisi to'g'riligini tekshiring.

### Migratsiya "extension does not exist" deydi

Baza foydalanuvchisida kengaytma yaratish huquqi yo'q:

```bash
sudo -u postgres psql -d ctsale -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
sudo -u postgres psql -d ctsale -c "CREATE EXTENSION IF NOT EXISTS unaccent;"
```

---

## Qidiruv tizimlariga ulash

Sayt ishga tushgach:

1. **Google Search Console** — domenni tasdiqlang, tasdiqlash kodini
   `.env` dagi `GOOGLE_SITE_VERIFICATION` ga qo'ying yoki admin
   panelidagi SEO sozlamalariga kiriting
2. Sitemap yuboring: `https://domain.uz/sitemap.xml`
3. **Yandex Webmaster** — xuddi shunday, `YANDEX_VERIFICATION`
4. `https://domain.uz/robots.txt` ochilishini tekshiring —
   sitemap havolalari va `Host` direktivasi bo'lishi kerak

Tasdiqlash kodlari kodga yozilmaydi — `.env` yoki admin panel orqali
boshqariladi.
