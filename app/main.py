from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router
from app.ws.endpoints import router as ws_router
from app.tasks.background import lifespan
import logging

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s:%(name)s:%(message)s"
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
logging.getLogger("app.nats.client").setLevel(logging.WARNING)
logging.getLogger("app.tasks.background").setLevel(logging.WARNING)
logging.getLogger("app.services.currency_service").setLevel(logging.WARNING)

app = FastAPI(
    title="Currency Parser",
    description="Парсер курсов валют",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)
app.include_router(api_router, prefix="/api/v1", tags=["API"])
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
