# 🤖 Oxun Boboyev Bot — To'liq Qo'llanma

Ushbu bot guruhlarni samarali moderatsiya qilish, spamdan himoya qilish va adminlarni boshqarish uchun mo'ljallangan.

---

## 👑 Asosiy Admin (Super Admin) Buyruqlari
Asosiy admin botning to'liq egasi hisoblanadi va quyidagi amallarni bajara oladi:

- `/adminlist` — Barcha tayinlangan adminlar va ularning huquqlarini ko'rishingiz mumkin.
- `/admin [target] [nom]` — Yangi admin qo'shish, uning nomini o'zgaritirish va huquqlarini (inline menu orqali) belgilash.
- `/deladmin [target]` — Adminni guruhdan va bot bazasidan olib tashlash.
- `/reset_stat` — Barcha guruh statistikasini (warn, mute, ban) butunlay tozalash.
- `/add_bad_word [so'z]` — Taqiqlangan so'zlar ro'yxatiga yangi so'z qo'shish.
- `/del_bad_word [so'z]` — Taqiqlangan so'zlar ro'yxatidan so'zni o'chirish.
- `/bad_words` — Taqiqlangan so'zlar ro'yxatini ko'rish.
- `/help_super` — Asosiy admin uchun yordam menyusi.

---

## 🛡️ Admin Buyruqlari
Tayinlangan adminlar o'zlariga berilgan huquqlar doirasida quyidagilarni bajara oladi:

- `/warn [target]` — Foydalanuvchiga ogohlantirish berish. (3 ta ogohlantirishdan so'ng avto-mute).
- `/unwarn [target]` — Ogohlantirishlarni nolga tushirish.
- `/clear [soni]` — Xabarlarni ommaviy o'chirish (masalan: `/clear 50`).
- `/mute [target] [soat]` — Foydalanuvchini yozishdan cheklash.
- `/unmute [target]` — Mutedan chiqarish.
- `/ban [target]` — Foydalanuvchini guruhdan haydash.
- `/unban [target]` — Bandan chiqarish.
- `/info [target]` — Foydalanuvchi haqida batafsil ma'lumot va moderatsiya statistikasi.
- `/stats` — Guruhdagi umumiy moderatsiya statistikasi.
- `/help_sadmin` / `/admin` — Sizga ruxsat berilgan barcha buyruqlar ro'yxatini bot orqali shaxsiy xabarda (PM) ko'rish.

---

## 🔒 Xavfsizlik va Avto-Moderatsiya
Bot guruhning toza va xavfsiz bo'lishini avtomatik ta'minlaydi:

1.  **Haqoratli so'zlar**: Taqiqlangan so'z ishlatilganda, bot xabarni o'chiradi va foydalanuvchini darhol **5 daqiqa**ga mute qiladi.
2.  **Reklama va Linklar**: Guruhga link yuborilganda, bot xabarni o'chiradi va foydalanuvchini **5 daqiqa**ga mute qiladi.
3.  **Media Cheklovi**: Oddiy foydalanuvchilar faqat matn yozishi mumkin. Stiker, rasm yoki boshqa fayllar yuborilganda bot xabarni o'chiradi.
4.  **Admin Daxlsizligi**: Telegram guruh adminlari (hatto botda ro'yxatda bo'lmasa ham) bot moderatsiyasidan to'liq daxlsizdir.
5.  **Shaffof Boshqaruv**: Har bir admin harakati guruhda qayd etiladi.

---

## 🤫 Maxfiylik (Privacy Mode)
Adminlar guruhda `/` bilan boshlanadigan har qanday buyruqni yuborganda:
- Bot buyruq xabarini darhol o'chiradi.
- Bot vaqtinchalik (5 soniya) "🛡️ Bu buyruq faqat adminlar uchun" degan xabarni ko'rsatadi.
- Bu orqali oddiy foydalanuvchilar adminlar qanday buyruqlardan foydalanayotganini ko'rmaydilar.

---

## 💡 Qo'shimcha Ma'lumot
- `[target]` sifatida foydalanuvchi IDsi, @usernamesi yoki uning xabariga reply qilishdan foydalanish mumkin.
- Bot guruhda to'liq ishlashi uchun unga "Adminlarni tayinlash" (Add new admins) va "Xabarlarni o'chirish" (Delete messages) huquqlari berilishi shart.
