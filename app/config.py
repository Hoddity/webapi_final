from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Crypto Parser API (Binance)"
    debug: bool = True

    database_url: str = "sqlite+aiosqlite:///./crypto.db"
    nats_url: str = "nats://localhost:4222"
    nats_subject: str = "crypto.updates"

    background_task_interval: int = 60

    binance_url: str = "https://api.binance.com/api/v3/ticker/price"

    class Config:
        env_file = ".env"

settings = Settings()