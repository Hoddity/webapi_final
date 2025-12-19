import asyncio
from typing import Optional, Callable, Any
import json
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class NatsClient:
    """Клиент для работы с NATS"""

    def __init__(self):
        self.nc: Optional[NATS] = None
        self.subscription = None
        self.is_connected = False

    async def connect(self):
        """Подключение к NATS"""
        try:
            self.nc = NATS()
            await self.nc.connect(servers=[settings.nats_url])
            self.is_connected = True
            logger.info(f"Connected to NATS at {settings.nats_url}")

            # Подписываемся на канал
            await self.subscribe()

        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            self.is_connected = False

    async def subscribe(self):
        """Подписка на канал обновлений валют"""
        if self.nc:
            try:
                self.subscription = await self.nc.subscribe(
                    settings.nats_subject,
                    cb=self.message_handler
                )
                logger.info(f"Subscribed to {settings.nats_subject}")
            except Exception as e:
                logger.error(f"Failed to subscribe: {e}")

    async def message_handler(self, msg):
        """Обработчик входящих сообщений"""
        try:
            data = json.loads(msg.data.decode())
            logger.info(f"Received NATS message: {data}")

            # Здесь можно добавить логику обработки сообщений
            # Например, обновление кэша или уведомление WebSocket клиентов

        except Exception as e:
            logger.error(f"Error processing NATS message: {e}")

    async def publish(self, data: dict):
        """Публикация сообщения в NATS"""
        if self.nc and self.is_connected:
            try:
                await self.nc.publish(
                    settings.nats_subject,
                    json.dumps(data).encode()
                )
                logger.info(f"Published to {settings.nats_subject}: {data}")
            except Exception as e:
                logger.error(f"Failed to publish to NATS: {e}")
        else:
            logger.warning("NATS client not connected")

    async def close(self):
        """Закрытие соединения с NATS"""
        if self.nc:
            await self.nc.close()
            self.is_connected = False
            logger.info("NATS connection closed")

# Глобальный экземпляр клиента
nats_client = NatsClient()