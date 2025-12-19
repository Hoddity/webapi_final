import logging
from typing import Dict, Any, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..config import settings
from ..models.currency import CurrencyRate

logger = logging.getLogger(__name__)

class CurrencyService:
    """Сервис для получения и обработки курсов валют"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_cbr_rates(self) -> Optional[Dict[str, Any]]:
        """Получение курсов валют с ЦБ РФ"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(settings.cbr_url, timeout=10.0)
                data = response.json()

                usd_rate = data.get("Valute", {}).get("USD", {}).get("Value")
                eur_rate = data.get("Valute", {}).get("EUR", {}).get("Value")
                jpy_rate = data.get("Valute", {}).get("JPY", {}).get("Value")

                if all([usd_rate, eur_rate, jpy_rate]):
                    return {
                        "source": "cbr",
                        "usd_rate": float(usd_rate),
                        "eur_rate": float(eur_rate),
                        "jpy_rate": float(jpy_rate),
                        "raw_data": data
                    }

        except Exception as e:
            logger.error(f"Error fetching CBR rates: {e}")
        return None

    async def fetch_ecb_rates(self) -> Optional[Dict[str, Any]]:
        """Получение курсов валют с ЕЦБ (через exchangerate-api)"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(settings.ecb_url, timeout=10.0)
                data = response.json()

                # Получаем курсы USD и JPY относительно EUR
                usd_rate = data.get("rates", {}).get("USD")
                jpy_rate = data.get("rates", {}).get("JPY")

                if usd_rate and jpy_rate:
                    return {
                        "source": "ecb",
                        "usd_rate": float(usd_rate),
                        "eur_rate": 1.0,  # Базовая валюта
                        "jpy_rate": float(jpy_rate),
                        "raw_data": data
                    }

        except Exception as e:
            logger.error(f"Error fetching ECB rates: {e}")
        return None

    async def fetch_binance_rates(self) -> Optional[Dict[str, Any]]:
        """Получение курсов криптовалют с Binance"""
        try:
            async with httpx.AsyncClient() as client:
                # Получаем основные пары
                symbols = ["BTCUSDT", "ETHUSDT", "EURUSDT", "JPYUSDT"]
                results = {}

                for symbol in symbols:
                    try:
                        response = await client.get(
                            f"{settings.binance_url}?symbol={symbol}",
                            timeout=10.0
                        )
                        data = response.json()
                        results[symbol] = float(data.get("price", 0))
                    except:
                        results[symbol] = None

                # Преобразуем курсы
                btc_rate = results.get("BTCUSDT")
                eth_rate = results.get("ETHUSDT")
                eur_rate = results.get("EURUSDT")
                jpy_rate = results.get("JPYUSDT")

                # USD курс для Binance всегда 1 (базовая валюта)
                return {
                    "source": "binance",
                    "usd_rate": 1.0,
                    "eur_rate": eur_rate,
                    "jpy_rate": jpy_rate,
                    "btc_rate": btc_rate,
                    "eth_rate": eth_rate,
                    "raw_data": results
                }

        except Exception as e:
            logger.error(f"Error fetching Binance rates: {e}")
        return None

    async def save_currency_rate(self, data: Dict[str, Any]) -> Optional[CurrencyRate]:
        """Сохранение курса валюты в БД"""
        try:
            currency_rate = CurrencyRate(**data)
            self.db.add(currency_rate)
            await self.db.commit()
            await self.db.refresh(currency_rate)

            logger.info(f"Saved currency rate from {data['source']}")
            return currency_rate

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error saving currency rate: {e}")
            return None

    async def get_latest_rates(self, source: Optional[str] = None):
        """Получение последних курсов"""
        query = select(CurrencyRate).order_by(CurrencyRate.timestamp.desc())

        if source:
            query = query.where(CurrencyRate.source == source)

        result = await self.db.execute(query)
        rates = result.scalars().all()

        return [rate.to_dict() for rate in rates]

    async def get_rate_by_id(self, rate_id: int):
        """Получение курса по ID"""
        query = select(CurrencyRate).where(CurrencyRate.id == rate_id)
        result = await self.db.execute(query)
        rate = result.scalar_one_or_none()

        return rate.to_dict() if rate else None