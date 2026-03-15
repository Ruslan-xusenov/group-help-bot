import logging
from datetime import datetime, timedelta
from typing import Optional
from aiogram import Router, F, Bot
from aiogram.types import Message, ChatPermissions, ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER

import database as db
from config import MAX_WARNINGS, MUTE_DURATION_MINUTES
from utils.moderation import contains_bad_word, is_media_message, format_user_mention, contains_emoji

logger = logging.getLogger(__name__)
router = Router()

MUTE_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
)

TEXT_ONLY_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
)

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group_message(message: Message, bot: Bot):
    if not message.from_user or message.from_user.is_bot:
        return

    if await db.is_admin(message.from_user.id):
        return
    try:
        member = await message.chat.get_member(message.from_user.id)
        if member.status in ["administrator", "creator"]:
            return
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")

    user = message.from_user
    await db.register_user(user.id, user.username, user.full_name)
    
    display_name = f"@{user.username}" if user.username else user.full_name
    
    await db.update_user_name_and_history(message.chat.id, user.id, display_name)

    text = message.text or message.caption or ""
    
    if is_media_message(message) or contains_emoji(text):
        try:
            await message.delete()
        except Exception:
            pass
        
        reason = "📵 Faqat matnli xabarlar yuborishga ruxsat berilgan."
        if contains_emoji(text) and not is_media_message(message):
             reason = "📵 Emojilardan foydalanish taqiqlangan."
             
        count = await db.add_warning(message.chat.id, user.id, display_name)
        await _respond_warning(message, reason, count)
        await _check_mute_logic(message, user.id, count)
        return
    
    entities = message.entities or message.caption_entities or []
    has_link = any(e.type in ["url", "text_link"] for e in entities)
    
    if has_link:
        try:
            await message.delete()
        except Exception:
            pass
        
        await db.reset_warnings(message.chat.id, user.id)
        return

    found, word = await contains_bad_word(text)
    if found:
        try:
            await message.delete()
        except Exception:
            pass
        
        await db.reset_warnings(message.chat.id, user.id)
        await _check_mute_logic(message, user.id, MAX_WARNINGS, reason=f"Sokish/Haqorat ishlatildi: {word}")
        return

async def _respond_warning(message: Message, reason: str, count: int):
    user_mention = format_user_mention(message.from_user)
    next_warn = "❗ Yana bir ogohlantirishdan so'ng mute qilinasiz!" if count == MAX_WARNINGS - 1 else ""
    text = (
        f"⚠️ <b>Ogohlantirish {count}/{MAX_WARNINGS}</b>\n"
        f"👤 Foydalanuvchi: {user_mention}\n"
        f"📋 Sabab: {reason}\n\n"
        f"{next_warn}"
    )
    await message.answer(text, parse_mode="HTML")

async def _check_mute_logic(message: Message, user_id: int, count: int, reason: Optional[str] = None):
    if count >= MAX_WARNINGS:
        try:
            until = datetime.now() + timedelta(minutes=MUTE_DURATION_MINUTES)
            await message.chat.restrict(user_id=user_id, permissions=MUTE_PERMISSIONS, until_date=until)
            await db.reset_warnings(message.chat.id, user_id)
            await db.log_mute(message.chat.id, user_id)
            user_mention = format_user_mention(message.from_user)
            
            mute_reason = reason or f"{MAX_WARNINGS} ta ogohlantirish oldi"
            await message.answer(
                f"🔇 <b>MUTE</b>\n"
                f"👤 {user_mention}\n"
                f"⏳ Muddat: {MUTE_DURATION_MINUTES} minut\n"
                f"📋 Sabab: {mute_reason}",
                parse_mode="HTML"
            )
        except Exception as e:
            await message.answer("❌ Tizimda xatolik yuz berdi (Avto-mute). Bu haqda adminga xabar berildi.")

@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    user = event.new_chat_member.user
    if user.is_bot:
        return
    
    if await db.is_admin(user.id):
        return

    try:
        await event.chat.restrict(user_id=user.id, permissions=TEXT_ONLY_PERMISSIONS)
    except Exception as e:
        logger.error(f"Join restriction error: {e}")