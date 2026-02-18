# Insight Bot

Интеллектуальный Telegram-помощник для принятия решений на основе нумерологии, таро и астрологии.

## Быстрый старт

### 1. Настройка

```bash
cp .env.example .env
# Заполните BOT_TOKEN, DB_PASSWORD, ANTHROPIC_API_KEY
```

### 2. Docker

```bash
docker-compose up -d
```

### 3. Локальная разработка

```bash
pip install -r requirements.txt
docker-compose up -d db redis
python -m bot.main
```

## Деплой на Timeweb VPS

```bash
# SSH на сервер
ssh user@your-server-ip

# Установите Docker
curl -fsSL https://get.docker.com | sh

# Клонируйте проект, настройте .env
docker-compose up -d

# Проверьте логи
docker logs -f insight_bot
```

## Подписки

| План | Цена | Лимит/день | AI-трактовки |
|------|------|-----------|-------------|
| Free | 0 | 1 | Нет |
| Basic | 299/мес | 10 | Нет |
| Premium | 599/мес | 50 | Да |
| Expert | 1499/мес | Безлимит | Да + приоритет |
