from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.api import schemas
from app.services.currency_service import CurrencyService
from app.db.session import get_db
from app.tasks.background import background_task
from app.nats.client import nats_client
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/rates", response_model=List[schemas.CurrencyRateResponse])
async def get_rates(
        limit: int = 10,
        db: AsyncSession = Depends(get_db)
):
    service = CurrencyService(db)
    rates = await service.get_latest_rates(limit)
    return rates

@router.get("/rates/{rate_id}", response_model=schemas.CurrencyRateResponse)
async def get_rate(
        rate_id: int,
        db: AsyncSession = Depends(get_db)
):
    service = CurrencyService(db)
    rate = await service.get_rate_by_id(rate_id)

    if not rate:
        raise HTTPException(status_code=404, detail="Курсы валют не найдены")

    return rate

@router.post("/rates", response_model=schemas.CurrencyRateResponse)
async def create_rate(
        rate_data: schemas.CurrencyRateCreate,
        db: AsyncSession = Depends(get_db)
):
    service = CurrencyService(db)

    rate = await service.save_currency_rate(rate_data.dict())

    if not rate:
        raise HTTPException(status_code=400, detail="Ошибка создания курса валюты")

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
    from sqlalchemy import select, delete
    from app.models.currency import CurrencyRate

    query = select(CurrencyRate).where(CurrencyRate.id == rate_id)
    result = await db.execute(query)
    rate = result.scalar_one_or_none()

    if not rate:
        raise HTTPException(status_code=404, detail="Курс валюты не найден")

    rate_data = rate.to_dict()

    delete_query = delete(CurrencyRate).where(CurrencyRate.id == rate_id)
    await db.execute(delete_query)
    await db.commit()

    nats_data = {
        "event_type": "rate_deleted",
        "data": rate_data
    }
    await nats_client.publish(nats_data)

    return {"message": "Курс валюты успешно удален"}

@router.post("/tasks/run", response_model=schemas.TaskResponse)
async def run_task():

    try:
        await background_task.run_manually()
        return {"message": "Фоновая задача успешно запущена"}
    except Exception as e:
        logger.error(f"Ошибка запуска фоновой задачи: {e}")
        raise HTTPException(status_code=500, detail=str(e))