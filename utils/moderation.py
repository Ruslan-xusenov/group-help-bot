import emoji
from database import get_custom_bad_words

async def contains_bad_word(text: str) -> tuple[bool, str]:
    if not text:
        return False, ""
    text_lower = text.lower()

    all_bad_words = await get_custom_bad_words()

    for word in all_bad_words:
        if word in text_lower:
            return True, word
    return False, ""


def is_media_message(message) -> bool:
    return any([
        message.photo,
        message.video,
        message.audio,
        message.document,
        message.sticker,
        message.animation,
        message.voice,
        message.video_note,
        message.dice,
        message.poll,
        message.location,
        message.contact,
        message.venue,
        message.game,
        message.story
    ])

def format_user_mention(user) -> str:
    name = user.full_name or user.first_name or "Noma'lum"
    if user.username:
        return f"@{user.username} [{user.id}]"
    return f'<a href="tg://user?id={user.id}">{name}</a> [{user.id}]'

def contains_emoji(text: str) -> bool:
    if not text:
        return False
    return emoji.emoji_count(text) > 0