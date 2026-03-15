#!/bin/bash

# Ranglar
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔄 Yangilanishlar tekshirilmoqda...${NC}"

# Git pull (agar git loyiha bo'lsa)
if [ -d .git ]; then
    echo -e "${YELLOW}📥 GitHub'dan yangi o'zgarishlar olinmoqda...${NC}"
    git pull origin main || git pull origin master
else
    echo -e "${YELLOW}ℹ️  Git repository topilmadi, pull o'tkazib yuborildi.${NC}"
fi

# .env faylni tekshirish va yaratish
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 .env fayli topilmadi. .env.example dan nusxa olinmoqda...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env yaratildi. Iltimos, uni tahrirlab bot tokenini kiriting!${NC}"
    # Agar token bo'sh bo'lsa to'xtatish (ixtiyoriy, lekin foydali)
    if grep -q "BOT_TOKEN=$" .env || grep -q "BOT_TOKEN= " .env; then
        echo -e "${YELLOW}⚠️  Diqqat: .env faylida BOT_TOKEN ko'rsatilmagan. Uni to'ldirib qayta urinib ko'ring.${NC}"
    fi
fi

# Docker mavjudligini tekshirish
if ! [ -x "$(command -v docker)" ]; then
  echo '❌ Xatolik: docker o'rnatilmagan.' >&2
  exit 1
fi

# Konteynerlarni to'xtatish va qayta qurish/ishga tushirish
echo -e "${BLUE}🏗️  Konteynerlar qurilmoqda va ishga tushirilmoqda...${NC}"
docker compose down
docker compose up --build -d

echo -e "${GREEN}✅ Hammasi tayyor! Bot muvaffaqiyatli yangilandi va ishga tushdi!${NC}"
echo "📊 Loglarni ko'rish: docker compose logs -f bot"