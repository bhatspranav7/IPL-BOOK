from fastapi import WebSocket, APIRouter
from app.services.websocket_manager import manager

router = APIRouter()

@router.websocket("/ws/pricing")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        manager.disconnect(websocket)