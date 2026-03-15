# 🛡️ Oxun Boboyev Bot — Guruh Moderatsiya Boti

Zamonaviy, tezkor va xavfsiz Telegram guruh moderatsiyasi boti. **Aiogram 3.x** va **SQLAlchemy (SQLite)** asosida yaratilgan.

---

## ⚡ Vazifalar
- **Avtوماتik Moderatsiya**: Haqoratli so'zlarni bazadan tekshiradi va o'chiradi.
- **Media Nazorati**: Rasm, video, fayl va boshqa medialarni avtomatik o'chira oladi (faqat adminlarga ruxsat).
- **Aqlli Taqiqlash**: 3 ta ogohlantirishdan so'ng foydalanuvchini avtomatik mute qiladi.
- **User Registry**: Foydalanuvchilarning @username'larini bazaga saqlab boradi (Username orqali boshqarish uchun).
- **Granulyar Ruxsatnomalar**: Adminlarga alohida huquqlar (Warn, Mute, Ban) berish imkoniyati.

---

## 🚀 Ishga Tushirish

### 1. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 2. .env faylini to'ldirish
Loyiha ildizida `.env` faylini yarating:
```env
BOT_TOKEN=BotFather_token
SUPER_ADMIN_ID=Asosiy_Admin_ID
MAX_WARNINGS=3
MUTE_DURATION_HOURS=168
DB_URL=sqlite+aiosqlite:///data/bot_database.sqlite
```

### 3. Ishga tushirish
```bash
python bot.py
```

---

## 👑 Admin Ierarxiyasi

| Daraja | Kim | Imkoniyatlari |
|--------|-----|---------------|
| **Asosiy Admin** | `.env` dagi ID | To'liq nazorat, Admin qo'shish/o'chirish, Ruxsatnomalarni belgilash |
| **Admin** | Asosiy admin tayinlaydi | Berilgan huquqlarga ko'ra (Warn, Mute, Ban) moderatsiya |

---

## 🛠️ Buyruqlar

Barcha moderatsiya buyruqlari **ID**, **@username** yoki **Reply** orqali ishlaydi.

### 👑 Asosiy Admin Buyruqlari (`/help_super`)
| Buyruq | Vazifasi |
|--------|----------|
| `/addadmin [target]` | Yangi admin qo'shish |
| `/deladmin [target]` | Adminni o'chirish |
| `/setperm [target] [warn/mute/ban] [1/0]` | Admin huquqlarini belgilash |
| `/adminlist` | Adminlar ro'yxati va huquqlari |
| `/add_bad_word [so'z]` | Haqoratli so'z qo'shish |
| `/del_bad_word [so'z]` | Haqoratli so'z o'chirish |
| `/bad_words` | Barcha haqoratli so'zlar ro'yxati |

### 🛡️ Moderatsiya Buyruqlari (`/help_admin`)
| Buyruq | Vazifasi |
|--------|----------|
| `/warn [target]` | Ogohlantirish berish |
| `/unwarn [target]` | Ogohlantirishlarni olib tashlash |
| `/mute [target] [soat]` | Ma'lum vaqtga mute qilish |
| `/unmute [target]` | Mute cheklovini olib tashlash |
| `/ban [target]` | Guruhdan ban qilish |
| `/unban [target]` | Bandan chiqarish |
| `/info [target]` | Foydalanuvchi haqida to'liq ma'lumot (Stats, History, RegDate) |
| `/stats` | Guruhdagi ogohlantirishlar statistikasi |

---

## 📂 Loyiha Tuzilmasi

```
oxun-boboyev-bot/
├── bot.py                      # Botni ishga tushirish
├── config.py                   # Konfiguratsiya
├── database.py                 # SQLAlchemy modellari va baza operatsiyalari
├── data/                       # Ma'lumotlar bazasi papkasi
│   └── bot_database.sqlite
├── handlers/
│   ├── message_handler.py      # Xabarlarni filtrlash va foydalanuvchi registratsiyasi
│   ├── admin_commands.py       # Moderatsiya buyruqlari
│   └── superadmin_commands.py  # Asosiy admin buyruqlari
├── utils/                      # Yordamchi vositalar
├── requirements.txt
└── .env
```

---

## 📝 Eslatmalar
- **Username Resolution**: Bot biror foydalanuvchini `@username` orqali topishi uchun, u foydalanuvchi bot bor guruhda kamida **bitta xabar** yozgan bo'lishi kerak.
- **Bazani ko'chirish**: Agar eski JSON bazadan o'tayotgan bo'lsangiz, `migrate_json_to_db.py` skripti (mavjud bo'lsa) orqali ma'lumotlarni ko'chiring.