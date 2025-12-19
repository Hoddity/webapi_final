from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from ..db.base import Base

class CurrencyRate(Base):
    """
    Модель для хранения курсов валют.
    Каждая запись содержит курсы с одного источника на момент времени.
    """
    __tablename__ = "currency_rates"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True)  # cbr, ecb, binance
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Основные валюты
    usd_rate = Column(Float, nullable=True)  # RUB/USD для CBR, EUR/USD для ECB
    eur_rate = Column(Float, nullable=True)  # RUB/EUR для CBR
    jpy_rate = Column(Float, nullable=True)  # RUB/JPY для CBR

    # Криптовалюты (только для Binance)
    btc_rate = Column(Float, nullable=True)  # BTC/USD
    eth_rate = Column(Float, nullable=True)  # ETH/USD

    # Дополнительные данные в JSON
    raw_data = Column(JSON, nullable=True)

    def to_dict(self):
        """Преобразование объекта в словарь"""
        return {
            "id": self.id,
            "source": self.source,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "usd_rate": self.usd_rate,
            "eur_rate": self.eur_rate,
            "jpy_rate": self.jpy_rate,
            "btc_rate": self.btc_rate,
            "eth_rate": self.eth_rate,
            "raw_data": self.raw_data
        }