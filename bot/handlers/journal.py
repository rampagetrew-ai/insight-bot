"""Хендлер журнала решений."""

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database import User

router = Router(name="journal")


@router.callback_query(F.data == "menu:journal")
async def journal_menu(callback: CallbackQuery, db_user: User) -> None:
    """Меню журнала."""
    await callback.answer()
    
    await callback.message.edit_text(
        "📓 <b>Журнал решений</b>\n\n"
        "Здесь будут сохраняться твои расклады и выборы.\n"
        "Функция в разработке.",
        reply_markup=InlineKeyboardBuilder().button(
            text="🔙 Назад", callback_data="menu:back"
        ).as_markup(),
    )
