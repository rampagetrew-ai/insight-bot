"""Хендлер админа — управление пользователями."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.database import User

router = Router(name="admin")

ADMIN_ID = 123456789  # Заменить на реальный ID


@router.message(Command("admin"))
async def cmd_admin(message: Message, db_user: User) -> None:
    """Админ-панель."""
    if db_user.telegram_id != ADMIN_ID:
        return
    
    await message.answer(
        "🔧 <b>Админ-панель</b>\n\n"
        "Команды:\n"
        "/stats — статистика\n"
        "/give_sub — выдать подписку"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message, db_user: User) -> None:
    """Статистика бота."""
    if db_user.telegram_id != ADMIN_ID:
        return
    
    await message.answer("📊 Статистика будет здесь")
