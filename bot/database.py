"""Модели БД и подключение."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, Date, Time, JSON, Float, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from bot.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="user")
    subscription_type: Mapped[str] = mapped_column(String(20), default="free")
    subscription_expires: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    bonus_requests: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    birth_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    current_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    birth_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    birth_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    birth_place: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    birth_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    birth_lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NumerologyCache(Base):
    __tablename__ = "numerology_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    life_path: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    soul_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    personality_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    destiny_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    personal_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    personal_year_for: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class TarotReading(Base):
    __tablename__ = "tarot_readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    spread_type: Mapped[str] = mapped_column(String(32))
    cards_json: Mapped[dict] = mapped_column(JSON)
    question: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_interpretation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    situation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decision: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    await engine.dispose()
