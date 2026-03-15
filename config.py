import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "0"))
MAX_WARNINGS = int(os.getenv("MAX_WARNINGS", "3"))
MUTE_DURATION_MINUTES = int(os.getenv("MUTE_DURATION_MINUTES", "5"))
MUTE_DURATION_HOURS = int(os.getenv("MUTE_DURATION_HOURS", "168"))

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
ADMINS_FILE = os.path.join(DATA_DIR, "admins.json")
WARNINGS_FILE = os.path.join(DATA_DIR, "warnings.json")
CUSTOM_BAD_WORDS_FILE = os.path.join(DATA_DIR, "custom_bad_words.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

# Ma'lumotlar bazasi URL (PostgreSQL production uchun tavsiya etiladi)
# SQLite faqat local testlar uchun: sqlite+aiosqlite:///data/bot_database.sqlite
# PostgreSQL: postgresql+asyncpg://user:password@localhost/dbname
DB_URL = os.getenv("DB_URL", f"sqlite+aiosqlite:///{os.path.join(DATA_DIR, 'bot_database.sqlite')}")