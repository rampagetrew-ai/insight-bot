"""Хендлер профиля — настройка данных пользователя."""

from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.database import Profile, User, async_session

router = Router(name="profile")


class ProfileStates(StatesGroup):
    waiting_birth_date = State()
    waiting_birth_time = State()
    waiting_birth_place = State()
    waiting_name = State()


@router.callback_query(F.data == "menu:profile")
async def profile_menu(callback: CallbackQuery, db_user: User) -> None:
    """Меню профиля."""
    await callback.answer()
    
    # Получаем профиль
    async with async_session() as session:
        result = await session.execute(
            select(Profile).where(Profile.user_id == db_user.id)
        )
        profile = result.scalar_one_or_none()
    
    if profile and profile.birth_date:
        text = (
            f"👤 <b>Твой профиль</b>\n\n"
            f"📅 Дата рождения: {profile.birth_date.strftime('%d.%m.%Y')}\n"
            f"🕐 Время: {profile.birth_time or 'не указано'}\n"
            f"📍 Место: {profile.birth_place or 'не указано'}\n"
            f"🏷 Имя: {profile.current_name or profile.birth_name or 'не указано'}\n\n"
            f"Данные используются для астрологических расчётов."
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(text="✏️ Изменить", callback_data="profile:edit")
        builder.button(text="🔙 Назад", callback_data="menu:back")
        
    else:
        text = (
            f"👤 <b>Создать профиль</b>\n\n"
            f"Для точных расчётов нужны данные рождения.\n\n"
            f"📅 Дата — обязательно\n"
            f"🕐 Время — для астрологии\n"
            f"📍 Место — для астрологии"
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(text="📝 Заполнить", callback_data="profile:create")
        builder.button(text="🔙 Назад", callback_data="menu:back")
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "profile:create")
async def create_profile_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало создания профиля."""
    await callback.answer()
    await callback.message.edit_text(
        "📅 Введи дату рождения:\n"
        "Формат: <code>15.03.1990</code>",
        parse_mode="HTML",
    )
    await state.set_state(ProfileStates.waiting_birth_date)


@router.message(ProfileStates.waiting_birth_date)
async def process_birth_date(message: Message, state: FSMContext, db_user: User) -> None:
    """Обработка даты рождения."""
    try:
        date = datetime.strptime(message.text.strip(), "%d.%m.%Y")
        await state.update_data(birth_date=date)
        
        await message.answer(
            "🕐 Введи время рождения (или отправь '-'):\n"
            "Формат: <code>14:30</code>",
            parse_mode="HTML",
        )
        await state.set_state(ProfileStates.waiting_birth_time)
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Попробуй: <code>15.03.1990</code>",
            parse_mode="HTML",
        )


@router.message(ProfileStates.waiting_birth_time)
async def process_birth_time(message: Message, state: FSMContext) -> None:
    """Обработка времени рождения."""
    time_str = message.text.strip()
    if time_str == "-":
        time_str = None
    
    await state.update_data(birth_time=time_str)
    
    await message.answer(
        "📍 Введи место рождения (город):\n"
        "Или отправь '-' если не знаешь",
    )
    await state.set_state(ProfileStates.waiting_birth_place)


@router.message(ProfileStates.waiting_birth_place)
async def process_birth_place(message: Message, state: FSMContext, db_user: User) -> None:
    """Обработка места рождения и сохранение профиля."""
    place = message.text.strip()
    if place == "-":
        place = None
    
    data = await state.get_data()
    
    # Создаём или обновляем профиль
    async with async_session() as session:
        result = await session.execute(
            select(Profile).where(Profile.user_id == db_user.id)
        )
        profile = result.scalar_one_or_none()
        
        if profile:
            profile.birth_date = data["birth_date"]
            profile.birth_time = data.get("birth_time")
            profile.birth_place = place
        else:
            profile = Profile(
                user_id=db_user.id,
                birth_date=data["birth_date"],
                birth_time=data.get("birth_time"),
                birth_place=place,
            )
            session.add(profile)
        
        await session.commit()
    
    await state.clear()
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 В меню", callback_data="menu:back")
    
    await message.answer(
        "✅ <b>Профиль сохранён!</b>\n\n"
        "Теперь можно использовать все функции бота.",
        reply_markup=builder.as_markup(),
    )
