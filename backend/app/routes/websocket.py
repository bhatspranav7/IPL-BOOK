from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from app.services.websocket_manager import manager

router = APIRouter()


async def _serve(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


@router.websocket("/ws/events")
async def events(websocket: WebSocket):
    await _serve(websocket)


# Original endpoint name, kept for existing clients
@router.websocket("/ws/pricing")
async def pricing(websocket: WebSocket):
    await _serve(websocket)
