from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from . import schemas
from ..services.currency_service import CurrencyService
from ..db.session import get_db
from ..tasks.background import background_task
from ..nats.client import nats_client
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/rates", response_model=List[schemas.CurrencyRateResponse])
async def get_rates(
        source: Optional[str] = None,
        limit: int = 10,
        db: AsyncSession = Depends(get_db)
):
    """
    Получение списка курсов валют
    """
    service = CurrencyService(db)
    rates = await service.get_latest_rates(source)
    return rates[:limit]

@router.get("/rates/{rate_id}", response_model=schemas.CurrencyRateResponse)
async def get_rate(
        rate_id: int,
        db: AsyncSession = Depends(get_db)
):
    """
    Получение конкретного курса по ID.
    """
    service = CurrencyService(db)
    rate = await service.get_rate_by_id(rate_id)

    if not rate:
        raise HTTPException(status_code=404, detail="Rate not found")

    return rate

@router.post("/rates", response_model=schemas.CurrencyRateResponse)
async def create_rate(
        rate_data: schemas.CurrencyRateCreate,
        db: AsyncSession = Depends(get_db)
):
    """
    Создание новой записи о курсе валюты.
    """
    service = CurrencyService(db)

    # Проверяем, есть ли уже курс за это время
    rate = await service.save_currency_rate(rate_data.dict())

    if not rate:
        raise HTTPException(status_code=400, detail="Failed to create rate")

    # Публикуем событие в NATS
    nats_data = {
        "event_type": "rate_created",
        "data": rate.to_dict()
    }
    await nats_client.publish(nats_data)

    return rate

@router.delete("/rates/{rate_id}")
async def delete_rate(
        rate_id: int,
        db: AsyncSession = Depends(get_db)
):
    """
    Удаление записи о курсе валюты.
    """
    from sqlalchemy import select, delete
    from app.models.currency import CurrencyRate

    # Проверяем существование записи
    query = select(CurrencyRate).where(CurrencyRate.id == rate_id)
    result = await db.execute(query)
    rate = result.scalar_one_or_none()

    if not rate:
        raise HTTPException(status_code=404, detail="Rate not found")

    # Сохраняем данные для NATS
    rate_data = rate.to_dict()

    # Удаляем запись
    delete_query = delete(CurrencyRate).where(CurrencyRate.id == rate_id)
    await db.execute(delete_query)
    await db.commit()

    # Публикуем событие в NATS
    nats_data = {
        "event_type": "rate_deleted",
        "data": rate_data
    }
    await nats_client.publish(nats_data)

    return {"message": "Rate deleted successfully"}

@router.post("/tasks/run", response_model=schemas.TaskResponse)
async def run_task():
    """
    Принудительный запуск фоновой задачи парсинга курсов.
    """
    try:
        await background_task.run_manually()
        return {"message": "Background task executed successfully"}
    except Exception as e:
        logger.error(f"Error executing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))