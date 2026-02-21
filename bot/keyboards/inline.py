"""Inline клавиатуры бота."""

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb() -> InlineKeyboardBuilder:
    """Главное меню."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🃏 Таро", callback_data="tarot:menu"),
        InlineKeyboardButton(text="🔢 Нумерология", callback_data="numerology:menu"),
    )
    builder.row(
        InlineKeyboardButton(text="🌟 Астрология", callback_data="menu:astrology"),
        InlineKeyboardButton(text="📓 Журнал", callback_data="menu:journal"),
    )
    builder.row(
        InlineKeyboardButton(text="👤 Профиль", callback_data="menu:profile"),
        InlineKeyboardButton(text="💎 Подписка", callback_data="menu:subscription"),
    )
    
    return builder.as_markup()


def back_to_menu_kb() -> InlineKeyboardBuilder:
    """Кнопка назад в меню."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="menu:back")
    )
    return builder.as_markup()


def tarot_menu_kb() -> InlineKeyboardBuilder:
    """Меню таро."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🎴 Расклад на 3 карты", callback_data="tarot:spread:3"),
    )
    builder.row(
        InlineKeyboardButton(text="☀️ Карта дня", callback_data="tarot:daily"),
    )
    builder.row(
        InlineKeyboardButton(text="❓ Ответ на вопрос", callback_data="tarot:question"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="menu:back"),
    )
    
    return builder.as_markup()


def numerology_menu_kb() -> InlineKeyboardBuilder:
    """Меню нумерологии."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🔢 Число жизненного пути", callback_data="num:life_path"),
    )
    builder.row(
        InlineKeyboardButton(text="💫 Личный год", callback_data="num:personal_year"),
    )
    builder.row(
        InlineKeyboardButton(text="⚡ Совместимость", callback_data="num:compatibility"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="menu:back"),
    )
    
    return builder.as_markup()
