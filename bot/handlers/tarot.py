"""Обновлённый хендлер таро с повествовательными раскладами."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from bot.database import Profile, TarotReading, User, async_session
from bot.keyboards.inline import back_to_menu_kb, tarot_interpret_kb, tarot_menu_kb
from bot.middlewares.limits import RateLimitMiddleware
from bot.services.ai import ai_interpreter
from bot.services.tarot import SPREADS, tarot
from bot.utils.personalization import (
    CARD_STORIES,
    TAROT_DAILY_TEMPLATE,
    TAROT_DECISION_TEMPLATE,
    TAROT_THREE_CARDS_TEMPLATE,
    get_card_story,
    get_time_greeting,
)
from bot.utils.texts_new import TAROT_ASK_QUESTION, TAROT_MENU

router = Router(name="tarot")


class TarotStates(StatesGroup):
    waiting_question = State()


# ═══════════════════════════════════════════════════════════
# МЕНЮ
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "menu:tarot")
async def tarot_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(
        TAROT_MENU, reply_markup=tarot_menu_kb(), parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════
# ВЫБОР РАСКЛАДА
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("tarot:") & ~F.data.startswith("tarot:interpret"))
async def tarot_start_spread(
    callback: CallbackQuery, state: FSMContext, db_user: User, redis: object
) -> None:
    await callback.answer()
    spread_type = callback.data.split(":")[1]

    if spread_type not in SPREADS:
        return

    spread = SPREADS[spread_type]

    # Проверяем premium
    if spread.get("premium") and db_user.subscription_type not in ("premium", "expert"):
        from bot.utils.texts_new import SUBSCRIPTION_REQUIRED
        await callback.message.edit_text(
            SUBSCRIPTION_REQUIRED.format(
                feature=f"Расклад «{spread['name_ru']}»",
                required="Premium",
                current=db_user.subscription_type.upper(),
            ),
            reply_markup=back_to_menu_kb(),
            parse_mode="HTML",
        )
        return

    # Проверяем лимит
    rate_limiter = RateLimitMiddleware.__new__(RateLimitMiddleware)
    rate_limiter.redis = redis
    rate_limiter.limits = {"free": 1, "basic": 10, "premium": 50, "expert": 999}
    allowed, remaining = await rate_limiter.check_limit(db_user, "tarot")
    if not allowed:
        from bot.utils.texts_new import LIMIT_REACHED
        await callback.message.edit_text(
            LIMIT_REACHED, reply_markup=back_to_menu_kb(), parse_mode="HTML"
        )
        return

    # Для карты дня — сразу делаем расклад
    if spread_type == "daily":
        await _do_spread(callback.message, db_user, spread_type, question=None, edit=True)
        return

    # Для остальных — спрашиваем вопрос
    await state.update_data(spread_type=spread_type)
    await callback.message.edit_text(TAROT_ASK_QUESTION, parse_mode="HTML")
    await state.set_state(TarotStates.waiting_question)


@router.message(TarotStates.waiting_question)
async def tarot_process_question(
    message: Message, state: FSMContext, db_user: User
) -> None:
    data = await state.get_data()
    await state.clear()
    spread_type = data.get("spread_type", "three_cards")
    question = message.text.strip()

    await _do_spread(message, db_user, spread_type, question)


# ═══════════════════════════════════════════════════════════
# РАСКЛАД С ПОВЕСТВОВАНИЕМ
# ═══════════════════════════════════════════════════════════

async def _do_spread(
    message: Message,
    db_user: User,
    spread_type: str,
    question: str | None,
    edit: bool = False,
) -> None:
    """Выполняет расклад с повествовательным текстом."""
    
    result = tarot.do_spread(spread_type)
    
    # Получаем имя пользователя
    async with async_session() as session:
        profile_result = await session.execute(
            select(Profile).where(Profile.user_id == db_user.id)
        )
        profile = profile_result.scalar_one_or_none()
        name = profile.current_name if profile else ""
    
    # Формируем повествовательный текст
    if spread_type == "daily":
        text = _format_daily_spread(result, name, profile, db_user)
    elif spread_type == "decision":
        text = _format_decision_spread(result, name, question)
    else:
        text = _format_three_cards_spread(result, name, question)

    # Сохраняем в БД
    cards_data = [
        {"position": item["position"], "card": item["card"].to_dict()}
        for item in result["cards"]
    ]

    async with async_session() as session:
        reading = TarotReading(
            user_id=db_user.id,
            spread_type=spread_type,
            cards_json=cards_data,
            question=question,
            is_premium=db_user.subscription_type in ("premium", "expert"),
        )
        session.add(reading)
        await session.commit()
        await session.refresh(reading)
        reading_id = reading.id

    # Добавляем призыв к AI
    kb = tarot_interpret_kb(reading_id)
    
    if edit:
        await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


def _format_three_cards_spread(result: dict, name: str, question: str | None) -> str:
    """Форматирует расклад '3 карты' как историю."""
    cards = result["cards"]
    
    past_card = cards[0]["card"]
    present_card = cards[1]["card"]
    future_card = cards[2]["card"]
    
    past_reversed = " (перевёрнутая)" if past_card.reversed else ""
    present_reversed = " (перевёрнутая)" if present_card.reversed else ""
    future_reversed = " (перевёрнутая)" if future_card.reversed else ""
    
    # Генерируем историю
    past_story = get_card_story(past_card.name_ru, past_card.reversed)
    present_story = get_card_story(present_card.name_ru, present_card.reversed)
    future_story = get_card_story(future_card.name_ru, future_card.reversed)
    
    # Формируем ключевой вопрос
    key_questions = [
        "Что ты откладывал(а) 'потом' — и готово ли это 'потом' наступить?",
        "Какую правду ты избегаешь видеть?",
        "Что изменится, если ты перестанешь сопротивляться?",
        "Какой шаг ты боишься сделать — но знаешь, что нужно?",
        "Что ты контролируешь слишком сильно?",
    ]
    import random
    key_question = random.choice(key_questions)
    
    text = TAROT_THREE_CARDS_TEMPLATE.format(
        name=name or "Друг",
        past_card=past_card.name_ru,
        past_reversed=past_reversed,
        past_story=past_story,
        present_card=present_card.name_ru,
        present_reversed=present_reversed,
        present_story=present_story,
        future_card=future_card.name_ru,
        future_reversed=future_reversed,
        future_story=future_story,
        key_question=key_question,
    )
    
    if question:
        text = f"❓ <b>Вопрос:</b> {question}\n\n{text}"
    
    return text


def _format_daily_spread(
    result: dict, 
    name: str, 
    profile: Profile | None,
    db_user: User,
) -> str:
    """Форматирует 'Карту дня' с персонализацией."""
    from datetime import datetime
    
    card = result["cards"][0]["card"]
    reversed_mark = " (перевёрнутая)" if card.reversed else ""
    
    # Определяем время суток
    hour = datetime.now().hour
    time_of_day = get_time_greeting(hour)
    
    # Получаем историю карты
    card_story = get_card_story(card.name_ru, card.reversed)
    
    # Генерируем совет
    advices = [
        "Не принимай сегодня поспешных решений до 15:00",
        "Обрати внимание на знаки — повторяющиеся числа, песни, фразы",
        "Скажи 'да' тому, что обычно отклоняешь",
        "Сделай паузу перед ответом — даже если уверен(а)",
        "Запиши сон сегодняшней ночи — даже если кажется бредом",
    ]
    import random
    advice = random.choice(advices)
    
    # Вопрос для размышления
    reflections = [
        "Что я сопротивляюсь принять?",
        "Какую маску я ношу слишком долго?",
        "Что изменится, если я перестану бояться?",
        "Кому я должен(на) прощение — включая себя?",
        "Что я знаю, но делаю вид, что не знаю?",
    ]
    reflection = random.choice(reflections)
    
    # Персональный год
    year_hint = ""
    if profile and profile.birth_date:
        from bot.services.numerology import numerology
        personal_year = numerology.calculate_personal_year(profile.birth_date)
        year_hints = {
            1: "Год новых начинаний — карта поддерживает смелые шаги",
            2: "Год партнёрств — обрати внимание на предложения помощи",
            3: "Год творчества — экспериментируй, не жди идеальных условий",
            4: "Год работы — карта говорит о важности фундамента",
            5: "Год перемен — будь готов(а) к неожиданным поворотам",
            6: "Год отношений — семья и близкие на первом месте",
            7: "Год анализа — доверяй интуиции, она остра сейчас",
            8: "Год результатов — время собирать урожай усилий",
            9: "Год завершений — отпускай то, что отжило своё",
        }
        year_hint = year_hints.get(personal_year, "")
    
    return TAROT_DAILY_TEMPLATE.format(
        time_of_day=time_of_day,
        name=name or "Друг",
        card_name=card.name_ru,
        reversed=reversed_mark,
        card_story=card_story,
        advice=advice,
        reflection_question=reflection,
        personal_year=personal_year if profile else "—",
        year_hint=year_hint,
    )


def _format_decision_spread(result: dict, name: str, question: str | None) -> str:
    """Форматирует расклад 'Решение' с историей выбора."""
    cards = result["cards"]
    
    left_card = cards[0]["card"]   # Вариант А
    right_card = cards[1]["card"]  # Вариант Б
    center_card = cards[2]["card"]  # Суть
    
    left_reversed = " (перевёрнутая)" if left_card.reversed else ""
    right_reversed = " (перевёрнутая)" if right_card.reversed else ""
    center_reversed = " (перевёрнутая)" if center_card.reversed else ""
    
    # Истории для вариантов
    left_story = get_card_story(left_card.name_ru, left_card.reversed)
    right_story = get_card_story(right_card.name_ru, right_card.reversed)
    center_story = get_card_story(center_card.name_ru, center_card.reversed)
    
    # Рекомендация
    recommendations = [
        "Оба пути ведут к росту — выбирай тот, который пугает сильнее",
        "Суть ситуации важнее вариантов — разберись с ней первым делом",
        "Ты уже знаешь ответ — карты просто отражают это",
        "Подожди 3 дня — сейчас эмоции мешают видеть ясно",
        "Выбери вариант А, если хочешь комфорта. Вариант Б — если роста",
    ]
    import random
    recommendation = random.choice(recommendations)
    
    text = TAROT_DECISION_TEMPLATE.format(
        name=name or "Друг",
        question=question or "Выбор",
        left_card=left_card.name_ru,
        left_reversed=left_reversed,
        left_story=left_story,
        right_card=right_card.name_ru,
        right_reversed=right_reversed,
        right_story=right_story,
        center_card=center_card.name_ru,
        center_reversed=center_reversed,
        center_story=center_story,
        recommendation=recommendation,
    )
    
    return text


# ═══════════════════════════════════════════════════════════
# AI ИНТЕРПРЕТАЦИЯ
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("tarot:interpret:"))
async def tarot_interpret(callback: CallbackQuery, db_user: User) -> None:
    await callback.answer("🤖 Погружаюсь в твой расклад...")

    reading_id = int(callback.data.split(":")[2])

    # Проверка подписки
    if db_user.subscription_type not in ("premium", "expert"):
        from bot.utils.texts_new import SUBSCRIPTION_REQUIRED
        await callback.message.edit_text(
            SUBSCRIPTION_REQUIRED.format(
                feature="AI-трактовка",
                required="Premium",
                current=db_user.subscription_type.upper(),
            ),
            reply_markup=back_to_menu_kb(),
            parse_mode="HTML",
        )
        return

    # Получаем расклад
    async with async_session() as session:
        result = await session.execute(
            select(TarotReading).where(TarotReading.id == reading_id)
        )
        reading = result.scalar_one_or_none()

    if not reading:
        await callback.message.edit_text(
            "Расклад не найден.", reply_markup=back_to_menu_kb()
        )
        return

    # Получаем контекст пользователя
    async with async_session() as session:
        result = await session.execute(
            select(Profile).where(Profile.user_id == db_user.id)
        )
        profile = result.scalar_one_or_none()

    user_context = ""
    if profile and profile.birth_name:
        from bot.services.numerology import numerology as num_engine
        numbers = num_engine.full_report(profile.birth_name, profile.birth_date)
        user_context = (
            f"Число жизненного пути: {numbers['life_path']}, "
            f"Персональный год: {numbers['personal_year']}. "
            f"Это контекст для понимания энергии пользователя."
        )

    # AI-трактовка
    interpretation = await ai_interpreter.interpret_tarot(
        cards=reading.cards_json,
        question=reading.question,
        user_context=user_context,
    )

    # Сохраняем
    async with async_session() as session:
        result = await session.execute(
            select(TarotReading).where(TarotReading.id == reading_id)
        )
        reading = result.scalar_one_or_none()
        if reading:
            reading.ai_interpretation = interpretation
            await session.commit()

    text = (
        f"🤖 <b>AI-трактовка</b>\n\n"
        f"{interpretation}\n\n"
        f"<i>Это не истина — это точка обзора. "
        f"Увидел(а) что-то ценное? Запиши. Нет? Отпусти.</i>"
    )
    await callback.message.edit_text(
        text, reply_markup=back_to_menu_kb(), parse_mode="HTML"
    )
