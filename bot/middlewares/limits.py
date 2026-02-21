"""Middleware: лимиты запросов по подписке."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from redis.asyncio import Redis

from bot.database import User, async_session


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.limits = {"free": 1, "basic": 10, "premium": 50, "expert": 999}

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: Dict[str, Any]) -> Any:
        data["redis"] = self.redis
        return await handler(event, data)

    async def check_limit(self, db_user: User, action: str = "general") -> tuple[bool, int]:
        if db_user.role in ("admin", "superadmin"):
            return True, 999

        limit = self.limits.get(db_user.subscription_type, 1)
        key = f"limit:{db_user.telegram_id}:{action}"

        current = await self.redis.get(key)
        if current is None:
            await self.redis.setex(key, 86400, 1)
            return True, limit - 1

        current = int(current)
        if current < limit:
            await self.redis.incr(key)
            return True, limit - current - 1

        # Check bonus requests
        if db_user.bonus_requests > 0:
            async with async_session() as session:
                from sqlalchemy import select
                stmt = select(User).where(User.id == db_user.id)
                result = await session.execute(stmt)
                u = result.scalar_one_or_none()
                if u and u.bonus_requests > 0:
                    u.bonus_requests -= 1
                    await session.commit()
                    return True, u.bonus_requests

        return False, 0
