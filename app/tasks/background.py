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
                        nats_data = {
                            "event_type": "rate_updated",
                            "timestamp": datetime.now().isoformat(),
                            "data": saved_rate.to_dict()
                        }
                        await nats_client.publish(nats_data)

                        ws_message = {
                            "event_type": "rate_updated",
                            "data": nats_data
                        }
                        await ws_manager.broadcast(ws_message)

                        logger.info(f"Курсы валют успешно обработаны")

            except Exception as e:
                logger.error(f"Ошибка при обработке курсов : {e}")


    async def run_periodically(self):

        self.is_running = True

        while self.is_running:
            try:
                await self.run_once()
            except Exception as e:
                logger.error(f"Ошибка в фоновой задаче: {e}")

            await asyncio.sleep(settings.background_task_interval)

    async def start(self):
        if not self.is_running:
            self.task = asyncio.create_task(self.run_periodically())
            logger.info("Фоновая задача запущена")

    async def stop(self):
        if self.is_running:
            self.is_running = False
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
            logger.info("Фоновая задача остановлена")

    async def run_manually(self):
        logger.info("Ручной запуск фоновой задачи")
        await self.run_once()

background_task = BackgroundTask()

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Запуск приложения...")

    from app.db.session import init_db
    await init_db()

    await nats_client.connect()
    await nats_client.subscribe()
    await background_task.start()

    yield

    logger.info("Завершение работы приложения...")
    await background_task.stop()
    await nats_client.close()