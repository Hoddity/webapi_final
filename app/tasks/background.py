import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.session import AsyncSessionLocal
from ..services.currency_service import CurrencyService
from ..ws.manager import ws_manager
from ..nats.client import nats_client
from ..config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BackgroundTask:
    def __init__(self):
        self.task = None
        self.is_running = False

    async def run_once(self):
        async with AsyncSessionLocal() as session:
            service = CurrencyService(session)

            try:
                data = await service.fetch_binance_rates()
                if data:
                    saved_rate = await service.save_currency_rate(data)

                    if saved_rate:
                        # Публикуем в NATS
                        nats_data = {
                            "event_type": "rate_updated",
                            "timestamp": datetime.now().isoformat(),
                            "data": saved_rate.to_dict()
                        }
                        await nats_client.publish(nats_data)

                        # Отправляем через WebSocket
                        ws_message = {
                            "event_type": "rate_updated",
                            "data": nats_data
                        }
                        await ws_manager.broadcast(ws_message)

                        logger.info(f"Successfully processed rates")

            except Exception as e:
                logger.error(f"Error processing : {e}")


    async def run_periodically(self):

        self.is_running = True

        while self.is_running:
            try:
                await self.run_once()
            except Exception as e:
                logger.error(f"Ошибка фоновой задачи: {e}")

            # Ожидание перед следующим запуском
            await asyncio.sleep(settings.background_task_interval)

    async def start(self):
        if not self.is_running:
            self.task = asyncio.create_task(self.run_periodically())
            logger.info("Фоновая задача запущена")

    async def stop(self):
        """Остановка фоновой задачи"""
        if self.is_running:
            self.is_running = False
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
            logger.info("Фоновая задача приостановлена")

    async def run_manually(self):
        """Ручной запуск задачи"""
        logger.info("Ручной запуск фоновой задачи")
        await self.run_once()

# Глобальный экземпляр задачи
background_task = BackgroundTask()

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting application...")

    from app.db.session import init_db
    await init_db()

    # 1. Подключение к NATS
    await nats_client.connect()

    # 2. Подписка на NATS (КРИТИЧНО)
    await nats_client.subscribe()

    # 3. Запуск фоновой задачи
    await background_task.start()

    yield

    logger.info("Shutting down application...")
    await background_task.stop()
    await nats_client.close()