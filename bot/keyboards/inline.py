"""Inline клавиатуры бота."""

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb(role: str = "user"):
    """Главное меню."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🃏 Таро", callback_data="menu:tarot"),
        InlineKeyboardButton(text="🔢 Нумерология", callback_data="menu:numerology"),
    )
    builder.row(
        InlineKeyboardButton(text="🌟 Астрология", callback_data="menu:astrology"),
        InlineKeyboardButton(text="📓 Журнал", callback_data="menu:journal"),
    )
    builder.row(
        InlineKeyboardButton(text="👤 Профиль", callback_data="menu:profile"),
        InlineKeyboardButton(text="💎 Подписка", callback_data="menu:subscription"),
    )
    if role in ("admin", "superadmin"):
        builder.row(
            InlineKeyboardButton(text="🔧 Админ-панель", callback_data="admin:panel"),
        )
    return builder.as_markup()


def back_to_menu_kb():
    """Кнопка назад в меню."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 В главное меню", callback_data="menu:back"))
    return builder.as_markup()


def tarot_menu_kb():
    """Меню таро."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🌅 Карта дня", callback_data="tarot:daily"))
    builder.row(InlineKeyboardButton(text="🎴 Три карты", callback_data="tarot:three_cards"))
    builder.row(InlineKeyboardButton(text="⚖️ Расклад на решение", callback_data="tarot:decision"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="menu:back"))
    return builder.as_markup()


def tarot_interpret_kb(reading_id: int):
    """Кнопка AI-трактовки после расклада."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🤖 AI-трактовка", callback_data=f"tarot:interpret:{reading_id}"))
    builder.row(InlineKeyboardButton(text="🃏 Ещё расклад", callback_data="menu:tarot"))
    builder.row(InlineKeyboardButton(text="🔙 В меню", callback_data="menu:back"))
    return builder.as_markup()


def numerology_menu_kb():
    """Меню нумерологии."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔥 Число жизненного пути", callback_data="num:life_path"))
    builder.row(InlineKeyboardButton(text="💫 Число души", callback_data="num:soul"))
    builder.row(InlineKeyboardButton(text="🎭 Число личности", callback_data="num:personality"))
    builder.row(InlineKeyboardButton(text="🌟 Число судьбы", callback_data="num:destiny"))
    builder.row(InlineKeyboardButton(text="📅 Персональный год", callback_data="num:personal_year"))
    builder.row(InlineKeyboardButton(text="📊 Полный отчёт", callback_data="num:full_report"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="menu:back"))
    return builder.as_markup()
