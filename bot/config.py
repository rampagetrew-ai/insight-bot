"""Конфигурация бота из .env."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram
    bot_token: str = ""

    # Database
    db_host: str = "db"
    db_port: int = 5432
    db_name: str = "insight_bot"
    db_user: str = "insight"
    db_password: str = "changeme"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Claude AI
    anthropic_api_key: str = ""
    claude_model: str = "claude-3-5-haiku-latest"

    # YandexGPT
    yandex_api_key: str = ""
    yandex_folder_id: str = ""
    yandex_model: str = "yandexgpt-lite"

    # Payments
    payment_provider_token: str = ""

    # Prices (kopecks)
    price_basic: int = 29900
    price_premium: int = 59900
    price_expert: int = 149900

    # Limits
    rate_limit_free_daily: int = 1
    rate_limit_basic_daily: int = 10
    rate_limit_premium_daily: int = 50
    log_level: str = "INFO"

    # Superadmin
    super_admin_username: str = "ALTLPU"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
