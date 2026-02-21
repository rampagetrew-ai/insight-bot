"""Реэкспорт текстов для обратной совместимости."""

from bot.utils.texts import *  # noqa: F401, F403

# Переменные, которые могут отсутствовать в texts.py
try:
    from bot.utils.texts import NUMEROLOGY_MENU
except ImportError:
    NUMEROLOGY_MENU = "🔢 <b>Нумерология</b>\n\nВыбери, что посчитать:"

try:
    from bot.utils.texts import NUMEROLOGY_NO_PROFILE
except ImportError:
    NUMEROLOGY_NO_PROFILE = (
        "🌙 <b>Для расчёта нужен профиль</b>\n\n"
        "Зайди в «👤 Профиль» и заполни дату рождения."
    )

try:
    from bot.utils.texts import TAROT_MENU
except ImportError:
    TAROT_MENU = "🃏 <b>Таро</b>\n\nВыбери расклад:"

try:
    from bot.utils.texts import TAROT_ASK_QUESTION
except ImportError:
    TAROT_ASK_QUESTION = (
        "❓ <b>Задай вопрос</b>\n\n"
        "Не 'буду ли я богат?', а 'что мне делать, чтобы увеличить доход?'"
    )

try:
    from bot.utils.texts import LIMIT_REACHED
except ImportError:
    LIMIT_REACHED = (
        "🌙 <b>Лимит на сегодня исчерпан</b>\n\n"
        "Подпишись для большего доступа или подожди до завтра."
    )

try:
    from bot.utils.texts import SUBSCRIPTION_REQUIRED
except ImportError:
    SUBSCRIPTION_REQUIRED = (
        "🔒 <b>Эта функция в Premium</b>\n\n"
        "{feature} доступно с подписки <b>{required}</b>.\n"
        "Твоя подписка: <b>{current}</b>"
    )
