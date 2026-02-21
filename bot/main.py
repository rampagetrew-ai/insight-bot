"""Точка входа Insight Bot с астрологией."""

import asyncio
import logging
import sys

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from bot.config import settings
from bot.database import close_db, init_db
from bot.handlers import (
    admin,
    astrology,
    journal,
    numerology,
    profile,
    start,
    subscription,
    tarot,
)
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.limits import RateLimitMiddleware


def setup_logging() -> None:
    """Настройка structlog + стандартного logging."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(message)s",
        stream=sys.stdout,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
    )


async def main() -> None:
    setup_logging()
    logger = structlog.get_logger()

    logger.info("Starting Insight Bot...")

    # Redis
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    storage = RedisStorage(redis=Redis.from_url(settings.redis_url))

    # Bot & Dispatcher
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    # Middlewares
    dp.update.middleware(AuthMiddleware())

    rate_limiter = RateLimitMiddleware(redis=redis)
    dp.update.middleware(rate_limiter)

    # Routers
    dp.include_routers(
        admin.router,
        start.router,
        profile.router,
        numerology.router,
        tarot.router,
        astrology.router,
        journal.router,
        subscription.router,
    )

    # Database
    await init_db()
    logger.info("Database initialized")

    # Start polling
    try:
        logger.info("Bot is running (polling mode)")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        logger.info("Shutting down...")
        await redis.close()
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
