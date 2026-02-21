"""Обновлённый хендлер нумерологии с персонализацией."""

from datetime import date

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select

from bot.database import NumerologyCache, Profile, User, async_session
from bot.keyboards.inline import back_to_menu_kb, numerology_menu_kb
from bot.middlewares.limits import RateLimitMiddleware
from bot.services.ai import ai_interpreter
from bot.services.numerology import numerology
from bot.utils.personalization import (
    LIFE_PATH_HOOKS,
    NUMEROLOGY_LIFE_PATH_TEMPLATE,
    get_personalized_numerology_intro,
)
from bot.utils.texts_new import NUMEROLOGY_MENU, NUMEROLOGY_NO_PROFILE

router = Router(name="numerology")


async def _get_profile(user_id: int) -> Profile | None:
    async with async_session() as session:
        result = await session.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()


async def _get_or_calculate(db_user: User, profile: Profile) -> dict[str, int]:
    """Получает или пересчитывает числа."""
    async with async_session() as session:
        result = await session.execute(
            select(NumerologyCache).where(NumerologyCache.user_id == db_user.id)
        )
        cache = result.scalar_one_or_none()

        current_year = date.today().year
        name = profile.current_name or profile.birth_name or ""

        # Проверяем кэш
        if cache and cache.life_path and cache.personal_year_for == current_year:
            return {
                "life_path": cache.life_path,
                "soul": cache.soul_number,
                "personality": cache.personality_number,
                "destiny": cache.destiny_number,
                "personal_year": cache.personal_year,
            }

        # Пересчитываем
        numbers = numerology.full_report(name, profile.birth_date)

        if cache is None:
            cache = NumerologyCache(user_id=db_user.id)
            session.add(cache)

        cache.life_path = numbers["life_path"]
        cache.soul_number = numbers["soul"]
        cache.personality_number = numbers["personality"]
        cache.destiny_number = numbers["destiny"]
        cache.personal_year = numbers["personal_year"]
        cache.personal_year_for = current_year

        await session.commit()
        return numbers


# ═══════════════════════════════════════════════════════════
# МЕНЮ
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "menu:numerology")
async def numerology_menu(callback: CallbackQuery, db_user: User) -> None:
    await callback.answer()
    profile = await _get_profile(db_user.id)
    
    if not profile or not profile.birth_date:
        await callback.message.edit_text(
            NUMEROLOGY_NO_PROFILE,
            reply_markup=back_to_menu_kb(),
            parse_mode="HTML",
        )
        return

    await callback.message.edit_text(
        NUMEROLOGY_MENU,
        reply_markup=numerology_menu_kb(),
        parse_mode="HTML",
    )


# ═══════════════════════════════════════════════════════════
# РАСЧЁТ ЧИСЕЛ С ПЕРСОНАЛИЗАЦИЕЙ
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("num:"))
async def numerology_calculate(
    callback: CallbackQuery, db_user: User, redis: object
) -> None:
    await callback.answer()
    action = callback.data.split(":")[1]

    profile = await _get_profile(db_user.id)
    if not profile or not profile.birth_date:
        await callback.message.edit_text(
            NUMEROLOGY_NO_PROFILE,
            reply_markup=back_to_menu_kb(),
            parse_mode="HTML",
        )
        return

    # Проверяем лимит
    rate_limiter = RateLimitMiddleware.__new__(RateLimitMiddleware)
    rate_limiter.redis = redis
    rate_limiter.limits = {
        "free": 1, "basic": 10, "premium": 50, "expert": 999,
    }
    allowed, remaining = await rate_limiter.check_limit(db_user, "numerology")
    if not allowed:
        from bot.utils.texts_new import LIMIT_REACHED
        await callback.message.edit_text(
            LIMIT_REACHED, reply_markup=back_to_menu_kb(), parse_mode="HTML"
        )
        return

    numbers = await _get_or_calculate(db_user, profile)
    name = profile.current_name or profile.birth_name or ""
    
    # Получаем персонализацию
    hooks = LIFE_PATH_HOOKS.get(numbers["life_path"], {})
    
    if action == "full_report":
        await _send_full_report(
            callback, db_user, profile, numbers, name, remaining, hooks
        )
    else:
        await _send_single_number(
            callback, action, numbers, name, remaining, hooks
        )


async def _send_single_number(
    callback: CallbackQuery,
    action: str,
    numbers: dict,
    name: str,
    remaining: int,
    hooks: dict,
) -> None:
    """Отправляет расчёт одного числа с персонализацией."""
    
    number_labels = {
        "life_path": ("🔥 Число жизненного пути", "life_path"),
        "soul": ("💫 Число души", "soul"),
        "personality": ("🎭 Число личности", "personality"),
        "destiny": ("🌟 Число судьбы", "destiny"),
        "personal_year": ("📅 Персональный год", "personal_year"),
    }
    
    if action not in number_labels:
        await callback.message.edit_text("Неизвестное действие")
        return
    
    label, context = number_labels[action]
    num = numbers[action]
    
    # Получаем базовое значение
    meaning = numerology.get_number_meaning(num, context)
    
    # Добавляем персонализацию для life_path
    if action == "life_path" and hooks:
        text = NUMEROLOGY_LIFE_PATH_TEMPLATE.format(
            name=name or "Друг",
            number=num,
            hook=hooks.get("hook", ""),
            childhood=hooks.get("childhood", ""),
            trap=hooks.get("trap", ""),
            current_advice=hooks.get("trap", "").replace("ловушка", "выход"),
            action=hooks.get("action", ""),
            remaining=remaining,
        )
    else:
        # Для других чисел — базовый формат
        text = (
            f"{label}\n\n"
            f"Твоё число: <b>{num}</b>\n\n"
            f"{meaning}\n\n"
            f"📊 Осталось запросов: {remaining}"
        )
    
    await callback.message.edit_text(
        text,
        reply_markup=numerology_menu_kb(),
        parse_mode="HTML",
    )


async def _send_full_report(
    callback: CallbackQuery,
    db_user: User,
    profile: Profile,
    numbers: dict,
    name: str,
    remaining: int,
    hooks: dict,
) -> None:
    """Отправляет полный отчёт с AI-интерпретацией для Premium."""
    
    # Базовая часть для всех
    lines = [
        f"🔮 <b>Полный нумерологический профиль</b>",
        f"",
        f"{get_personalized_numerology_intro(name or 'Друг', profile.birth_date.isoformat())}",
        f"",
    ]
    
    # Добавляем числа с краткими значениями
    number_emojis = {
        "life_path": "🔥",
        "soul": "💫", 
        "personality": "🎭",
        "destiny": "🌟",
        "personal_year": "📅",
    }
    
    for key, emoji in number_emojis.items():
        num = numbers[key]
        # Краткое значение (первое предложение)
        full_meaning = numerology.get_number_meaning(num, key)
        short_meaning = full_meaning.split('.')[0] + '.'
        lines.append(f"{emoji} <b>{key.replace('_', ' ').title()}:</b> {num}")
        lines.append(f"   <i>{short_meaning}</i>")
        lines.append("")
    
    # Добавляем персональный хук
    if hooks:
        lines.extend([
            f"⚠️ <b>Твоя ловушка:</b>",
            f"{hooks.get('trap', '')}",
            f"",
            f"🎯 <b>Действие сегодня:</b>",
            f"{hooks.get('action', '')}",
        ])
    
    lines.append(f"")
    lines.append(f"📊 Осталось запросов: {remaining}")
    
    # Для Premium — добавляем кнопку AI-интерпретации
    if db_user.subscription_type in ("premium", "expert"):
        lines.append(f"")
        lines.append(f"💡 <i>Хочешь глубокий разбор от AI?</i>")
        
        from aiogram.types import InlineKeyboardButton
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="🤖 AI-разбор всего профиля",
            callback_data=f"num:ai_interpret:{db_user.id}"
        ))
        builder.row(InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="menu:numerology"
        ))
        
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=builder.as_markup(),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=numerology_menu_kb(),
            parse_mode="HTML",
        )


# ═══════════════════════════════════════════════════════════
# AI ИНТЕРПРЕТАЦИЯ
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("num:ai_interpret:"))
async def numerology_ai_interpret(callback: CallbackQuery, db_user: User) -> None:
    """Генерирует AI-интерпретацию нумерологического профиля."""
    await callback.answer("🤖 Анализирую профиль...")
    
    if db_user.subscription_type not in ("premium", "expert"):
        from bot.utils.texts_new import SUBSCRIPTION_REQUIRED
        await callback.message.edit_text(
            SUBSCRIPTION_REQUIRED.format(
                feature="AI-интерпретация нумерологии",
                required="Premium",
                current=db_user.subscription_type.upper(),
            ),
            reply_markup=back_to_menu_kb(),
            parse_mode="HTML",
        )
        return
    
    profile = await _get_profile(db_user.id)
    if not profile:
        await callback.message.edit_text("Профиль не найден")
        return
    
    numbers = await _get_or_calculate(db_user, profile)
    name = profile.current_name or profile.birth_name or ""
    
    # Формируем контекст
    context = f"Имя: {name}. Дата рождения: {profile.birth_date}"
    if profile.birth_time:
        context += f", время: {profile.birth_time}"
    
    interpretation = await ai_interpreter.interpret_numerology(numbers, context)
    
    text = (
        f"🤖 <b>AI-разбор нумерологического профиля</b>\n\n"
        f"{interpretation}\n\n"
        f"<i>Это не предсказание — это зеркало. "
        f"Увидел(а) что-то важное? Запиши.</i>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=back_to_menu_kb(),
        parse_mode="HTML",
    )
