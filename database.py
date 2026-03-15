import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, text, select, delete, update, BigInteger
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import DB_URL, SUPER_ADMIN_ID

engine = create_async_engine(DB_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

class Admin(Base):
    __tablename__ = "admins"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    can_warn: Mapped[bool] = mapped_column(Integer, default=1)
    can_mute: Mapped[bool] = mapped_column(Integer, default=1)
    can_ban: Mapped[bool] = mapped_column(Integer, default=0)
    can_delete: Mapped[bool] = mapped_column(Integer, default=0)
    can_invite: Mapped[bool] = mapped_column(Integer, default=0)

class WarningRecord(Base):
    __tablename__ = "warnings"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    user_name: Mapped[str] = mapped_column(String(255), default="Noma'lum")
    total_warnings: Mapped[int] = mapped_column(Integer, default=0)
    total_mutes: Mapped[int] = mapped_column(Integer, default=0)
    total_bans: Mapped[int] = mapped_column(Integer, default=0)

class NameHistory(Base):
    __tablename__ = "name_history"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    old_name: Mapped[str] = mapped_column(String(255))
    changed_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

class CustomBadWord(Base):
    __tablename__ = "custom_bad_words"
    word: Mapped[str] = mapped_column(String(100), primary_key=True)

class UserRegistry(Base):
    __tablename__ = "user_registry"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    last_seen: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

class MessageLog(Base):
    __tablename__ = "message_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    message_id: Mapped[int] = mapped_column(BigInteger)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def is_admin(user_id: int) -> bool:
    if user_id == SUPER_ADMIN_ID:
        return True
    async with async_session() as session:
        result = await session.execute(select(Admin).where(Admin.user_id == user_id))
        return result.scalar_one_or_none() is not None

async def has_permission(user_id: int, perm: str) -> bool:
    if user_id == SUPER_ADMIN_ID:
        return True
    async with async_session() as session:
        result = await session.execute(select(Admin).where(Admin.user_id == user_id))
        admin = result.scalar_one_or_none()
        if not admin:
            return False
        return getattr(admin, f"can_{perm}", False)

async def is_super_admin(user_id: int) -> bool:
    return user_id == SUPER_ADMIN_ID

async def get_admins() -> List[int]:
    async with async_session() as session:
        result = await session.execute(select(Admin.user_id))
        return [row[0] for row in result.all()]

async def add_admin(user_id: int, can_warn=1, can_mute=1, can_ban=0, can_delete=0, can_invite=0) -> bool:
    if await is_admin(user_id) and user_id != SUPER_ADMIN_ID:
        return False
    async with async_session() as session:
        session.add(Admin(
            user_id=user_id, 
            can_warn=can_warn, 
            can_mute=can_mute, 
            can_ban=can_ban,
            can_delete=can_delete,
            can_invite=can_invite
        ))
        await session.commit()
        return True

async def update_admin_permissions(user_id: int, **perms) -> bool:
    async with async_session() as session:
        stmt = update(Admin).where(Admin.user_id == user_id).values(**perms)
        result = await session.execute(stmt)
        await session.commit()
        return (result.rowcount or 0) > 0

async def get_admin_permissions(user_id: int) -> Optional[dict]:
    if user_id == SUPER_ADMIN_ID:
        return {
            "warn": True, "mute": True, "ban": True, 
            "delete": True, "invite": True
        }
    async with async_session() as session:
        res = await session.execute(select(Admin).where(Admin.user_id == user_id))
        admin = res.scalar_one_or_none()
        if admin:
            return {
                "warn": bool(admin.can_warn),
                "mute": bool(admin.can_mute),
                "ban": bool(admin.can_ban),
                "delete": bool(admin.can_delete),
                "invite": bool(admin.can_invite)
            }
        return None

async def remove_admin(user_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(delete(Admin).where(Admin.user_id == user_id))
        await session.commit()
        return (result.rowcount or 0) > 0

async def register_user(user_id: int, username: Optional[str], full_name: str):
    async with async_session() as session:
        stmt = select(UserRegistry).where(UserRegistry.user_id == user_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        
        clean_username = username.replace("@", "").strip().lower() if username else None
        
        if user:
            user.username = clean_username
            user.full_name = full_name
        else:
            session.add(UserRegistry(
                user_id=user_id, 
                username=clean_username, 
                full_name=full_name
            ))
        await session.commit()

async def get_id_by_username(username: str) -> Optional[int]:
    clean_username = username.replace("@", "").strip().lower()
    async with async_session() as session:
        stmt = select(UserRegistry.user_id).where(UserRegistry.username == clean_username)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

async def add_warning(chat_id: int, user_id: int, user_name: str) -> int:
    async with async_session() as session:
        stmt = select(WarningRecord).where(
            WarningRecord.chat_id == chat_id, 
            WarningRecord.user_id == user_id
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        
        if record:
            record.count += 1
            record.total_warnings += 1
            record.user_name = user_name
        else:
            record = WarningRecord(
                chat_id=chat_id, 
                user_id=user_id, 
                count=1, 
                total_warnings=1,
                user_name=user_name
            )
            session.add(record)
            
        await session.commit()
        return record.count

async def get_warnings(chat_id: int, user_id: int) -> int:
    async with async_session() as session:
        stmt = select(WarningRecord.count).where(
            WarningRecord.chat_id == chat_id, 
            WarningRecord.user_id == user_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() or 0

async def reset_warnings(chat_id: int, user_id: int):
    async with async_session() as session:
        await session.execute(
            update(WarningRecord)
            .where(WarningRecord.chat_id == chat_id, WarningRecord.user_id == user_id)
            .values(count=0)
        )
        await session.commit()

async def log_mute(chat_id: int, user_id: int):
    async with async_session() as session:
        stmt = select(WarningRecord).where(
            WarningRecord.chat_id == chat_id, 
            WarningRecord.user_id == user_id
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        if record:
            record.total_mutes += 1
        else:
            session.add(WarningRecord(chat_id=chat_id, user_id=user_id, total_mutes=1))
        await session.commit()

async def log_ban(chat_id: int, user_id: int):
    async with async_session() as session:
        stmt = select(WarningRecord).where(
            WarningRecord.chat_id == chat_id, 
            WarningRecord.user_id == user_id
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        if record:
            record.total_bans += 1
        else:
            session.add(WarningRecord(chat_id=chat_id, user_id=user_id, total_bans=1))
        await session.commit()

async def get_user_stats(chat_id: int, user_id: int) -> dict:
    async with async_session() as session:
        stmt = select(WarningRecord).where(
            WarningRecord.chat_id == chat_id, 
            WarningRecord.user_id == user_id
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        if record:
            return {
                "warnings": record.total_warnings,
                "mutes": record.total_mutes,
                "bans": record.total_bans
            }
        return {"warnings": 0, "mutes": 0, "bans": 0}

async def get_all_warnings(chat_id: int) -> dict:
    async with async_session() as session:
        stmt = select(WarningRecord).where(WarningRecord.chat_id == chat_id)
        result = await session.execute(stmt)
        records = result.scalars().all()
        return {str(r.user_id): {"count": r.count, "name": r.user_name} for r in records}

async def reset_all_chat_stats(chat_id: int):
    async with async_session() as session:
        await session.execute(delete(WarningRecord).where(WarningRecord.chat_id == chat_id))
        await session.commit()

async def add_custom_bad_word(word: str) -> bool:
    word = word.lower().strip()
    async with async_session() as session:
        stmt = select(CustomBadWord).where(CustomBadWord.word == word)
        res = await session.execute(stmt)
        if res.scalar_one_or_none():
            return False
        session.add(CustomBadWord(word=word))
        await session.commit()
        return True

async def remove_custom_bad_word(word: str) -> bool:
    word = word.lower().strip()
    async with async_session() as session:
        res = await session.execute(delete(CustomBadWord).where(CustomBadWord.word == word))
        await session.commit()
        return (res.rowcount or 0) > 0

async def get_custom_bad_words() -> List[str]:
    async with async_session() as session:
        res = await session.execute(select(CustomBadWord.word))
        return [row[0] for row in res.all()]

async def update_user_name_and_history(chat_id: int, user_id: int, user_name: str) -> None:
    async with async_session() as session:
        stmt = select(WarningRecord).where(
            WarningRecord.chat_id == chat_id, 
            WarningRecord.user_id == user_id
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        
        if record:
            if record.user_name != user_name:
                session.add(NameHistory(user_id=user_id, old_name=record.user_name))
                record.user_name = user_name
                await session.commit()

async def get_user_history(user_id: int) -> dict:
    async with async_session() as session:
        stmt = select(NameHistory).where(NameHistory.user_id == user_id).order_by(NameHistory.changed_at.desc())
        result = await session.execute(stmt)
        records = result.scalars().all()
        
        stmt_curr = select(WarningRecord.user_name).where(WarningRecord.user_id == user_id).limit(1)
        res_curr = await session.execute(stmt_curr)
        curr_name = res_curr.scalar_one_or_none() or "Noma'lum"
        
        return {
            "current_name": curr_name,
            "names": [{"name": r.old_name, "date": r.changed_at.strftime("%d.%m.%Y")} for r in records]
        }

def get_registration_year(user_id: int) -> str:
    ranges = [
        (100_000_000, "2013-2014"),
        (250_000_000, "2015-2016"),
        (450_000_000, "2017"),
        (700_000_000, "2018"),
        (950_000_000, "2019"),
        (1_200_000_000, "2020"),
        (1_600_000_000, "2021"),
        (3_000_000_000, "2022"),
        (5_500_000_000, "2023"),
        (7_500_000_000, "2024"),
    ]
    for limit, year in ranges:
        if user_id < limit:
            return year
    return "2024-2025"

async def log_message(chat_id: int, user_id: int, message_id: int):
    async with async_session() as session:
        session.add(MessageLog(chat_id=chat_id, user_id=user_id, message_id=message_id))
        await session.commit()

async def get_user_messages(chat_id: int, user_id: int, limit: int) -> List[int]:
    async with async_session() as session:
        stmt = select(MessageLog.message_id).where(
            MessageLog.chat_id == chat_id,
            MessageLog.user_id == user_id
        ).order_by(MessageLog.message_id.desc()).limit(limit)
        res = await session.execute(stmt)
        return [row[0] for row in res.scalars().all()]

async def delete_logged_messages(chat_id: int, message_ids: List[int]):
    async with async_session() as session:
        await session.execute(delete(MessageLog).where(
            MessageLog.chat_id == chat_id,
            MessageLog.message_id.in_(message_ids)
        ))
        await session.commit()