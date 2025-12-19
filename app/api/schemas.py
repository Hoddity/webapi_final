from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class CurrencyRateBase(BaseModel):
    """Базовая схема для курса валюты"""
    source: str
    usd_rate: Optional[float] = None
    eur_rate: Optional[float] = None
    jpy_rate: Optional[float] = None
    btc_rate: Optional[float] = None
    eth_rate: Optional[float] = None
    raw_data: Optional[Dict[str, Any]] = None

class CurrencyRateCreate(CurrencyRateBase):
    """Схема для создания записи"""
    pass

class CurrencyRateResponse(CurrencyRateBase):
    """Схема для ответа API"""
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True  # Позволяет создавать из ORM-объектов

class TaskResponse(BaseModel):
    """Схема для ответа о запуске задачи"""
    message: str
    task_id: Optional[str] = None

class WebSocketMessage(BaseModel):
    """Схема для сообщений WebSocket"""
    event_type: str  # created, updated, deleted, rate_updated
    data: Dict[str, Any]