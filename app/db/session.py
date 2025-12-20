from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from ..config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
)

# Создаем фабрику сессий
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """
    Dependency для получения сессии БД.
    Используется в эндпоинтах FastAPI.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """
    Инициализация БД - создание таблиц.
    Вызывается при старте приложения.
    """
    from app.models.currency import CurrencyRate
    from app.db.base import Base

    async with engine.begin() as conn:
        # Создаем все таблицы
        await conn.run_sync(Base.metadata.create_all)

    print("Database initialized")