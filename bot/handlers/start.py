"""Стартовый хендлер — приветствие и главное меню."""

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot.database import User
from bot.keyboards.inline import main_menu_kb

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: User) -> None:
    """Обработка команды /start."""
    name = db_user.username or "Друг"
    
    text = (
        f"🌟 <b>Привет, {name}!</b>\n\n"
        f"Я Insight — твой помощник для принятия решений.\n"
        f"Использую нумерологию, таро и астрологию как инструменты самопознания.\n\n"
        f"🔮 <b>Что умею:</b>\n"
        f"• Нумерология — твои числа и их значение\n"
        f"• Таро — расклады для конкретных вопросов\n"
        f"• Астрология — натальная карта (Premium)\n\n"
        f"Начни с заполнения профиля — это займёт минуту."
    )
    
    await message.answer(text, reply_markup=main_menu_kb())


@router.callback_query(F.data == "menu:back")
async def back_to_menu(callback: CallbackQuery) -> None:
    """Возврат в главное меню."""
    await callback.answer()
    
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыбери раздел:",
        reply_markup=main_menu_kb(),
    )
