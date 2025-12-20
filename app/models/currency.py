from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base import Base

class CurrencyRate(Base):
    __tablename__ = "currency_rates"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, default="binance")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    btc_usdt = Column(Float, nullable=True)
    eth_usdt = Column(Float, nullable=True)
    bnb_usdt = Column(Float, nullable=True)
    eur_usdt = Column(Float, nullable=True)

    raw_data = Column(JSON, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "source": self.source,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "btc_usdt": self.btc_usdt,
            "eth_usdt": self.eth_usdt,
            "bnb_usdt": self.bnb_usdt,
            "eur_usdt": self.eur_usdt,
            "raw_data": self.raw_data
        }