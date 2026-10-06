# CT Sale — TELEGRAM

Tasdiqlangan har bir e'lon avtomatik Telegram kanalga chiqadi.
Sotilganda kanaldagi post yangilanadi.

---

## Sozlash

### 1. Bot yaratish

[@BotFather](https://t.me/BotFather) ga yozing:

```
/newbot
```

Nom va username so'raladi. Natijada token beriladi:

```
1234567890:AAAbbbCCCdddEEEfffGGGhhhIIIjjjKKKlll
```

(yuqoridagi — namuna, haqiqiy token emas)

> **Tokenni hech kimga yubormang va kodga yozmang.** U faqat `.env`
> da turadi. Agar token biror joyga tushib qolgan bo'lsa,
> @BotFather → `/revoke` orqali darhol yangilang.

### 2. Kanal tayyorlash

1. Telegram kanalingizni oching (yoki yangi yarating)
2. **Administratorlar** → botni qo'shing
3. Botga kamida shu huquqlarni bering:
   - Xabar yuborish
   - Xabarlarni tahrirlash (sotilgan deb belgilash uchun)
   - Xabarlarni o'chirish

### 3. Kanal ID ni aniqlash

**Ochiq kanal** — username yetarli: `@kanal_nomi`

**Yopiq kanal** — raqamli ID kerak:

1. Kanaldagi istalgan xabarni botga yo'naltiring
2. Brauzerda oching:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. `forward_from_chat.id` ni oling — `-100` bilan boshlanadi

### 4. `.env` ga yozish

```ini
TELEGRAM_BOT_TOKEN=1234567890:AAAbbbCCCddd...
TELEGRAM_CHANNEL_ID=@kanal_nomi
# yoki yopiq kanal uchun:
# TELEGRAM_CHANNEL_ID=-1001234567890
```

### 5. Tekshirish

```bash
# Bot ishlayaptimi
curl "https://api.telegram.org/bot<TOKEN>/getMe"

# Bot kanalda administratormi
curl "https://api.telegram.org/bot<TOKEN>/getChatMember?chat_id=@kanal_nomi&user_id=<BOT_ID>"
```

`"status": "administrator"` va `"can_post_messages": true` bo'lishi kerak.

Sayt tomonidan:

```bash
curl http://127.0.0.1:8000/api/v1/health/
# "telegram_configured": true
```

---

## Mock rejim

Token yoki kanal ko'rsatilmagan bo'lsa (yoki `TELEGRAM_MOCK=True`)
klient **mock rejimda** ishlaydi:

- Telegram API'ga so'rov yuborilmaydi
- Shablon render qilinadi, media tanlanadi, `TelegramPost` yozuvi
  yaratiladi — butun oqim xuddi haqiqiydek bajariladi
- `TelegramPost.is_mock = True`, `message_id = 0`

Shu sababli Telegram tokensiz ham loyihani to'liq ishga tushirish va
test qilish mumkin. Token qo'shilgan zahoti real ishlay boshlaydi.

---

## Post qanday chiqadi

```
🔥 YANGI MAHSULOT

💻 ASUS ROG Strix G16 gaming noutbuk RTX 4060

💰 Narxi: 12 500 000 so'm (kelishiladi)
📦 Holati: Yaxshi holatda
⚙️ Intel Core i7-13650HX / 16 GB / 1000 GB / RTX 4060
📍 Toshkent shahri

🔗 Saytda ko'rish
```

Pastida inline tugma: **[Saytda ko'rish]** → mahsulot sahifasi.

### Media qanday tanlanadi

| Holat | Usul |
|---|---|
| Rasm yo'q | `sendMessage` |
| 1 rasm | `sendPhoto` + inline tugma |
| 2–10 rasm | `sendMediaGroup` (tugmasiz — Telegram albomda tugmani qo'llamaydi, havola matnda qoladi) |
| Video bor | `sendVideo` |

Xususiyatlar qatoriga faqat `is_in_card` belgilangan xususiyatlar
kiradi (standart 4 tagacha) — post uzayib ketmasin.

---

## Shablonni o'zgartirish

Admin panel → Telegram sozlamalari, yoki API orqali:

```http
PATCH /api/v1/admin/telegram/settings/
{"post_template": "🔥 {title}\n\n💰 {price}\n📍 {location}\n\n{url}"}
```

Mavjud o'zgaruvchilar:

| O'zgaruvchi | Misol |
|---|---|
| `{title}` | ASUS ROG Strix G16 |
| `{price}` | 12 500 000 so'm (kelishiladi) |
| `{condition}` | Yaxshi holatda |
| `{category}` | Gaming noutbuklar |
| `{brand}` | ASUS |
| `{model}` | G614JI |
| `{specs_line}` | ⚙️ Intel i7 / 16 GB / RTX 4060 |
| `{location}` | Toshkent shahri, Chilonzor |
| `{url}` | https://domain.uz/uz/product/slug |
| `{seller}` | Akobir Javadev |
| `{description}` | Tavsifning birinchi 300 belgisi |

Shablon **saqlashdan oldin sinab ko'riladi** — noma'lum o'zgaruvchi
bo'lsa `400` qaytadi va sozlama saqlanmaydi. Aks holda keyingi
barcha postlar buzilardi.

Formatlash: Telegram HTML rejimi (`<b>`, `<i>`, `<a href>`, `<code>`).

---

## Boshqa sozlamalar

| Sozlama | Standart | Izoh |
|---|---|---|
| `auto_publish` | yoqilgan | Tasdiqlangan zahoti yuborish |
| `publish_media` | yoqilgan | Rasm bilan yuborish |
| `publish_video` | yoqilgan | Video ham yuborilsin |
| `update_on_sold` | yoqilgan | Sotilganda postni tahrirlash |
| `sold_suffix` | `❌ SOTILDI` | Sotilganda qo'shiladigan matn |
| `button_text` | `Saytda ko'rish` | Inline tugma matni |
| `max_specs_in_post` | 4 | Postdagi xususiyatlar soni |
| `is_enabled` | yoqilgan | Butun integratsiyani o'chirish |

---

## Oqim

```
Mahsulot APPROVED bo'ladi
        ↓
publish_product_to_telegram.delay(product_id)      (Celery)
        ↓
auto_publish tekshiriladi
        ↓
TelegramPost(status=PENDING) yaratiladi
        ↓
Shablon render qilinadi, media tanlanadi
        ↓
   ┌────┴────┐
   ↓         ↓
  OK      XATO
   │         │
   │         ├─ retryable (429, 5xx) → 60s → 300s → 900s (3 marta)
   │         └─ retryable emas (4xx)  → status=FAILED, xato saqlanadi
   ↓
status=PUBLISHED, message_id saqlanadi
```

Sotilganda:

```
mark_as_sold()  →  mark_telegram_post_sold.delay()  →  editMessageCaption
```

Tahrirlash muvaffaqiyatsiz bo'lsa (post o'chirilgan, juda eski)
xato **yutiladi** — sotuvchining amali shu sababli bekor bo'lmasligi kerak.

---

## Postlarni kuzatish

Admin panel → Telegram, yoki:

```http
GET /api/v1/admin/telegram/?status=failed
```

```json
{
  "results": [{
    "id": 12,
    "product_title": "ASUS ROG Strix G16",
    "status": "failed",
    "status_display": "Xatolik",
    "error_message": "Telegram xatosi: Bad Request: chat not found",
    "retry_count": 3,
    "message_url": ""
  }]
}
```

Qayta yuborish:

```http
POST /api/v1/admin/telegram/{id}/republish/
```

`TelegramPost` statuslari: `pending` · `published` · `failed` ·
`skipped` · `deleted`.

---

## Xatolarni bartaraf etish

### `chat not found`

Bot kanalga qo'shilmagan yoki kanal ID noto'g'ri.

```bash
curl "https://api.telegram.org/bot<TOKEN>/getChat?chat_id=@kanal_nomi"
```

### `not enough rights to send text messages`

Bot administrator, lekin "Xabar yuborish" huquqi berilmagan.
Kanal → Administratorlar → bot → huquqlarni tekshiring.

### `inline keyboard button URL ... is invalid: Wrong HTTP URL`

Telegram `localhost`, `127.0.0.1` va ichki tarmoq manzillarini qabul
qilmaydi. Kod buni oldindan aniqlaydi: `FRONTEND_URL` ochiq domen
bo'lmasa **inline tugma tushiriladi** va matndagi `<a href>` teglari
olib tashlanadi (ichidagi matn qoladi). Productionda bu shart
bajarilmaydi, ya'ni tugma har doim bo'ladi.

Lokal muhitda tugmani sinash uchun tunnel ishlatish mumkin
(masalan `ngrok`), `FRONTEND_URL` ni o'sha manzilga qo'ying.

### Rasm yuborilmayapti

Telegram rasmni **o'zi yuklab oladi**, shuning uchun rasm URL'i
internetdan ochiladigan bo'lishi kerak. Lokal muhitda
`http://localhost/media/...` ochilmaydi va rasm tushiriladi — faqat
matn ketadi. Productionda muammo bo'lmaydi.

### `Too Many Requests`

Telegram kanalga soniyasiga ~20 xabar chegarasini qo'yadi. Klient
buni qayta urinish mumkin bo'lgan xato deb belgilaydi va Celery
60s / 300s / 900s oraliqlarida qayta uradi.

### Post ketmayapti, xato ham yo'q

Tekshiring:

1. `is_enabled` va `auto_publish` yoqilganmi
2. Mahsulot haqiqatan `APPROVED` bo'lganmi
3. `TelegramPost` yozuvi `skipped` emasmi — `error_message` sababni aytadi
4. Celery worker ishlayaptimi (yoki `CELERY_TASK_ALWAYS_EAGER=True` mi)

---

## Xavfsizlik

| Chora | Izoh |
|---|---|
| Token faqat `.env` da | Bazada ham, kodda ham yo'q. `.env` `.gitignore` da |
| Token API javobiga chiqmaydi | `/admin/telegram/settings/` faqat `is_configured` bayrog'ini beradi |
| Webhook `secret_token` bilan | `TELEGRAM_WEBHOOK_SECRET` header orqali tekshiriladi |
| Foydalanuvchi `telegram_id` bo'yicha aniqlanadi | Username o'zgarishi mumkin, ID — yo'q |
| Matn ekranlanadi | `<`, `>`, `&` belgilar `&lt;` ga aylanadi — e'lon sarlavhasi orqali HTML in'ektsiya qilib bo'lmaydi |

Apostrof (`'`) **ekranlanmaydi**: Telegram uni talab qilmaydi va
o'zbekcha matnda juda ko'p uchraydi (`so'm`, `ko'rish`) — ekranlansa
post `so&#x27;m` ko'rinishida chiqardi.

---

## Botdan shaxsiy xabar

Foydalanuvchi `telegram_id` ni bog'lagan bo'lsa, bildirishnomalar
Telegram orqali ham yuboriladi:

```python
from apps.telegrambot.services import send_direct_message

send_direct_message(user.telegram_id, "<b>Sarlavha</b>\n\nMatn")
```

Havolalar to'liq va til prefiksi bilan yuboriladi
(`https://domain.uz/uz/product/slug`) — ichki yo'l yuborilsa 404 bo'lardi.

Bot foydalanuvchini bloklagan bo'lsa xato yutiladi va sayt ichidagi
bildirishnoma baribir ko'rinadi.

---

## Bot bilan suhbat

Kanal e'lonlarni **tarqatadi**, bot esa ularni **topishga** yordam
beradi. Ikkalasi bitta token bilan ishlaydi.

### Buyruqlar

| Buyruq | Nima qiladi |
|---|---|
| `/start` | Salomlashadi va tugmalarni ko'rsatadi |
| `/start <kod>` | Sayt hisobini ulaydi (deep link) |
| `/search <so'z>` yoki oddiy matn | E'lonlarni qidiradi |
| `/my` | E'lonlaringiz va ularning holati |
| `/link` | Hisobni ulash yo'riqnomasi |
| `/stop` | Bildirishnomalarni to'xtatadi |
| `/help` | Yordam |

Qidiruv saytdagi bilan **bir xil funksiyani** ishlatadi
(`apps/products/search.py`): avval full-text, natija bo'lmasa trigram.
Mantiq ikki joyda takrorlanmaydi.

Natijalar 5 tadan chiqadi, qolgani inline tugmalar orqali.
`callback_data` 64 baytga qisqartiriladi — Telegram chegarasi shunday.

Qoralama va rad etilgan e'lonlar qidiruvda **ko'rinmaydi**: bot
`Product.objects.public()` dan foydalanadi. `/my` esa aksincha,
sotuvchining barcha e'lonlarini holati bilan ko'rsatadi.

### Hisobni ulash

```
Sayt profili --> POST /api/v1/telegram/link-token/
             --> https://t.me/<bot>?start=<kod>
             --> bot kodni tekshiradi --> User.telegram_id yoziladi
```

Kod bir martalik va 30 daqiqada eskiradi. U `TelegramLinkToken`
jadvalida turadi, `TelegramBotUser` da emas — bot bilan hali
gaplashmagan odam ham havolani ola bilishi kerak.

Ulangandan keyin bildirishnomalar Telegramga ham boradi.

### Ishga tushirish

Development (webhook localhost'ga kelmaydi):

```bash
cd backend
venv/Scripts/python manage.py run_bot
```

Production:

```bash
venv/Scripts/python manage.py run_bot --set-webhook https://domain.uz/telegram/webhook/
```

`TELEGRAM_WEBHOOK_SECRET` bo'sh bo'lsa buyruq ham, endpoint ham ishni
rad etadi: sirsiz webhook'ga istalgan odam bot nomidan update yubora
olardi. Sir `X-Telegram-Bot-Api-Secret-Token` headerida tekshiriladi.

Webhook `/telegram/webhook/` da — `/api/v1/` ostida emas, chunki u
Telegram serveri uchun: DRF autentifikatsiyasi ham, versiyalash ham
unga tegishli emas.

`run_bot` long polling'dan oldin webhook'ni o'chiradi — Telegram
ikkalasini bir vaqtda bermaydi.

---

## Testlar

```bash
cd backend
venv/Scripts/python -m pytest tests/test_telegram.py -v
```

```bash
venv/Scripts/python -m pytest tests/test_bot_handlers.py -v
```

`test_telegram.py` — 31 test: shablon render, HTML ekranlash, usul
tanlash (photo / mediaGroup / video), mock rejim, xatolarni qayd
etish, sotilgan postni yangilash, shablon validatsiyasi, tokenning
javobga chiqmasligi.

`test_bot_handlers.py` — 39 test: buyruqlar, qidiruv va sahifalash,
`/my`, hisobni ulash (bir martalik va eskiruvchi kod), bloklash,
webhook siri. Tarmoq yo'q: soxta klient yuborilgan xabarlarni yig'adi.

Testlar **hech qachon tarmoqqa chiqmaydi** — `FakeClient` chaqiruvlarni
yozib boradi va tayyor javob qaytaradi.
