from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

import database as db

router = Router()

@router.message(Command("start"))
async def start_cmd(message: Message, command: CommandObject):
    if command.args == "help":
        if await db.is_admin(message.from_user.id):
            from handlers.admin_commands import generate_help_text
            help_text = await generate_help_text(message.from_user.id)
            if help_text:
                await message.answer(help_text, parse_mode="HTML")
                return
    
    text = (
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Men guruhlarni nazorat qiluvchi botman.\n"
        "Guruhda tartibni saqlashga, haqoromlarni tozalashga yordam beraman."
    )
    if await db.is_admin(message.from_user.id):
        text += "\n\nSiz adminsiz! Buyruqlarni ko'rish uchun <code>/help_sadmin</code> yozing."
    
    await message.answer(text, parse_mode="HTML")

@router.message(Command("help"))
async def help_cmd(message: Message):
    text = (
        "ℹ️ <b>BOT YORDAMI</b>\n\n"
        "Guruhda rasm/video va haqoratli so'zlar taqiqlangan.\n"
        "Qoidabuzarlarga avtomatik ogohlantirish beriladi.\n"
        "3 ta ogohlantirishdan so'ng guruhdan vaqtincha chetlatilasiz (mute)."
    )
    await message.answer(text, parse_mode="HTML")