from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from models.order import Order, OrderStatus
from models.notification import Notification
from models.return_request import ReturnRequest, ReturnStatus
from models.user import User
from schemas.return_request import ReturnRequestCreate, ReturnRequestOut

router = APIRouter(prefix="/orders", tags=["returns"])

RETURN_WINDOW_DAYS = 7


@router.post("/{order_id}/return", response_model=ReturnRequestOut)
def request_return(
    order_id: int,
    payload: ReturnRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only request a return on your own order")

    if order.order_status != OrderStatus.DELIVERED:
        raise HTTPException(status_code=400, detail="Return can only be requested for delivered orders")

    window_end = order.created_at + timedelta(days=RETURN_WINDOW_DAYS)
    if datetime.utcnow() > window_end:
        raise HTTPException(
            status_code=400,
            detail=f"Return window has expired ({RETURN_WINDOW_DAYS} days from order date)",
        )

    existing = (
        db.query(ReturnRequest)
        .filter(ReturnRequest.order_id == order_id, ReturnRequest.status == ReturnStatus.PENDING)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="A return request is already pending for this order")

    return_request = ReturnRequest(
        order_id=order.id,
        user_id=current_user.id,
        reason=payload.reason,
        comment=payload.comment,
        status=ReturnStatus.PENDING,
    )
    db.add(return_request)

    order.order_status = OrderStatus.RETURN_REQUESTED

    db.add(
        Notification(
            user_id=current_user.id,
            type="return_requested",
            message=f"Return requested for Order #{order.id}: {payload.reason}",
        )
    )

    db.commit()
    db.refresh(return_request)
    return return_request
