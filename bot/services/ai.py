"""AI-интерпретатор с импортом промптов."""

import json
import structlog
import urllib.request
import urllib.error

from bot.config import settings
from bot.services.ai_prompts import (
    SYSTEM_PROMPT,
    TAROT_INTERPRET_PROMPT,
    NUMEROLOGY_INTERPRET_PROMPT,
    DAILY_CARD_PROMPT,
)

logger = structlog.get_logger()


class AIInterpreter:
    def __init__(self) -> None:
        self.yandex_api_key = settings.yandex_api_key
        self.yandex_folder_id = settings.yandex_folder_id
        self.yandex_model = settings.yandex_model
        self.anthropic_api_key = settings.anthropic_api_key
        self.claude_model = settings.claude_model

    async def interpret_tarot(self, cards: list, question: str | None = None, user_context: str = "") -> str:
        cards_text = ""
        for c in cards:
            card = c if isinstance(c, dict) else c
            card_data = card.get("card", card)
            rev = " (перевёрнутая)" if card_data.get("reversed") else ""
            kws = ", ".join(card_data.get("keywords", []))
            meaning = card_data.get("meaning", "")
            cards_text += f'- Позиция "{c.get("position", "")}": {card_data.get("name_ru", "")}{rev}'
            if kws:
                cards_text += f" — {kws}"
            if meaning:
                cards_text += f"\n  Значение: {meaning}"
            cards_text += "\n"

        prompt = TAROT_INTERPRET_PROMPT.format(
            cards=cards_text,
            question=question or "Общая интерпретация",
            user_context=user_context or "Контекст не указан",
        )

        return await self._request(prompt)

    async def interpret_numerology(self, numbers: dict, context: str = "") -> str:
        numbers_text = "\n".join(f"- {k}: {v}" for k, v in numbers.items())
        
        prompt = NUMEROLOGY_INTERPRET_PROMPT.format(
            numbers=numbers_text,
            context=context or "Контекст не указан",
        )

        return await self._request(prompt)

    async def generate_daily_insight(self, card: dict, personal_year: int | None = None) -> str:
        prompt = DAILY_CARD_PROMPT.format(
            card_name=card.get("name_ru", ""),
            personal_year=personal_year or "не указан",
        )

        return await self._request(prompt)

    async def _request(self, prompt: str) -> str:
        # Пробуем YandexGPT
        if self.yandex_api_key and self.yandex_folder_id:
            try:
                return await self._request_yandex(prompt)
            except Exception as e:
                logger.error("YandexGPT error", error=str(e))

        # Пробуем Anthropic как fallback
        if self.anthropic_api_key:
            try:
                return await self._request_anthropic(prompt)
            except Exception as e:
                logger.error("Anthropic error", error=str(e))

        return "AI-интерпретация временно недоступна. Попробуйте позже."

    async def _request_yandex(self, prompt: str) -> str:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._request_yandex_sync, prompt)

    def _request_yandex_sync(self, prompt: str) -> str:
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

        body = {
            "modelUri": f"gpt://{self.yandex_folder_id}/{self.yandex_model}",
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,
                "maxTokens": 1000,
            },
            "messages": [
                {"role": "system", "text": SYSTEM_PROMPT},
                {"role": "user", "text": prompt},
            ],
        }

        data = json.dumps(body).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.yandex_api_key}",
        }

        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        return result["result"]["alternatives"][0]["message"]["text"]

    async def _request_anthropic(self, prompt: str) -> str:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._request_anthropic_sync, prompt)

    def _request_anthropic_sync(self, prompt: str) -> str:
        url = "https://api.anthropic.com/v1/messages"

        body = {
            "model": self.claude_model,
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        }

        data = json.dumps(body).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
        }

        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        return result["content"][0]["text"]


ai_interpreter = AIInterpreter()
