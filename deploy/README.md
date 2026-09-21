# deploy/

Production konfiguratsiyalari. Ishlatish tartibi: [../DEPLOYMENT.md](../DEPLOYMENT.md)

```
systemd/    4 ta servis: backend (gunicorn), frontend (SSR),
            celery worker, celery beat
nginx/      reverse proxy, SSL, statik fayllar, so'rov chegarasi
backup.sh   kunlik baza + media zaxirasi
```

Fayllarni ko'chirishdan oldin o'zgartiring:

| Fayl | Nimani |
|---|---|
| `nginx/ctsale.conf` | `domain.uz` → o'z domeningiz |
| `systemd/*.service` | `/opt/ctsale/app` → haqiqiy yo'l (boshqa bo'lsa) |
| `backup.sh` | Muhit o'zgaruvchilari orqali sozlanadi, tahrirlash shart emas |

Docker orqali chiqarish uchun bular kerak emas — `docker-compose.yml`
va `Dockerfile` lar loyiha ildizida.
