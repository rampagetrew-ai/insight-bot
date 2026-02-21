"""Middleware: авторегистрация + роли + суперадмин с expert подпиской."""

from typing import Any, Awaitable, Callable, Dict
from datetime import datetime, timedelta, timezone

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy import select

from bot.config import settings
from bot.database import async_session, User


class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: Dict[str, Any]) -> Any:
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        async with async_session() as session:
            stmt = select(User).where(User.telegram_id == user.id)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()

            if db_user is None:
                role = "user"
                sub = "free"
                sub_exp = None
                if user.username and user.username.lower() == settings.super_admin_username.lower():
                    role = "superadmin"
                    sub = "expert"
                    sub_exp = datetime.now(timezone.utc) + timedelta(days=36500)

                db_user = User(
                    telegram_id=user.id, username=user.username,
                    first_name=user.first_name, role=role,
                    subscription_type=sub, subscription_expires=sub_exp,
                )
                session.add(db_user)
                await session.commit()
                await session.refresh(db_user)
            else:
                changed = False
                if user.username != db_user.username:
                    db_user.username = user.username
                    changed = True
                is_super = user.username and user.username.lower() == settings.super_admin_username.lower()
                if is_super:
                    if db_user.role != "superadmin":
                        db_user.role = "superadmin"
                        changed = True
                    if db_user.subscription_type != "expert":
                        db_user.subscription_type = "expert"
                        db_user.subscription_expires = datetime.now(timezone.utc) + timedelta(days=36500)
                        changed = True
                if changed:
                    await session.commit()
                    await session.refresh(db_user)

            data["db_user"] = db_user
            data["session"] = session
            return await handler(event, data)
