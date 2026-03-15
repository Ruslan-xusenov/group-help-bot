import asyncio
import os
from sqlalchemy import select, create_mock_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import models from our database file
import sys
sys.path.append(os.getcwd())
from database import Base, Admin, WarningRecord, NameHistory, CustomBadWord, UserRegistry, MessageLog
from config import DATA_DIR

# Hardcoded source and destination for safety in this script
SQLITE_URL = f"sqlite+aiosqlite:///{os.path.join(DATA_DIR, 'bot_database.sqlite')}"
PG_URL = os.getenv("DB_URL") # This should be set in .env or system

async def migrate():
    if not PG_URL or "postgresql" not in PG_URL:
        print("❌ PostgreSQL URL (.env ichidagi DB_URL) topilmadi yoki noto'g'ri!")
        return

    print(f"🔄 Migratsiya boshlandi...")
    print(f"📁 Manba: SQLite ({SQLITE_URL})")
    print(f"🐘 Manzil: PostgreSQL")

    # Engines
    sqlite_engine = create_async_engine(SQLITE_URL)
    pg_engine = create_async_engine(PG_URL)

    # Sessions
    SQLiteSession = sessionmaker(sqlite_engine, expire_on_commit=False, class_=AsyncSession)
    PGSession = sessionmaker(pg_engine, expire_on_commit=False, class_=AsyncSession)

    # 1. Create tables in PG
    async with pg_engine.begin() as conn:
        print("🛠️ PostgreSQL jadvallari yaratilmoqda...")
        await conn.run_sync(Base.metadata.create_all)

    # 2. Copy data table by table
    tables = [Admin, WarningRecord, NameHistory, CustomBadWord, UserRegistry, MessageLog]
    
    async with SQLiteSession() as s_session, PGSession() as p_session:
        for model in tables:
            print(f"📦 {model.__tablename__} ko'chirilmoqda...")
            
            # Check if table exists in SQLite
            try:
                result = await s_session.execute(select(model))
                items = result.scalars().all()
            except Exception as e:
                if "no such table" in str(e).lower():
                    print(f"⚠️ Jadval SQLite'da topilmadi, o'tkazib yuboriladi.")
                    continue
                raise e
            
            if items:
                # Merge into postgres
                for item in items:
                    # Clear state to avoid conflict between sessions
                    s_session.expunge(item)
                    await p_session.merge(item)
                
                await p_session.commit()
                print(f"✅ {len(items)} ta qator ko'chirildi.")
            else:
                print(f"ℹ️ Jadval bo'sh.")

    print("\n🎉 Migratsiya muvaffaqiyatli yakunlandi!")
    
    await sqlite_engine.dispose()
    await pg_engine.dispose()

if __name__ == "__main__":
    # Load .env manually if needed
    from dotenv import load_dotenv
    load_dotenv()
    PG_URL = os.getenv("DB_URL")
    
    asyncio.run(migrate())
