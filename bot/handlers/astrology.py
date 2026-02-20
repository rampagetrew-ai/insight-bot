"""Хендлер астрологии — натальная карта, транзиты, совместимость."""

from datetime import datetime
from typing import Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from bot.database import Profile, User, async_session
from bot.keyboards.inline import back_to_menu_kb
from bot.services.astrology_engine import astrology, NatalChart
from bot.utils.personalization import get_time_greeting

router = Router(name="astrology")


class AstrologyStates(StatesGroup):
    waiting_birthplace = State()
    waiting_partner_data = State()


# ═══════════════════════════════════════════════════════════
# МЕНЮ АСТРОЛОГИИ
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "menu:astrology")
async def astrology_menu(callback: CallbackQuery, db_user: User) -> None:
    """Главное меню астрологии."""
    await callback.answer()
    
    # Проверяем подписку
    if db_user.subscription_type not in ("premium", "expert"):
        await callback.message.edit_text(
            ASTROLOGY_LOCKED,
            reply_markup=back_to_menu_kb(),
            parse_mode="HTML",
        )
        return
    
    # Проверяем, есть ли профиль
    profile = await _get_profile(db_user.id)
    has_chart = profile and profile.birth_date
    
    text = ASTROLOGY_MENU.format(
        has_chart="✅" if has_chart else "❌",
        chart_status="Карта рассчитана" if has_chart else "Нужны данные рождения",
    )
    
    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    if has_chart:
        builder.row(InlineKeyboardButton(
            text="🌟 Моя натальная карта",
            callback_data="astro:natal"
        ))
        builder.row(InlineKeyboardButton(
            text="📅 Транзиты на сегодня",
            callback_data="astro:transits"
        ))
        builder.row(InlineKeyboardButton(
            text="💕 Совместимость",
            callback_data="astro:compatibility"
        ))
    else:
        builder.row(InlineKeyboardButton(
            text="📝 Заполнить данные рождения",
            callback_data="menu:profile"
        ))
    
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="menu:back"
    ))
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


# ═══════════════════════════════════════════════════════════
# НАТАЛЬНАЯ КАРТА
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "astro:natal")
async def show_natal_chart(callback: CallbackQuery, db_user: User) -> None:
    """Показывает натальную карту."""
    await callback.answer()
    
    profile = await _get_profile(db_user.id)
    if not profile or not profile.birth_date:
        await callback.message.edit_text(
            "❌ Сначала заполни профиль с датой рождения",
            reply_markup=back_to_menu_kb(),
        )
        return
    
    # Рассчитываем карту
    chart = _calculate_chart(profile)
    if not chart:
        await callback.message.edit_text(
            "❌ Ошибка расчёта карты. Проверь данные в профиле.",
            reply_markup=back_to_menu_kb(),
        )
        return
    
    # Получаем интерпретацию триады
    triad = astrology.get_triad_interpretation(chart)
    
    name = profile.current_name or profile.birth_name or "Друг"
    
    text = _format_natal_chart(name, triad, chart)
    
    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="📅 Транзиты",
        callback_data="astro:transits"
    ))
    builder.row(InlineKeyboardButton(
        text="💕 Совместимость",
        callback_data="astro:compatibility"
    ))
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="menu:astrology"
    ))
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


def _format_natal_chart(name: str, triad: dict, chart: NatalChart) -> str:
    """Форматирует натальную карту для вывода."""
    
    lines = [
        f"🌟 <b>Натальная карта {name}</b>",
        f"",
        f"<i>Триада — три ключевые точки, которые определяют твою личность</i>",
        f"",
        f"━━━━━━━━━━━━━━━━━━",
        f"",
    ]
    
    # Солнце
    sun = triad["sun"]
    lines.extend([
        f"{sun['emoji']} <b>{sun['title']}</b>",
        f"{sun['sign']} ({sun['element']})",
        f"{sun['house']}",
        f"",
        f"<i>{sun['meaning']}</i>",
        f"",
    ])
    
    # Луна
    moon = triad["moon"]
    lines.extend([
        f"{moon['emoji']} <b>{moon['title']}</b>",
        f"{moon['sign']} ({moon['element']})",
        f"{moon['house']}",
        f"",
        f"<i>{moon['meaning']}</i>",
        f"",
    ])
    
    # Асцендент
    asc = triad["ascendant"]
    lines.extend([
        f"{asc['emoji']} <b>{asc['title']}</b>",
        f"{asc['sign']} ({asc['element']})",
        f"{asc['house']}",
        f"",
        f"<i>{asc['meaning']}</i>",
        f"",
    ])
    
    # Синтез
    lines.extend([
        f"━━━━━━━━━━━━━━━━━━",
        f"",
        f"💡 <b>Синтез:</b>",
        f"<i>{triad['synthesis']}</i>",
        f"",
    ])
    
    # Дополнительные планеты (для Expert)
    if chart.mercury:
        lines.extend([
            f"📊 <b>Дополнительно:</b>",
            f"☿ Меркурий: {chart.mercury.sign}",
            f"♀ Венера: {chart.venus.sign if chart.venus else '—'}",
            f"♂ Марс: {chart.mars.sign if chart.mars else '—'}",
        ])
    
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# ТРАНЗИТЫ
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "astro:transits")
async def show_transits(callback: CallbackQuery, db_user: User) -> None:
    """Показывает транзиты на сегодня."""
    await callback.answer()
    
    profile = await _get_profile(db_user.id)
    if not profile or not profile.birth_date:
        await callback.message.edit_text(
            "❌ Сначала заполни профиль",
            reply_markup=back_to_menu_kb(),
        )
        return
    
    chart = _calculate_chart(profile)
    if not chart:
        await callback.message.edit_text(
            "❌ Ошибка расчёта",
            reply_markup=back_to_menu_kb(),
        )
        return
    
    # Рассчитываем транзиты
    transits = astrology.calculate_transits(chart)
    
    hour = datetime.now().hour
    time_greeting = get_time_greeting(hour)
    
    name = profile.current_name or profile.birth_name or "Друг"
    
    text = _format_transits(name, time_greeting, transits, chart)
    
    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🌟 Моя карта",
        callback_data="astro:natal"
    ))
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="menu:astrology"
    ))
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


def _format_transits(name: str, time: str, transits: list, chart: NatalChart) -> str:
    """Форматирует транзиты."""
    
    lines = [
        f"📅 <b>Транзиты на сегодня, {name}</b>",
        f"",
        f"<i>Как текущие положения планет влияют на твою натальную карту</i>",
        f"",
    ]
    
    if not transits:
        lines.extend([
            f"🌙 <b>Спокойный день</b>",
            f"",
            f"Нет сильных транзитов. Хороший момент для рутинных дел,",
            f"отдыха, завершения старых проектов.",
        ])
    else:
        for transit in transits:
            intensity = "🔥" if transit.get("intensity") == "high" else "🌙"
            lines.extend([
                f"{intensity} <b>{transit.get('planet', 'Планета')}</b>",
                f"{transit.get('meaning', '')}",
                f"",
            ])
    
    lines.extend([
        f"",
        f"💡 <b>Совет дня:</b>",
        f"<i>{_get_daily_advice(chart, transits)}</i>",
    ])
    
    return "\n".join(lines)


def _get_daily_advice(chart: NatalChart, transits: list) -> str:
    """Генерирует совет на день."""
    sun_sign = chart.sun.sign
    
    advices = {
        "Aries": "Сегодня твоя энергия высока — начни то, что откладывал",
        "Taurus": "Потрать время на что-то приятное для тела — вкусная еда, массаж",
        "Gemini": "Позвони старому другу или напиши — связи активируют удачу",
        "Cancer": "Побудь дома, с семьёй. Эмоциональная перезагрузка важнее дел",
        "Leo": "Покажи себя — даже если кажется, что никто не смотрит",
        "Virgo": "Сделай маленькое дело идеально, а не многое наспех",
        "Libra": "Примирение или компромисс сегодня принесёт больше, чем победа",
        "Scorpio": "Не бойся заглянуть в тень — там твоя сила",
        "Sagittarius": "Узнай что-то новое или спланируй поездку",
        "Capricorn": "Шаг назад для обзора — не отступление, тактика",
        "Aquarius": "Необычное решение сегодня — правильное",
        "Pisces": "Доверься интуиции, даже если логика против",
    }
    
    return advices.get(sun_sign, "Слушай себя — ты уже знаешь ответ")


# ═══════════════════════════════════════════════════════════
# СОВМЕСТИМОСТЬ
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "astro:compatibility")
async def compatibility_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начинает расчёт совместимости."""
    await callback.answer()
    
    await callback.message.edit_text(
        COMPATIBILITY_ASK_PARTNER,
        parse_mode="HTML",
    )
    await state.set_state(AstrologyStates.waiting_partner_data)


@router.message(AstrologyStates.waiting_partner_data)
async def process_partner_data(message: Message, state: FSMContext, db_user: User) -> None:
    """Обрабатывает данные партнёра."""
    await state.clear()
    
    # Парсим ввод: дата [время] [место]
    # Пример: "15.03.1990 14:30 Москва" или "15.03.1990"
    
    text = message.text.strip()
    parts = text.split()
    
    if len(parts) < 1:
        await message.answer(
            "❌ Нужна хотя бы дата. Пример: <code>15.03.1990</code>",
            parse_mode="HTML",
        )
        return
    
    # Парсим дату
    from bot.utils.helpers import parse_date
    partner_date = parse_date(parts[0])
    
    if not partner_date:
        await message.answer(
            "❌ Не распознал дату. Формат: <code>15.03.1990</code>",
            parse_mode="HTML",
        )
        return
    
    # Получаем свою карту
    profile = await _get_profile(db_user.id)
    if not profile:
        await message.answer("❌ Сначала заполни свой профиль")
        return
    
    my_chart = _calculate_chart(profile)
    partner_chart = astrology.calculate_natal_chart(
        partner_date, None, 55.75, 37.61  # Москва по умолчанию
    )
    
    if not my_chart or not partner_chart:
        await message.answer("❌ Ошибка расчёта карт")
        return
    
    # Рассчитываем совместимость
    compatibility = _calculate_compatibility(my_chart, partner_chart)
    
    text = _format_compatibility(compatibility, my_chart, partner_chart)
    
    await message.answer(
        text,
        reply_markup=back_to_menu_kb(),
        parse_mode="HTML",
    )


def _calculate_compatibility(chart1: NatalChart, chart2: NatalChart) -> dict:
    """Рассчитывает совместимость двух карт."""
    
    # Элементы
    elem1 = astrology.SIGN_ELEMENTS.get(chart1.sun.sign, "")
    elem2 = astrology.SIGN_ELEMENTS.get(chart2.sun.sign, "")
    
    # Совместимость элементов
    element_compatibility = {
        ("Огонь", "Огонь"): 70,
        ("Огонь", "Воздух"): 90,
        ("Огонь", "Земля"): 40,
        ("Огонь", "Вода"): 30,
        ("Земля", "Земля"): 80,
        ("Земля", "Вода"): 90,
        ("Земля", "Огонь"): 40,
        ("Земля", "Воздух"): 30,
        ("Воздух", "Воздух"): 75,
        ("Воздух", "Огонь"): 90,
        ("Воздух", "Земля"): 30,
        ("Воздух", "Вода"): 40,
        ("Вода", "Вода"): 85,
        ("Вода", "Земля"): 90,
        ("Вода", "Огонь"): 30,
        ("Вода", "Воздух"): 40,
    }
    
    sun_score = element_compatibility.get((elem1, elem2), 50)
    
    # Луна — эмоциональная совместимость
    moon_elem1 = astrology.SIGN_ELEMENTS.get(chart1.moon.sign, "")
    moon_elem2 = astrology.SIGN_ELEMENTS.get(chart2.moon.sign, "")
    moon_score = element_compatibility.get((moon_elem1, moon_elem2), 50)
    
    # Итоговый процент
    total = int((sun_score * 0.6) + (moon_score * 0.4))
    
    return {
        "total": total,
        "sun_score": sun_score,
        "moon_score": moon_score,
        "element1": elem1,
        "element2": elem2,
        "strength": _get_compatibility_strength(total),
        "challenge": _get_compatibility_challenge(chart1, chart2),
    }


def _get_compatibility_strength(score: int) -> str:
    """Возвращает силу совместимости."""
    if score >= 80:
        return "Гармоничный союз — энергии дополняют друг друга"
    elif score >= 60:
        return "Хорошая совместимость — нужно учитывать различия"
    elif score >= 40:
        return "Средняя совместимость — требует работы и компромиссов"
    else:
        return "Сложный союз — но именно в этом может быть рост"


def _get_compatibility_challenge(chart1: NatalChart, chart2: NatalChart) -> str:
    """Возвращает главную сложность в паре."""
    
    # Разные стихии Солнца
    elem1 = astrology.SIGN_ELEMENTS.get(chart1.sun.sign, "")
    elem2 = astrology.SIGN_ELEMENTS.get(chart2.sun.sign, "")
    
    if {elem1, elem2} == {"Огонь", "Вода"}:
        return "🔥💧 Огонь и Вода — страсть и эмоции. Риск сжечь друг друга или создать пар"
    elif {elem1, elem2} == {"Огонь", "Земля"}:
        return "🔥🌍 Огонь хочет двигаться, Земля — стабильности. Найти баланс скорости и корней"
    elif {elem1, elem2} == {"Воздух", "Вода"}:
        return "💨💧 Воздух анализирует, Вода чувствует. Риск непонимания языков любви"
    elif {elem1, elem2} == {"Земля", "Воздух"}:
        return "🌍💨 Земля практична, Воздух теоретизирует. Соединить реальность с идеями"
    else:
        return "Одинаковые стихии — комфортно, но риск застоя без роста"


def _format_compatibility(comp: dict, chart1: NatalChart, chart2: NatalChart) -> str:
    """Форматирует результат совместимости."""
    
    # Прогресс-бар
    filled = comp["total"] // 10
    bar = "█" * filled + "░" * (10 - filled)
    
    return (
        f"💕 <b>Совместимость</b>\n\n"
        f"{chart1.sun.sign} + {chart2.sun.sign}\n"
        f"{comp['element1']} + {comp['element2']}\n\n"
        f"<b>Совместимость: {comp['total']}%</b>\n"
        f"<code>{bar}</code>\n\n"
        f"☉ Солнце: {comp['sun_score']}% — совместимость личностей\n"
        f"☽ Луна: {comp['moon_score']}% — эмоциональная гармония\n\n"
        f"💪 <b>Сила союза:</b>\n"
        f"<i>{comp['strength']}</i>\n\n"
        f"⚡ <b>Главный вызов:</b>\n"
        f"<i>{comp['challenge']}</i>\n\n"
        f"<i>Помни: астрология — не приговор, а карта. "
        f"Выбор всегда за вами.</i>"
    )


# ═══════════════════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════

async def _get_profile(user_id: int) -> Optional[Profile]:
    """Получает профиль пользователя."""
    async with async_session() as session:
        result = await session.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()


def _calculate_chart(profile: Profile) -> Optional[NatalChart]:
    """Рассчитывает натальную карту из профиля."""
    if not profile.birth_date:
        return None
    
    # Координаты по умолчанию (Москва)
    lat, lon = 55.75, 37.61
    
    # TODO: геокодинг для определения координат по месту рождения
    
    return astrology.calculate_natal_chart(
        profile.birth_date,
        profile.birth_time,
        lat,
        lon,
    )


# ═══════════════════════════════════════════════════════════
# ТЕКСТЫ
# ═══════════════════════════════════════════════════════════

ASTROLOGY_MENU = (
    "🌟 <b>Астрология</b>\n\n"
    "Натальная карта — это снимок неба в момент твоего рождения. "
    "Не предсказание, а карта твоих потенциалов и паттернов.\n\n"
    "Статус карты: {has_chart} {chart_status}\n\n"
    "Выбери:"
)

ASTROLOGY_LOCKED = (
    "🔒 <b>Астрология — в Expert</b>\n\n"
    "Натальная карта, транзиты и совместимость доступны с подписки Expert.\n\n"
    "🌟 <b>Что включено:</b>\n"
    "• Расчёт натальной карты (Солнце, Луна, Асцендент)\n"
    "• Транзиты на сегодня\n"
    "• Совместимость с партнёром\n"
    "• Персональный календарь\n\n"
    "🏆 <b>Expert — 1499₽/мес</b>\n"
    "Безлимит всех функций + астрология"
)

COMPATIBILITY_ASK_PARTNER = (
    "💕 <b>Совместимость</b>\n\n"
    "Введи данные партнёра:\n"
    "<code>ДД.ММ.ГГГГ [время] [место]</code>\n\n"
    "Примеры:\n"
    "• <code>15.03.1990</code> — только дата\n"
    "• <code>15.03.1990 14:30</code> — с временем\n"
    "• <code>15.03.1990 14:30 Москва</code> — полные данные\n\n"
    "💡 <i>Чем точнее данные, тем точнее результат</i>"
)
