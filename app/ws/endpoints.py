from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws.manager import ws_manager
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/rates")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)

    try:
        welcome_message = {
            "event_type": "connected",
            "data": {
                "message": "Connected to Currency Parser WebSocket",
                "supported_events": ["rate_updated", "rate_created", "rate_deleted"]
            }
        }
        await ws_manager.send_personal_message(welcome_message, websocket)


        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                if message.get("action") == "ping":
                    await ws_manager.send_personal_message({
                        "event_type": "pong",
                        "data": {"timestamp": "now"}
                    }, websocket)

                elif message.get("action") == "subscribe":
                    await ws_manager.send_personal_message({
                        "event_type": "subscribed",
                        "data": {"channels": message.get("channels", ["all"])}
                    }, websocket)

            except json.JSONDecodeError:
                await ws_manager.send_personal_message({
                    "event_type": "error",
                    "data": {"message": "Invalid JSON"}
                }, websocket)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("WebSocket отключился")

    except Exception as e:
        logger.error(f"WebSocket ошибка: {e}")
        ws_manager.disconnect(websocket)