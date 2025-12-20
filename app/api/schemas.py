from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class CurrencyRateBase(BaseModel):
    source: str = "binance"  # По умолчанию binance
    btc_usdt: Optional[float] = None
    eth_usdt: Optional[float] = None
    bnb_usdt: Optional[float] = None
    eur_usdt: Optional[float] = None
    raw_data: Optional[Dict[str, Any]] = None

class CurrencyRateCreate(CurrencyRateBase):
    pass

class CurrencyRateResponse(CurrencyRateBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class TaskResponse(BaseModel):
    message: str
    task_id: Optional[str] = None