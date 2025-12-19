from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Настройки приложения"""
    # Настройки приложения
    app_name: str = "Currency Parser API"
    debug: bool = True

    # Настройки БД
    database_url: str = "sqlite+aiosqlite:///./currencies.db"

    # Настройки NATS
    nats_url: str = "nats://localhost:4222"
    nats_subject: str = "currency.py.updates"

    # Настройки фоновой задачи
    background_task_interval: int = 300  # секунды (5 минут)

    # Источники данных
    cbr_url: str = "https://www.cbr-xml-daily.ru/daily_json.js"
    ecb_url: str = "https://api.exchangerate-api.com/v4/latest/EUR"
    binance_url: str = "https://api.binance.com/api/v3/ticker/price"

    class Config:
        env_file = ".env"

settings = Settings()