# SulgX Bot — Railway Deployment (بدون VPS)

این نسخه از پروژه کاملاً برای اجرا روی **Railway** (بدون VPS، بدون nginx،
بدون systemd، بدون certbot، بدون Docker) آماده شده. تمام آن ابزارها از
مسیر اصلی پروژه حذف شده‌اند.

## دو سرویس جدا از این پروژه

⚠️ توجه مهم: پنل SulgX شما (`https://web-production-c666b.up.railway.app`)
از قبل روی Railway اجراست و **یک سرویس کاملاً جدا** است — این ریپو به آن
دست نمی‌زند، فقط از طریق API با آن صحبت می‌کند (`SULGX_BASE_URL`).

این ریپو (پروژه‌ی بات) خودش را به‌صورت **دو سرویس Railway** از همین یک
مخزن GitHub دیپلوی می‌کند:

| سرویس Railway | نقش | Start Command |
|---|---|---|
| `backend` (web) | FastAPI + Telegram WebApp (استاتیک) | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
| `bot` (worker) | ربات تلگرام (polling) | `python -m bot.main` |

هر دو از همان مخزن و همان `nixpacks.toml` استفاده می‌کنند؛ فقط Start
Command سرویس `bot` را در Railway override می‌کنید (پایین توضیح داده شده).

هر دو سرویس باید به **همان** پلاگین PostgreSQL وصل باشند تا از یک
دیتابیس مشترک استفاده کنند.

## مراحل دیپلوی

1. این ریپو را در GitHub push کنید (شامل همین ZIP، بدون `.env` واقعی).
2. در Railway: **New Project → Deploy from GitHub repo** → همین ریپو را
   انتخاب کنید. این سرویس اول را `backend` نام‌گذاری کنید.
3. **New → Database → PostgreSQL** را به همین Project اضافه کنید. Railway
   خودش متغیر `DATABASE_URL` را در سرویس‌هایی که به آن وصل کنید تزریق
   می‌کند (سرویس `backend` را به این Postgres وصل/Attach کنید).
4. در تنظیمات سرویس `backend` → **Variables**، مقادیر بخش
   «Environment Variables لازم» را وارد کنید (پایین).
5. در همان Project یک سرویس دوم بسازید: **New → GitHub Repo** → همان ریپو
   را دوباره انتخاب کنید، نامش را `bot` بگذارید.
   - در Settings → Deploy → **Start Command** مقدار
     `python -m bot.main` را ست کنید (این مقدار پیش‌فرض `nixpacks.toml`
     یعنی uvicorn را override می‌کند).
   - همان Postgres را به این سرویس هم Attach کنید (یا متغیرهای
     `DATABASE_URL` و بقیه را با «Shared Variables» بین دو سرویس به
     اشتراک بگذارید) و همان BOT_TOKEN / SULGX_* را اینجا هم ست کنید.
6. سرویس `backend` را دیپلوی کنید، صبر کنید تا build کامل شود (نصب
   pip + npm install + vite build طبق `nixpacks.toml`)، سپس از تب
   **Settings → Networking** یک دامنه‌ی عمومی برایش فعال کنید (چیزی شبیه
   `https://your-bot-backend.up.railway.app`).
7. متغیر `WEBAPP_URL` را در هر دو سرویس به
   `https://<همان-دامنه>/webapp/` آپدیت کنید و هر دو سرویس را Redeploy
   کنید (بات باید WEBAPP_URL درست را برای دکمه‌ی WebApp بداند).
8. سرویس `bot` را هم دیپلوی کنید و لاگش را چک کنید:
   `Bot starting (polling mode)...` باید دیده شود.

Healthcheck اختیاری برای سرویس `backend` در Railway: مسیر `/health`.

## Environment Variables لازم

```
# --- اجباری ---
BOT_TOKEN=                      # از @BotFather — هرگز در کد/ZIP قرار نمی‌گیرد
SULGX_BASE_URL=https://web-production-c666b.up.railway.app   # بدون /panel
SULGX_ADMIN_PASSWORD=           # پسورد ادمین پنل — هرگز در کد/ZIP قرار نمی‌گیرد
WEBAPP_URL=https://<دامنه-سرویس-backend-شما>/webapp/
ADMIN_IDS=111111111             # آی‌دی عددی ادمین(ها)، با کاما جدا

# --- تزریق خودکار توسط Railway (به دستکاری نیاز ندارد) ---
DATABASE_URL=                   # با اتصال پلاگین Postgres خودکار ست می‌شود
PORT=                           # خودکار توسط Railway ست می‌شود

# --- اختیاری / پیش‌فرض دارند ---
BOT_USERNAME=
REQUIRED_CHANNELS=
REQUIRED_CHANNELS_URLS=
BACKEND_SECRET_KEY=change-this-to-a-long-random-string
CORS_ORIGINS=                   # خالی = فقط same-origin (webapp از همان بک‌اند سرو می‌شود)
TELEGRAM_INIT_DATA_MAX_AGE=86400
SULGX_VERIFY_SSL=true
SULGX_REQUEST_TIMEOUT=15
SULGX_LINK_FIELD=link           # اگر پاسخ POST /api/links کلید دیگری برای لینک VLESS دارد
MIN_VOLUME_GB=1
MAX_VOLUME_GB=55
ALLOWED_VALIDITY_DAYS=7,15,30
ALLOWED_MAX_CONNECTIONS=1,2,3
LOG_LEVEL=INFO
```

جزئیات کامل و توضیح هر متغیر در `.env.example`.

## ساختار نهایی پروژه

```
project/
├── nixpacks.toml            # build/start برای Railway (Python + Node، بدون Docker)
├── Procfile                 # مرجع: web / worker process types
├── requirements.txt
├── .env.example
├── .gitignore
├── config.py                 # همه‌ی تنظیمات از Environment Variables
├── sulgx_api.py               # تنها نقطه‌ی اتصال به API واقعی پنل SulgX v1.1.0
├── database/
│   ├── models.py              # User, Config (بدون inbound_id), RequiredChannel, BroadcastLog
│   └── session.py             # SQLAlchemy async engine (Postgres روی Railway / SQLite لوکال)
├── backend/
│   ├── main.py                 # FastAPI app + mount استاتیک /webapp
│   ├── schemas.py
│   ├── security.py             # اعتبارسنجی initData تلگرام (HMAC طبق مستندات رسمی)
│   └── services/
│       ├── config_service.py   # منطق اصلی: create/renew/reset-link/delete/sync
│       └── user_service.py
├── bot/
│   ├── main.py                  # aiogram 3, polling (بدون webhook)
│   ├── handlers/ (start, service, config_flow, admin)
│   ├── keyboards/
│   ├── middlewares/ (membership)
│   └── services/ (نازک؛ به backend.services وصل می‌شود)
└── webapp/                      # React + Vite (Telegram WebApp)
    ├── src/
    ├── vite.config.js           # base: "/webapp/"
    └── .env.production           # VITE_API_BASE_URL خالی = same-origin
```

## نکات فنی مهم

- **Bot از polling استفاده می‌کند** (نه webhook) — نیازی به دامنه یا SSL
  برای خود بات نیست، فقط `BOT_TOKEN` کافی است.
- **WebApp روی همان دامنه‌ی بک‌اند** (زیر `/webapp`) سرو می‌شود، پس با
  HTTPS پیش‌فرض Railway به‌صورت خودکار روی HTTPS اجرا می‌شود و نیازی به
  CORS واقعی هم نیست (درخواست‌ها same-origin هستند).
- **initData Validation**: طبق الگوریتم رسمی تلگرام (HMAC-SHA256 با
  کلید `WebAppData`) در `backend/security.py` پیاده شده و قابل تنظیم
  حداکثر-عمر (`TELEGRAM_INIT_DATA_MAX_AGE`) است.
- **لینک VLESS همیشه از پاسخ واقعی SulgX خوانده می‌شود**، نه ساخته/حدس
  زده می‌شود (`sulgx_api.py::_extract_link`).
- **Database**: پیشنهادی و پیش‌فرض PostgreSQL (از پلاگین Railway)؛
  `DATABASE_URL` به‌صورت خودکار به درایور async `asyncpg` نگاشت می‌شود.
  SQLite فقط fallback برای اجرای محلی است.

## ⚠️ محدودیت‌های صادقانه‌ای که باید بدانید

1. **من نتوانستم فرانت‌اند را در این محیط build کنم** (این محیط به
   اینترنت دسترسی ندارد، پس `npm install` روی رجیستری npm شکست خورد).
   کد React بدون تغییر منطقی از نسخه‌ی قبلی شماست و از نظر ساختار سالم
   است، ولی build واقعی (`vite build`) را باید Railway در اولین دیپلوی
   انجام دهد — لاگ Build آن سرویس را حتماً چک کنید.
2. **فیلدهای دقیق بدنه‌ی `PATCH /api/links/{uid}`** (برای تمدید حجم/زمان)
   حدسی و مبتنی بر الگوی نام‌گذاری معمول این‌گونه پنل‌هاست
   (`add_limit_bytes`, `extend_days`, ...) — چون به پنل واقعی شما دسترسی
   مستقیم ندارم، پیشنهاد می‌کنم یک بار با DevTools > Network یک ویرایش
   دستی روی پنل انجام دهید و بدنه‌ی درخواست واقعی را با
   `backend/services/config_service.py::renew_config` مقایسه کنید.
3. **نام کلید لینک VLESS در پاسخ API** (`link` به‌صورت پیش‌فرض) هم باید
   یک‌بار با DevTools تأیید شود؛ در صورت اختلاف فقط کافی‌ست
   `SULGX_LINK_FIELD` را در Environment Variables ست کنید — نیازی به
   تغییر کد نیست.
