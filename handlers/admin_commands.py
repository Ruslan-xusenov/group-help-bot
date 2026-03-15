import logging
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonRequestUsers, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from aiogram.filters import Command, CommandObject

import database as db
from config import MAX_WARNINGS, MUTE_DURATION_HOURS, SUPER_ADMIN_ID
from utils.moderation import format_user_mention

logger = logging.getLogger(__name__)
router = Router()

MUTE_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
)

ADMIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🛡️ Help")],
        [KeyboardButton(text="👤 Foydalanuvchini tanlash", request_users=KeyboardButtonRequestUsers(request_id=1, user_is_bot=False))]
    ],
    resize_keyboard=True
)

async def get_mod_menu(admin_id: int, target_id: int):
    perms = await db.get_admin_permissions(admin_id)
    keyboard = []
    
    if perms.get("warn"):
        keyboard.append([InlineKeyboardButton(text="⚠️ Ogohlantirish", callback_data=f"mod_warn_{target_id}")])
    
    mutes = []
    if perms.get("mute"):
        mutes.append(InlineKeyboardButton(text="🔇 Mute (1s)", callback_data=f"mod_mute_{target_id}_1"))
        mutes.append(InlineKeyboardButton(text="🔇 Mute (24s)", callback_data=f"mod_mute_{target_id}_24"))
    if mutes: keyboard.append(mutes)
    
    if perms.get("ban"):
        keyboard.append([InlineKeyboardButton(text="🚫 Ban", callback_data=f"mod_ban_{target_id}")])
    
    keyboard.append([InlineKeyboardButton(text="🗑️ Tozalash", callback_data=f"mod_clear_{target_id}")])
    keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="mod_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def get_role_menu(admin_id: int, target_id: int):
    perms = await db.get_admin_permissions(target_id)
    if perms is None:
        perms = {"warn": False, "mute": False, "ban": False, "delete": False, "invite": False}
    
    def get_sym(val): return "✅" if val else "❌"
    
    keyboard = [
        [InlineKeyboardButton(text=f"⚠️ Warn {get_sym(perms.get('warn'))}", callback_data=f"toggle_{target_id}_warn")],
        [InlineKeyboardButton(text=f"🔇 Mute {get_sym(perms.get('mute'))}", callback_data=f"toggle_{target_id}_mute")],
        [InlineKeyboardButton(text=f"🚫 Ban {get_sym(perms.get('ban'))}", callback_data=f"toggle_{target_id}_ban")],
        [InlineKeyboardButton(text=f"🗑️ Delete {get_sym(perms.get('delete'))}", callback_data=f"toggle_{target_id}_delete")],
        [InlineKeyboardButton(text=f"📩 Invite {get_sym(perms.get('invite'))}", callback_data=f"toggle_{target_id}_invite")],
        [InlineKeyboardButton(text="🔒 Oddiy qilish", callback_data=f"role_{target_id}_regular")],
        [InlineKeyboardButton(text="❌ Yopish", callback_data="mod_cancel")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def generate_help_text(user_id: int):
    perms = await db.get_admin_permissions(user_id)
    if not perms: return None
    
    is_super = await db.is_super_admin(user_id)
    
    text = "🛡️ <b>ADMIN BUYRUQLAR</b>\n\n"
    
    if perms.get("warn"):
        text += "⚠️ <code>/warn [target]</code> — Ogohlantirish\n"
        text += "✅ <code>/unwarn [target]</code> — Ogohlantirishni olish\n"
    
    if perms.get("mute"):
        text += "🔇 <code>/mute [target] [soat]</code> — Mute\n"
        text += "🔊 <code>/unmute [target]</code> — Mutedan chiqarish\n"
        
    if perms.get("ban"):
        text += "🚫 <code>/ban [target]</code> — Ban\n"
        text += "🔓 <code>/unban [target]</code> — Bandan chiqarish\n"
    
    if perms.get("delete"):
        text += "🗑️ <code>/clear [target] [soni]</code> — Xabarlarni tozalash\n"
    
    text += (
        "\n📊 <code>/stats</code> — Guruh statistikasi\n"
        "ℹ️ <code>/info [target]</code> — Foydalanuvchi ma'lumoti\n"
    )
    
    if is_super:
        text += (
            "\n👑 <b>ASOSIY ADMIN:</b>\n"
            "• <code>/admin [target] [nom]</code> — Admin qo'shish/nomlash\n"
            "• <code>/deladmin [target]</code> — Adminlikdan olish\n"
            "• <code>/reset_stat</code> — Statistikani o'chirish\n"
            "• <code>/add_bad_word [so'z]</code> — So'z qo'shish\n"
            "• <code>/help_super</code> — Super Help"
        )

    text += "\n\n💡 <i>[target] = ID, @username yoki xabarga reply</i>"
    return text

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

async def _require_admin(message: Message) -> bool:
    if not await db.is_admin(message.from_user.id):
        await message.answer("❌ Bu buyruq faqat adminlar uchun!")
        return False
    return True

async def _require_permission(message: Message, perm: str) -> bool:
    if await db.has_permission(message.from_user.id, perm):
        return True
    await message.answer(f"❌ Sizda bu amal uchun (<code>{perm}</code>) huquqi yo'q!", parse_mode="HTML")
    return False

async def _is_target_admin(message: Message, target_id: int) -> bool:
    if await db.is_admin(target_id):
        return True
    try:
        member = await message.chat.get_member(target_id)
        return member.status in ["administrator", "creator"]
    except Exception:
        return False

@router.message(Command("warn"))
async def warn_user_cmd(message: Message, command: CommandObject):
    if not await _require_admin(message): return
    if not await _require_permission(message, "warn"): return
    target = await _get_target(message, command)
    if not target:
        await message.answer("❗ Foydalanuvchini ko'rsating (Reply, ID yoki Username).\n<code>/warn @username</code>", parse_mode="HTML")
        return

    try:
        member = await message.chat.get_member(target)
        if member.status in ["left", "kicked"]:
            await message.answer("❌ Foydalanuvchi guruhda emas!")
            return
        u = member.user
        target_name = f"@{u.username}" if u.username else u.full_name
    except Exception:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return

    if await _is_target_admin(message, target):
        await message.answer("❌ Adminni ogohlantirib bo'lmaydi.")
        return

    count = await db.add_warning(message.chat.id, target, target_name)
    text = (
        f"⚠️ <b>Ogohlantirish</b>\n"
        f"👤 Foydalanuvchi: {target_name} [<code>{target}</code>]\n"
        f"📊 Ogohlantirishlar: {count}/{MAX_WARNINGS}\n"
        f"👮 Admin tomonidan berildi"
    )
    await message.answer(text, parse_mode="HTML")

    if count >= MAX_WARNINGS:
        try:
            until = datetime.now() + timedelta(hours=MUTE_DURATION_HOURS)
            await message.chat.restrict(user_id=target, permissions=MUTE_PERMISSIONS, until_date=until)
            await db.reset_warnings(message.chat.id, target)
            await db.log_mute(message.chat.id, target)
            await message.answer(f"🔇 ID <code>{target}</code> — {MAX_WARNINGS} ta ogohlantirish sababli <b>mute</b> qilindi.", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Mute error: {e}")

@router.message(Command("mute"))
async def mute_user_cmd(message: Message, command: CommandObject):
    if not await _require_admin(message): return
    if not await _require_permission(message, "mute"): return
    target = await _get_target(message, command)
    if not target:
        await message.answer("❗ Foydalanuvchini ko'rsating (Reply, ID yoki Username).")
        return
    
    if await _is_target_admin(message, target):
        await message.answer("❌ Adminni mute qilib bo'lmaydi.")
        return

    hours = MUTE_DURATION_HOURS
    if command.args:
        parts = command.args.split()
        idx = 0 if message.reply_to_message else 1
        if len(parts) > idx and parts[idx].isdigit():
            hours = int(parts[idx])

    try:
        until = datetime.now() + timedelta(hours=hours)
        await message.chat.restrict(user_id=target, permissions=MUTE_PERMISSIONS, until_date=until)
        await db.log_mute(message.chat.id, target)
        await message.answer(f"🔇 ID <code>{target}</code> <b>mute</b> qilindi — {hours} soat.", parse_mode="HTML")
    except Exception as e:
        await message.answer("❌ Tizimda xatolik yuz berdi. Bu haqda adminga xabar berildi.")

@router.message(Command("ban"))
async def ban_user_cmd(message: Message, command: CommandObject):
    if not await _require_admin(message): return
    if not await _require_permission(message, "ban"): return
    target = await _get_target(message, command)
    if not target:
        await message.answer("❗ Foydalanuvchini ko'rsating (Reply, ID yoki Username).")
        return
    
    if await _is_target_admin(message, target):
        await message.answer("❌ Adminni ban qilib bo'lmaydi.")
        return

    try:
        await message.chat.ban(user_id=target)
        await db.reset_warnings(message.chat.id, target)
        await db.log_ban(message.chat.id, target)
        await message.answer(f"🚫 ID <code>{target}</code> <b>ban</b> qilindi.", parse_mode="HTML")
    except Exception as e:
        await message.answer("❌ Tizimda xatolik yuz berdi. Bu haqda adminga xabar berildi.")

@router.message(Command("unban"))
async def unban_user_cmd(message: Message, command: CommandObject):
    if not await _require_admin(message): return
    if not await _require_permission(message, "ban"): return
    target = await _get_target(message, command)
    if not target:
        await message.answer("❗ Foydalanuvchini ko'rsating.")
        return
    
    try:
        await message.chat.unban(user_id=target, only_if_banned=True)
        await message.answer(f"✅ ID <code>{target}</code> bandan chiqarildi.", parse_mode="HTML")
    except Exception as e:
        await message.answer("❌ Tizimda xatolik yuz berdi. Bu haqda adminga xabar berildi.")

@router.message(Command("unmute"))
async def unmute_user_cmd(message: Message, command: CommandObject):
    if not await _require_admin(message): return
    if not await _require_permission(message, "mute"): return
    target = await _get_target(message, command)
    if not target:
        await message.answer("❗ Foydalanuvchini ko'rsating.")
        return
        
    try:
        from aiogram.types import ChatPermissions
        full_permissions = ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True
        )
        await message.chat.restrict(user_id=target, permissions=full_permissions)
        await message.answer(f"🔊 ID <code>{target}</code> mutedan chiqarildi.", parse_mode="HTML")
    except Exception as e:
        await message.answer("❌ Tizimda xatolik yuz berdi. Bu haqda adminga xabar berildi.")

@router.message(Command("unwarn"))
async def unwarn_user_cmd(message: Message, command: CommandObject):
    if not await _require_admin(message): return
    if not await _require_permission(message, "warn"): return
    target = await _get_target(message, command)
    if not target:
        await message.answer("❗ Foydalanuvchini ko'rsating.")
        return
        
    await db.reset_warnings(message.chat.id, target)
    await message.answer(f"✅ ID <code>{target}</code> ogohlantirishlari olib tashlandi.", parse_mode="HTML")

@router.message(Command("clear"))
async def clear_messages_cmd(message: Message, command: CommandObject):
    if not await _require_admin(message): return
    if not await _require_permission(message, "delete"): return
    
    amount = 100
    target_id = None
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        if command.args and command.args.isdigit():
            amount = min(int(command.args), 500)
    elif command.args:
        args = command.args.split()
        arg = args[0]
        if arg.startswith("@"):
            target_id = await db.get_id_by_username(arg)
            if len(args) > 1 and args[1].isdigit():
                amount = min(int(args[1]), 500)
        elif arg.isdigit() or (arg.startswith("-") and arg[1:].isdigit()):
             # If arg is small, assume it's amount. Otherwise it's probably a user ID.
             val = int(arg)
             if len(arg) < 6: # amount
                 amount = min(val, 500)
             else: # ID
                 target_id = val
                 if len(args) > 1 and args[1].isdigit():
                     amount = min(int(args[1]), 500)
    
    deleted = 0
    if target_id:
        msg_ids = await db.get_user_messages(message.chat.id, target_id, amount)
        for mid in msg_ids:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=mid)
                deleted += 1
            except Exception:
                continue
        if msg_ids:
            await db.delete_logged_messages(message.chat.id, msg_ids)
    else:
        current_id = message.message_id
        for i in range(amount + 1):
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=current_id - i)
                deleted += 1
            except Exception:
                continue
    
    try:
        temp_msg = await message.bot.send_message(
            chat_id=message.chat.id, 
            text=f"🗑️ <b>{deleted}</b> ta xabar o'chirildi.",
            parse_mode="HTML"
        )
        import asyncio
        await asyncio.sleep(5)
        await temp_msg.delete()
    except Exception:
        pass

@router.message(Command("info"))
async def info_cmd(message: Message, command: CommandObject):
    if not await _require_admin(message): return
    target = await _get_target(message, command)
    if not target:
        await message.answer("❗ Foydalanuvchini ko'rsating (Reply, ID yoki Username).", parse_mode="HTML")
        return

    try:
        member = await message.chat.get_member(target)
        u = member.user
        
        reg = db.get_registration_year(target)
        perms = await db.get_admin_permissions(target)
        
        status_text = "Oddiy foydalanuvchi"
        if perms: status_text = "Admin"
        if target == SUPER_ADMIN_ID: status_text = "Asosiy Admin"
        
        text = (
            f"<b>Group Help</b>      <pre>admin</pre>\n"
            f"<b>{u.full_name}</b> ning buyruqlarini boshqarish\n"
            f"<i>Moderatorlar va Muterlar har doim oddiy.</i>\n\n"
            f"🆔 ID: <code>{u.id}</code>\n"
            f"📊 Status: {status_text}\n"
            f"📅 Reg: {reg}-yil"
        )
        
        reply_markup = await get_role_menu(message.from_user.id, target)
        await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Info error: {e}")
        await message.answer("❌ Foydalanuvchi ma'lumotlarini olishda xatolik yuz berdi.")

@router.message(Command("stats"))
async def stats_cmd(message: Message):
    if not await _require_admin(message): return
    all_warns = await db.get_all_warnings(message.chat.id)
    if not all_warns:
        await message.answer("📊 Hozircha ogohlantirishlar yo'q.")
        return
    
    lines = ["📊 <b>Ogohlantirishlar statistikasi:</b>\n"]
    for uid, data in sorted(all_warns.items(), key=lambda x: -x[1]["count"]):
        lines.append(f"• {data['name']} [<code>{uid}</code>] — {data['count']}/{MAX_WARNINGS}")
    await message.answer("\n".join(lines), parse_mode="HTML")

@router.message(Command("admin", "help_admin"))
async def help_admin_cmd(message: Message):
    if not await db.is_admin(message.from_user.id): return
    
    perms = await db.get_admin_permissions(message.from_user.id)
    text = "🛡️ <b>ADMIN BUYRUQLAR</b>\n\n"
    
    if perms.get("warn"):
        text += "⚠️ <code>/warn [target]</code> — Ogohlantirish\n"
        text += "✅ <code>/unwarn [target]</code> — Ogohlantirishni olish\n"
    
    if perms.get("mute"):
        text += "🔇 <code>/mute [target] [soat]</code> — Mute\n"
        text += "🔊 <code>/unmute [target]</code> — Mutedan chiqarish\n"
        
    if perms.get("ban"):
        text += "🚫 <code>/ban [target]</code> — Ban\n"
        text += "🔓 <code>/unban [target]</code> — Bandan chiqarish\n"
    
    if perms.get("delete"):
        text += "🗑️ <code>/clear [target] [soni]</code> — Xabarlarni tozalash\n"
    
    text += (
        "\n📊 <code>/stats</code> — Guruh statistikasi\n"
        "ℹ️ <code>/info [target]</code> — Foydalanuvchi ma'lumoti\n\n"
        "💡 <i>[target] = ID, @username yoki xabarga reply</i>"
    )
    markup = ADMIN_KEYBOARD if message.chat.type == "private" else None
    await message.answer(text, reply_markup=markup, parse_mode="HTML")

@router.message(Command("help_sadmin"))
async def help_sadmin_cmd(message: Message, bot: Bot):
    if not await db.is_admin(message.from_user.id):
        return # Ignore non-admins completely
    
    # 1. Provide button to PM
    if message.chat.type != "private":
        bot_user = await bot.get_me()
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Botga o'tish", url=f"https://t.me/{bot_user.username}?start=help")]
        ])
        
        # Original message will be deleted by middleware or we can do it here for safety
        try: await message.delete()
        except: pass
        
        info_msg = await message.answer(
            f"🛡️ <b>{message.from_user.full_name}</b>, sizning ruxsatlaringiz botga yuborildi.",
            reply_markup=kb
        )
        import asyncio
        await asyncio.sleep(5)
        await info_msg.delete()
    
    # 2. Try to send PM
    try:
        help_text = await generate_help_text(message.from_user.id)
        if help_text:
            await bot.send_message(chat_id=message.from_user.id, text=help_text)
    except Exception:
        # If user hasn't started bot, they will see the button in the group
        pass

@router.message(F.text == "📊 Statistika")
async def btn_stats(message: Message):
    await stats_cmd(message)

@router.message(F.text == "🛡️ Help")
async def btn_help(message: Message):
    await help_admin_cmd(message)

@router.message(F.users_shared)
async def handle_user_shared(message: Message):
    if not await _require_admin(message): return
    user_id = message.users_shared.users[0].user_id
    reply_markup = await get_mod_menu(message.from_user.id, user_id)
    await message.answer(
        f"👤 Foydalanuvchi tanlandi: <code>{user_id}</code>\nNima qilmoqchisiz?",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("mod_"))
async def handle_mod_callback(query: CallbackQuery):
    if not await db.is_admin(query.from_user.id):
        await query.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    data = query.data
    if data == "mod_cancel":
        await query.message.edit_text("❌ Bekor qilindi.")
        return
    
    parts = data.split("_")
    action = parts[1]
    user_id = int(parts[2])

    if not await db.has_permission(query.from_user.id, action):
        await query.answer(f"❌ Sizda {action} huquqi yo'q!", show_alert=True)
        return
    
    if action == "warn":
        member = await query.message.chat.get_member(user_id)
        name = member.user.full_name
        count = await db.add_warning(query.message.chat.id, user_id, name)
        await query.message.answer(f"⚠️ {name} [<code>{user_id}</code>] ogohlantirildi ({count}/{MAX_WARNINGS})", parse_mode="HTML")
    elif action == "mute":
        hours = int(parts[3])
        until = datetime.now() + timedelta(hours=hours)
        await query.message.chat.restrict(user_id=user_id, permissions=MUTE_PERMISSIONS, until_date=until)
        await db.log_mute(query.message.chat.id, user_id)
        await query.message.answer(f"🔇 ID <code>{user_id}</code> mute qilindi ({hours} soat).", parse_mode="HTML")
    elif action == "ban":
        await query.message.chat.ban(user_id=user_id)
        await db.log_ban(query.message.chat.id, user_id)
        await query.message.answer(f"🚫 ID <code>{user_id}</code> ban qilindi.", parse_mode="HTML")
    elif action == "clear":
        # Clear recent messages from this user (if possible) or just generalized clear
        # Here we do a generalized clear for the last 50 messages as a quick action
        current_id = query.message.message_id
        for i in range(50):
            try:
                await query.message.bot.delete_message(chat_id=query.message.chat.id, message_id=current_id - i)
            except: continue
        return # already deleted menu
    
    await query.message.delete()

@router.callback_query(F.data.startswith("toggle_"))
async def handle_toggle_callback(query: CallbackQuery):
    if not await db.is_super_admin(query.from_user.id):
        await query.answer("❌ Faqat Asosiy Admin huquqlarni o'zgartira oladi!", show_alert=True)
        return

    parts = query.data.split("_")
    target_id = int(parts[1])
    perm_to_toggle = parts[2]

    current_perms = await db.get_admin_permissions(target_id)
    if current_perms is None:
        await query.answer("❌ Admin topilmadi.")
        return

    new_val = not current_perms.get(perm_to_toggle, False)
    update_data = {f"can_{perm_to_toggle}": int(new_val)}
    
    await db.update_admin_permissions(target_id, **update_data)
    
    try:
        updated_perms = await db.get_admin_permissions(target_id)
        if updated_perms:
            await query.message.chat.promote(
                user_id=target_id,
                can_delete_messages=bool(updated_perms.get("delete", False)),
                can_restrict_members=bool(updated_perms.get("mute", False)) or bool(updated_perms.get("ban", False)),
                can_pin_messages=True,
                can_invite_users=bool(updated_perms.get("invite", False))
            )
    except Exception as e:
        logger.error(f"Toggle sync error: {e}")

    await query.answer(f"✅ {perm_to_toggle.capitalize()} holati o'zgartirildi.")
    
    reply_markup = await get_role_menu(query.from_user.id, target_id)
    try:
        await query.message.edit_reply_markup(reply_markup=reply_markup)
    except Exception:
        pass

@router.callback_query(F.data.startswith("role_"))
async def handle_role_callback(query: CallbackQuery):
    if not await db.is_super_admin(query.from_user.id):
        await query.answer("❌ Faqat Asosiy Admin huquqlarni o'zgartira oladi!", show_alert=True)
        return
    
    parts = query.data.split("_")
    target_id = int(parts[1])
    role = parts[2]
    
    if role == "regular":
        await db.remove_admin(target_id)
        try:
            await query.message.chat.promote(
                user_id=target_id,
                can_change_info=False,
                can_post_messages=False,
                can_edit_messages=False,
                can_delete_messages=False,
                can_invite_users=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_promote_members=False
            )
            await query.message.edit_text(f"✅ ID {target_id} endi oddiy foydalanuvchi.")
        except Exception as e:
            logger.error(f"Demote error: {e}")
            await query.answer("⚠️ Guruhda adminlikdan olishda xato.")
            
        await query.answer("✅ Foydalanuvchi endi oddiy.")
    else:
        pass