"""Хендлер подписок — управление тарифами."""

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database import User

router = Router(name="subscription")


@router.callback_query(F.data == "menu:subscription")
async def subscription_menu(callback: CallbackQuery, db_user: User) -> None:
    """Меню подписок."""
    await callback.answer()
    
    current = db_user.subscription_type or "free"
    
    text = (
        f"💎 <b>Подписки Insight</b>\n\n"
        f"Твой уровень: <b>{current.upper()}</b>\n\n"
        f"🆓 <b>Free</b> — 1 запрос/день\n"
        f"💎 <b>Premium</b> — 50 запросов, AI, астрология — 599₽/мес\n"
        f"🏆 <b>Expert</b> — безлимит, всё включено — 1499₽/мес\n\n"
        f"Выбери тариф:"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="💎 Premium", callback_data="sub:premium")
    builder.button(text="🏆 Expert", callback_data="sub:expert")
    builder.button(text="🔙 Назад", callback_data="menu:back")
    builder.adjust(2)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("sub:"))
async def process_subscription(callback: CallbackQuery, db_user: User) -> None:
    """Обработка выбора подписки."""
    await callback.answer()
    
    sub_type = callback.data.split(":")[1]
    
    prices = {
        "premium": "599₽/мес",
        "expert": "1499₽/мес",
    }
    
    text = (
        f"💳 <b>Оформление подписки</b>\n\n"
        f"Тариф: <b>{sub_type.upper()}</b>\n"
        f"Стоимость: {prices.get(sub_type, '—')}\n\n"
        f"⚠️ Оплата пока не подключена.\n"
        f"Напиши @ALTLPU для активации подписки вручную."
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="menu:subscription")
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
