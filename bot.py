import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, SUPER_ADMIN_ID
import database as db

from handlers import common, admin_commands, superadmin_commands, message_handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN topilmadi! .env faylni tekshiring.")
        return

    await db.init_db()
    logger.info("✅ Ma'lumotlar bazasi tayyor.")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Middlewares
    from middlewares.privacy import CommandPrivacyMiddleware
    from middlewares.throttling import ThrottlingMiddleware
    
    dp.message.middleware(ThrottlingMiddleware())
    dp.message.middleware(CommandPrivacyMiddleware())

    dp.include_router(common.router)
    dp.include_router(superadmin_commands.router)
    dp.include_router(admin_commands.router)
    dp.include_router(message_handler.router)

    logger.info(f"🚀 Bot ishga tushdi | Super Admin ID: {SUPER_ADMIN_ID}")
    
    # Start flusher task
    flusher_task = asyncio.create_task(db.start_flusher())
    
    try:
        await dp.start_polling(bot)
    finally:
        flusher_task.cancel()
        await db.flush_message_logs()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")