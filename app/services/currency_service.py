import httpx
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.currency import CurrencyRate
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class CurrencyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_binance_rates(self) -> Optional[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient() as client:
                symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "EURUSDT"]
                results = {}

                for symbol in symbols:
                    try:
                        response = await client.get(
                            f"{settings.binance_url}?symbol={symbol}",
                            timeout=10.0
                        )
                        if response.status_code == 200:
                            data = response.json()
                            results[symbol] = float(data.get("price", 0))
                        else:
                            results[symbol] = None
                            logger.warning(f"Символ {symbol} не найден или ошибка: {response.status_code}")
                    except Exception as e:
                        results[symbol] = None
                        logger.error(f"Ошибка получения {symbol}: {e}")

                return {
                    "source": "binance",
                    "btc_usdt": results.get("BTCUSDT"),
                    "eth_usdt": results.get("ETHUSDT"),
                    "bnb_usdt": results.get("BNBUSDT"),
                    "eur_usdt": results.get("EURUSDT"),
                    "raw_data": results
                }

        except Exception as e:
            logger.error(f"Ошибка получения курсов с Binance: {e}")
            return None


    async def save_currency_rate(self, data: Dict[str, Any]) -> Optional[CurrencyRate]:
        try:
            currency_rate = CurrencyRate(**data)
            self.db.add(currency_rate)
            await self.db.commit()
            await self.db.refresh(currency_rate)

            logger.debug(f"Сохраненный курс валюты из {data['source']}")
            return currency_rate

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Ошибка сохранения курса валюты из: {e}")
            return None

    async def get_latest_rates(self, limit: int = 10):
        query = select(CurrencyRate).order_by(CurrencyRate.timestamp.desc()).limit(limit)
        result = await self.db.execute(query)
        rates = result.scalars().all()

        return [rate.to_dict() for rate in rates]

    async def get_rate_by_id(self, rate_id: int):
        query = select(CurrencyRate).where(CurrencyRate.id == rate_id)
        result = await self.db.execute(query)
        rate = result.scalar_one_or_none()

        return rate.to_dict() if rate else None