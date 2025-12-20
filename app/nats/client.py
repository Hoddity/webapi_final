from typing import Optional
import json
from nats.aio.client import Client as NATS
from ..config import settings
import logging

logger = logging.getLogger("nats_file_only")

class NatsClient:

    def __init__(self):
        self.nc: Optional[NATS] = None
        self.subscription = None
        self.is_connected = False

    async def connect(self):
        try:
            self.nc = NATS()
            await self.nc.connect(servers=[settings.nats_url])
            self.is_connected = True
            print(f"[NATS] Подключен к {settings.nats_url}")

        except Exception as e:
            print(f"[NATS] Ошибка подключения: {e}")
            self.is_connected = False

    async def subscribe(self):
        if self.nc:
            try:
                self.subscription = await self.nc.subscribe(
                    settings.nats_subject,
                    cb=self.message_handler
                )
                print(f"[NATS] Подписан на канал: {settings.nats_subject}")
            except Exception as e:
                print(f"[NATS] Ошибка подписки: {e}")

    async def message_handler(self, msg):
        try:
            data = json.loads(msg.data.decode())

            print(f"NATS получил: {data}")

        except json.JSONDecodeError:
            pass
        except Exception:
            pass

    async def publish(self, data: dict):
        if self.nc and self.is_connected:
            try:
                print(f"Опубликовано в NATS: {settings.nats_subject}, message={data}")

                await self.nc.publish(
                    settings.nats_subject,
                    json.dumps(data).encode()
                )

            except Exception:
                pass
        else:
            print(f"[NATS] Клиент не подключен")

    async def close(self):
        if self.nc:
            await self.nc.close()
            self.is_connected = False
            print(f"[NATS] Соединение закрыто")

nats_client = NatsClient()