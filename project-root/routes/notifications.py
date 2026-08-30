from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from core.security import decode_token
from models.notification import Notification
from models.user import User
from schemas.notification import NotificationOut, MarkReadRequest
from utils.websocket_manager import manager

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.timestamp.desc()).all()


@router.post("/notifications/read", response_model=NotificationOut)
def mark_read(payload: MarkReadRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notification = db.query(Notification).filter(
        Notification.id == payload.notification_id, Notification.user_id == current_user.id
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.read_status = True
    db.commit()
    db.refresh(notification)
    return notification


@router.websocket("/ws/notifications")
async def notifications_ws(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4401)
        return
    user_id = int(payload["sub"])
    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
