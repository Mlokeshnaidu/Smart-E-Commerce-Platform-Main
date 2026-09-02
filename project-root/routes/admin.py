from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.rbac import require_roles
from models.order import Order, OrderItem, OrderStatus, PaymentStatus
from models.product import Product
from models.user import User, UserRole

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/analytics/overview")
def analytics_overview(db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))):
    total_orders = db.query(func.count(Order.id)).scalar()
    total_revenue = db.query(func.coalesce(func.sum(Order.total), 0)).filter(Order.order_status != OrderStatus.CANCELLED).scalar()
    total_products = db.query(func.count(Product.id)).scalar()
    total_customers = db.query(func.count(User.id)).filter(User.role == UserRole.CUSTOMER).scalar()
    return {
        "total_orders": total_orders,
        "total_revenue": round(float(total_revenue), 2),
        "total_products": total_products,
        "total_customers": total_customers,
    }


@router.get("/analytics/top-products")
def top_products(db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))):
    results = (
        db.query(Product.id, Product.name, func.sum(OrderItem.quantity).label("units_sold"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.id, Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(10)
        .all()
    )
    return [{"product_id": r.id, "name": r.name, "units_sold": int(r.units_sold)} for r in results]


@router.get("/analytics/orders-by-status")
def orders_by_status(db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))):
    results = db.query(Order.order_status, func.count(Order.id)).group_by(Order.order_status).all()
    return {status.value: count for status, count in results}


from typing import List

from models.payment import Payment, PaymentTransactionStatus
from models.notification import Notification
from models.return_request import ReturnRequest, ReturnStatus
from schemas.return_request import ReturnRequestOut
from utils.stripe_service import create_refund
from utils.email_service import send_email


@router.get("/returns", response_model=List[ReturnRequestOut])
def list_return_requests(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.STAFF)),
):
    return db.query(ReturnRequest).order_by(ReturnRequest.created_at.desc()).all()


@router.post("/returns/{return_id}/approve", response_model=ReturnRequestOut)
def approve_return(
    return_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.STAFF)),
):
    return_request = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not return_request:
        raise HTTPException(status_code=404, detail="Return request not found")
    if return_request.status != ReturnStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending return requests can be approved")

    order = return_request.order

    for item in order.items:
        item.product.stock += item.quantity

    payment = order.payment
    if payment:
        refund = create_refund(payment.transaction_id, payment.amount)
        payment.status = PaymentTransactionStatus.REFUNDED

    return_request.status = ReturnStatus.APPROVED
    order.order_status = OrderStatus.REFUNDED
    order.payment_status = PaymentStatus.REFUNDED

    db.add(
        Notification(
            user_id=order.user_id,
            type="return_approved",
            message=f"Your return for Order #{order.id} has been approved.",
        )
    )
    db.add(
        Notification(
            user_id=order.user_id,
            type="refund_completed",
            message=f"Refund of ${payment.amount:.2f} completed for Order #{order.id}." if payment else f"Refund completed for Order #{order.id}.",
        )
    )

    db.commit()
    db.refresh(return_request)

    try:
        send_email(
            order.user.email,
            f"Return approved for Order #{order.id}",
            f"Your return request for Order #{order.id} has been approved and your refund has been processed.",
        )
    except Exception:
        pass

    return return_request


@router.post("/returns/{return_id}/reject", response_model=ReturnRequestOut)
def reject_return(
    return_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.STAFF)),
):
    return_request = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not return_request:
        raise HTTPException(status_code=404, detail="Return request not found")
    if return_request.status != ReturnStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending return requests can be rejected")

    order = return_request.order

    return_request.status = ReturnStatus.REJECTED
    order.order_status = OrderStatus.DELIVERED

    db.add(
        Notification(
            user_id=order.user_id,
            type="return_rejected",
            message=f"Your return request for Order #{order.id} has been rejected.",
        )
    )

    db.commit()
    db.refresh(return_request)

    try:
        send_email(
            order.user.email,
            f"Return rejected for Order #{order.id}",
            f"Your return request for Order #{order.id} has been rejected. Please contact support for details.",
        )
    except Exception:
        pass

    return return_request
