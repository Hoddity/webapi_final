from fastapi import FastAPI
from contextlib import asynccontextmanager

from api.endpoints import router as api_router
from ws.endpoints import router as ws_router
from tasks.background import lifespan
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Создание приложения с контекстом жизненного цикла
app = FastAPI(
    title="Currency Parser API",
    description="Асинхронный парсер курсов валют с REST API, WebSocket и NATS",
    version="1.0.0",
    lifespan=lifespan
)

# Подключаем роутеры
app.include_router(api_router, prefix="/api/v1", tags=["API"])
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Currency Parser API",
        "docs": "/docs",
        "websocket": "/ws/rates",
        "endpoints": {
            "rates": "/api/v1/rates",
            "manual_task": "/api/v1/tasks/run"
        }
    }

@app.get("/health")
async def health_check():
    """Эндпоинт для проверки здоровья приложения"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",  # Изменено с app.main:app на main:app
        host="0.0.0.0",
        port=8000,
        reload=True
    )