"""Вспомогательные функции."""

from datetime import datetime, date
from typing import Optional


def parse_date(text: str) -> Optional[date]:
    """Парсит дату из строки в разных форматах."""
    formats = ["%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_time(text: str) -> Optional[str]:
    """Парсит время из строки."""
    formats = ["%H:%M", "%H.%M", "%H %M"]
    for fmt in formats:
        try:
            t = datetime.strptime(text.strip(), fmt)
            return t.strftime("%H:%M")
        except ValueError:
            continue
    return None


def format_date_ru(d: date) -> str:
    """Форматирует дату на русский."""
    months = ["", "января", "февраля", "марта", "апреля", "мая", "июня",
              "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    return f"{d.day} {months[d.month]} {d.year}"
