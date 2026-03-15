import asyncio
import logging
from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
import database as db

logger = logging.getLogger(__name__)

class CommandPrivacyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Only handle messages in groups/supergroups
        if event.chat.type not in ["group", "supergroup"]:
            return await handler(event, data)

        # Check if it's a command (starts with /)
        text = event.text or event.caption or ""
        if text.startswith("/"):
            # 1. Delete the command trigger immediately
            try:
                await event.delete()
            except Exception as e:
                logger.error(f"Failed to delete command trigger: {e}")

            # 2. If it's an admin, send temporary notification
            user_id = event.from_user.id
            is_admin = await db.is_admin(user_id)
            if not is_admin:
                # Check actual Telegram admin status
                try:
                    member = await event.chat.get_member(user_id)
                    if member.status in ["administrator", "creator"]:
                        is_admin = True
                except Exception:
                    pass

            if is_admin and user_id != db.SUPER_ADMIN_ID:
                try:
                    msg = await event.answer("🛡️ <b>Bu xabar faqat admin uchun</b>", parse_mode="HTML")
                    # Delete notification after 5 seconds
                    async def delete_notice(m: Message):
                        await asyncio.sleep(1)
                        try:
                            await m.delete()
                        except Exception:
                            pass
                    
                    # Run deletion in background
                    asyncio.create_task(delete_notice(msg))
                except Exception as e:
                    logger.error(f"Failed to send/delete privacy notice: {e}")

        # Continue to the actual handler
        return await handler(event, data)
