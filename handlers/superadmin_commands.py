import logging
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonRequestUsers
from aiogram.filters import Command, CommandObject

import database as db
from config import SUPER_ADMIN_ID

logger = logging.getLogger(__name__)
router = Router()

SUPER_ADMIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="👑 Super Help")],
        [KeyboardButton(text="🛡️ Adminni boshqarish", request_users=KeyboardButtonRequestUsers(request_id=2, user_is_bot=False))],
        [KeyboardButton(text="🛡️ Admin Yordam")]
    ],
    resize_keyboard=True
)

async def _require_super_admin(message: Message) -> bool:
    if message.from_user.id != SUPER_ADMIN_ID:
        await message.answer("❌ Bu buyruq faqat <b>Asosiy Admin</b> uchun!", parse_mode="HTML")
        return False
    return True

async def _get_target(message: Message, command: CommandObject = None) -> int | None:
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    
    if command and command.args:
        arg = command.args.split()[0]
        if arg.startswith("@"):
            return await db.get_id_by_username(arg)
        if arg.isdigit() or (arg.startswith("-") and arg[1:].isdigit()):
            return int(arg)
    return None

# Removed add_admin_cmd as /admin now handles addition, title and roles.

@router.message(Command("deladmin"))
async def del_admin_cmd(message: Message, command: CommandObject):
    if not await _require_super_admin(message): return
    target = await _get_target(message, command)
    if not target:
        await message.answer("❗ Admin IDsini, @usernameni kiriting yoki xabarga reply qiling.", parse_mode="HTML")
        return
    
    if target == SUPER_ADMIN_ID:
        await message.answer("❌ Asosiy adminni o'chirib bo'lmaydi.")
        return

    if await db.remove_admin(target):
        await message.answer(f"✅ ID <code>{target}</code> adminlikdan olib tashlandi.", parse_mode="HTML")
        if message.chat.type in ["group", "supergroup"]:
            try:
                await message.chat.promote(
                    user_id=target,
                    is_anonymous=False,
                    can_manage_chat=False,
                    can_post_messages=False,
                    can_edit_messages=False,
                    can_delete_messages=False,
                    can_manage_video_chats=False,
                    can_restrict_members=False,
                    can_promote_members=False,
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False
                )
                await message.answer("ℹ️ Foydalanuvchi guruhda adminlikdan olindi.")
            except Exception as e:
                logger.error(f"Demotion error: {e}")
                await message.answer("⚠️ Guruhda xatolik yuz berdi. Bu haqda adminga xabar berildi.")
    else:
        await message.answer("ℹ️ Bu foydalanuvchi admin emas edi.")

@router.message(Command("adminlist"))
async def admin_list_cmd(message: Message):
    if not await _require_super_admin(message): return
    admins = await db.get_admins()
    text = f"👑 <b>Admin ro'yxati</b>\n\n⭐ Asosiy Admin: <code>{SUPER_ADMIN_ID}</code>"
    
    if admins:
        text += "\n\n"
        for uid in admins:
            async with db.async_session() as session:
                from sqlalchemy import select
                res = await session.execute(select(db.UserRegistry).where(db.UserRegistry.user_id == uid))
                user = res.scalar_one_or_none()
                
                perms = await db.get_admin_permissions(uid)
                p_text = []
                if perms.get("warn"): p_text.append("W")
                if perms.get("mute"): p_text.append("M")
                if perms.get("ban"): p_text.append("B")
                p_str = f"[{'|'.join(p_text)}]" if p_text else "[Yo'q]"

                if user:
                    name = f"@{user.username}" if user.username else user.full_name
                    text += f"🛡️ <b>{name}</b> <code>{p_str}</code> [<code>{uid}</code>]\n"
                else:
                    text += f"🛡️ Admin <code>{p_str}</code>: <code>{uid}</code>\n"
    else:
        text += "\n(qo'shimcha admin yo'q)"
    await message.answer(text, parse_mode="HTML")

@router.message(Command("admin"), F.from_user.id == SUPER_ADMIN_ID)
async def admin_title_cmd(message: Message, command: CommandObject):
    """Super Admin command to set custom titles and roles for admins"""
    from handlers.admin_commands import help_admin_cmd, get_role_menu
    
    # If no args, show help
    if not command.args:
        await help_admin_cmd(message)
        return

    target = await _get_target(message, command)
    if not target:
        await message.answer("❗ Admin IDsini, @usernameni kiriting yoki xabarga reply qiling.", parse_mode="HTML")
        return

    # Parse title
    custom_title = None
    args = command.args.split() if command.args else []
    
    # If target found via reply, entire command.args is the title
    if message.reply_to_message:
        custom_title = command.args
    else:
        # If target found via first arg, remaining args are the title
        if len(args) > 1:
            custom_title = " ".join(args[1:])

    # 1. Add to database if not already
    if not await db.is_admin(target):
        await db.add_admin(target)
        await message.answer(f"✅ ID <code>{target}</code> bazaga admin sifatida qo'shildi.", parse_mode="HTML")

    # 2. Promote and set title in Telegram
    if message.chat.type in ["group", "supergroup"]:
        try:
            # Promote if not already
            member = await message.chat.get_member(target)
            if member.status not in ["administrator", "creator"]:
                await message.chat.promote(
                    user_id=target,
                    can_delete_messages=True,
                    can_restrict_members=True,
                    can_pin_messages=True,
                    can_invite_users=True
                )
                await message.answer("ℹ️ Foydalanuvchi guruhda rasmiy admin qilindi.")

            # Set title if provided
            if custom_title:
                try:
                    await message.bot.set_chat_administrator_custom_title(
                        chat_id=message.chat.id,
                        user_id=target,
                        custom_title=custom_title
                    )
                    await message.answer(f"🏷️ Admin nomi: <b>{custom_title}</b>", parse_mode="HTML")
                except Exception as te:
                    logger.error(f"Title error: {te}")
                    await message.answer("⚠️ Nom o'rnatishda xato yuz berdi.")
        except Exception as e:
            logger.error(f"Promotion error: {e}")
            await message.answer("⚠️ Telegram huquqlarini berishda xato yuz berdi.")

    # 3. Show role menu for granular permissions
    reg = db.get_registration_year(target)
    perms = await db.get_admin_permissions(target)
    status_text = "Admin"
    if target == SUPER_ADMIN_ID: status_text = "Asosiy Admin"
    
    try:
        member = await message.chat.get_member(target)
        u = member.user
        text = (
            f"<b>Adminni boshqarish</b>\n\n"
            f"🆔 ID: <code>{u.id}</code>\n"
            f"👤 Ism: {u.full_name}\n"
            f"📊 Status: {status_text}\n"
            f"📅 Reg: {reg}-yil\n\n"
            f"👇 Quyidagidan uning huquqlarini (rolini) tanlang:"
        )
        reply_markup = await get_role_menu(message.from_user.id, target)
        await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Role menu error: {e}")
        await message.answer("❌ Tizimda xatolik yuz berdi.")

@router.message(Command("setperm"))
async def set_perm_cmd(message: Message, command: CommandObject):
    if not await _require_super_admin(message): return
    if not command.args or len(command.args.split()) < 3:
        await message.answer("❗ Format: <code>/setperm [target] [warn/mute/ban] [1/0]</code>", parse_mode="HTML")
        return
        
    parts = command.args.split()
    target_str = parts[0]
    perm = parts[1].lower()
    value = parts[2]
    
    if perm not in ["warn", "mute", "ban"]:
        await message.answer("❌ Faqat: <code>warn</code>, <code>mute</code>, <code>ban</code>", parse_mode="HTML")
        return
    
    if value not in ["1", "0"]:
        await message.answer("❌ Qiymat 1 (bor) yoki 0 (yo'q) bo'lishi kerak.")
        return
    
    # Resolve target
    if target_str.startswith("@"):
        target_id = await db.get_id_by_username(target_str)
    elif target_str.isdigit():
        target_id = int(target_str)
    else:
        target_id = None
        
    if not target_id and message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        
    if not target_id:
        await message.answer("❌ Admin topilmadi.")
        return
        
    if target_id == SUPER_ADMIN_ID:
        await message.answer("❌ Asosiy admin huquqlarini o'zgartirib bo'lmaydi.")
        return

    update_data = {f"can_{perm}": int(value)}
    if await db.update_admin_permissions(target_id, **update_data):
        status = "berildi" if value == "1" else "olib tashlandi"
        await message.answer(f"✅ ID <code>{target_id}</code> uchun <b>{perm}</b> huquqi {status}.", parse_mode="HTML")
    else:
        await message.answer("❌ Xato: Bu foydalanuvchi admin emas.")

@router.message(Command("add_bad_word"))
async def add_bw_cmd(message: Message, command: CommandObject):
    if not await _require_super_admin(message): return
    if not command.args:
        await message.answer("❗ So'zni kiriting.")
        return
    
    word = command.args.lower().strip()
    if await db.add_custom_bad_word(word):
        await message.answer(f"✅ <code>{word}</code> qo'shildi.", parse_mode="HTML")
    else:
        await message.answer("ℹ️ Allaqachon mavjud.")

@router.message(Command("del_bad_word"))
async def del_bw_cmd(message: Message, command: CommandObject):
    if not await _require_super_admin(message): return
    if not command.args:
        await message.answer("❗ So'zni kiriting.")
        return
    
    word = command.args.lower().strip()
    if await db.remove_custom_bad_word(word):
        await message.answer(f"✅ <code>{word}</code> o'chirildi.", parse_mode="HTML")
    else:
        await message.answer("ℹ️ Topilmadi.")

@router.message(Command("bad_words"))
async def bw_list_cmd(message: Message):
    if not await _require_super_admin(message): return
    custom = await db.get_custom_bad_words()
    text = f"🚫 <b>Haqoratli so'zlar</b>\n📦 Bazadagi jami: {len(custom)} ta"
    if custom:
        display_list = custom[:50]
        text += "\n\n<b>So'zlar:</b>\n" + "\n".join([f"• <code>{w}</code>" for w in display_list])
        if len(custom) > 50:
            text += f"\n\n... va yana {len(custom)-50} ta."
    await message.answer(text, parse_mode="HTML")

@router.message(Command("reset_stat"))
async def reset_stat_cmd(message: Message):
    if not await _require_super_admin(message): return
    await db.reset_all_chat_stats(message.chat.id)
    await message.answer("✅ Guruh statistikasi (ogohlantirishlar, mute, ban) butunlay tozalandi.")

@router.message(Command("help_super"))
async def help_super_cmd(message: Message):
    if not await _require_super_admin(message): return
    text = (
        "👑 <b>ASOSIY ADMIN BUYRUQLAR</b>\n\n"
        "👥 <b>Adminlar:</b>\n"
        "• <code>/admin [target] [nom]</code> — Admin qo'shish/nomlash va huquqlar\n"
        "• <code>/deladmin [target]</code> — Adminlikdan olish\n"
        "• <code>/adminlist</code> — Ro'yxat\n\n"
        "🚫 <b>So'zlar:</b>\n"
        "• <code>/add_bad_word [so'z]</code> | <code>/del_bad_word</code>\n"
        "• <code>/bad_words</code>\n\n"
        "🛡️ <b>Moderatsiya:</b>\n"
        "• <code>/warn</code> | <code>/unwarn</code>\n"
        "• <code>/mute</code> | <code>/unmute</code>\n"
        "• <code>/ban</code> | <code>/unban</code>\n"
        "• <code>/info [target]</code> | <code>/stats</code>\n"
        "• <code>/reset_stat</code> — Statistikani tozalash\n\n"
        "📖 <code>/help_admin</code> — Batafsil"
    )
    markup = SUPER_ADMIN_KEYBOARD if message.chat.type == "private" else None
    await message.answer(text, reply_markup=markup, parse_mode="HTML")

@router.message(F.text == "👑 Super Help")
async def btn_super_help(message: Message):
    await help_super_cmd(message)

@router.message(F.text == "🛡️ Admin Yordam")
async def btn_admin_help(message: Message):
    from handlers.admin_commands import help_admin_cmd
    await help_admin_cmd(message)

@router.message(F.users_shared)
async def handle_super_user_shared(message: Message):
    if not await _require_super_admin(message): return
    uid = message.users_shared.users[0].user_id
    rid = message.users_shared.request_id
    
    if rid == 2: # Add
        if await db.add_admin(uid):
            await message.answer(f"✅ <code>{uid}</code> admin qilindi.", parse_mode="HTML")
            if message.chat.type in ["group", "supergroup"]:
                try:
                    await message.chat.promote(
                        user_id=uid,
                        can_delete_messages=True,
                        can_restrict_members=True,
                        can_pin_messages=True,
                        can_invite_users=True
                    )
                    await message.answer("ℹ️ Foydalanuvchi guruhda ham rasmiy admin qilindi.")
                    # Show role menu automatically
                    from handlers.admin_commands import get_role_menu
                    reply_markup = await get_role_menu(message.from_user.id, uid)
                    await message.answer("👇 Endi uning huquqlarini belgilang:", reply_markup=reply_markup)
                except Exception as e:
                    logger.error(f"Promotion error: {e}")
                    err_msg = str(e)
                    if "not enough rights" in err_msg.lower():
                        await message.answer("❌ <b>Xato:</b> Botda foydalanuvchini admin qilish uchun huquq yetarli emas.\n\n"
                                             "💡 Iltimos, botni admin qiling va unga <b>'Yangilarini tayinlash' (Add new admins)</b> huquqini bering.", parse_mode="HTML")
                    else:
                        await message.answer("⚠️ Guruhda admin qilishda xatolik yuz berdi.")
        else:
            await message.answer("ℹ️ Allaqachon admin.")
    elif rid == 3:
        if await db.remove_admin(uid):
            await message.answer(f"✅ <code>{uid}</code> adminlikdan olindi.", parse_mode="HTML")
            if message.chat.type in ["group", "supergroup"]:
                try:
                    await message.chat.promote(
                        user_id=uid,
                        can_manage_chat=False,
                        can_delete_messages=False,
                        can_restrict_members=False,
                        can_pin_messages=False,
                        can_invite_users=False
                    )
                    await message.answer("ℹ️ Foydalanuvchi guruhda adminlikdan olindi.")
                except Exception as e:
                    logger.error(f"Demotion error: {e}")
                    await message.answer("⚠️ Guruhda adminlikdan olishda xatolik yuz berdi.")
        else:
            await message.answer("ℹ️ Admin emas edi.")