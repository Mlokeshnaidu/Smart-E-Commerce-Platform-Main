from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from models.cart import Cart
from models.notification import Notification
from models.order import Order, OrderItem, OrderStatus, PaymentStatus
from models.payment import Payment, PaymentTransactionStatus
from models.user import User
from schemas.order import CheckoutResponse, OrderOut
from utils.stripe_service import create_checkout_session, construct_webhook_event
from utils.email_service import send_order_confirmation_email, send_payment_status_email
from utils.websocket_manager import manager

router = APIRouter(tags=["checkout"])


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Re-validate stock at checkout time, not just at add-to-cart time
    for item in cart.items:
        if item.quantity > item.product.stock:
            raise HTTPException(
                status_code=400,
                detail=f"'{item.product.name}' only has {item.product.stock} in stock",
            )

    total = sum(item.product.price * item.quantity for item in cart.items)

    order = Order(user_id=current_user.id, total=round(total, 2))
    db.add(order)
    db.flush()

    for item in cart.items:
        db.add(OrderItem(order_id=order.id, product_id=item.product_id, quantity=item.quantity, price=item.product.price))
        item.product.stock -= item.quantity

    payment = Payment(order_id=order.id, amount=order.total, status=PaymentTransactionStatus.PENDING)
    db.add(payment)

    for item in list(cart.items):
        db.delete(item)

    # Call Stripe BEFORE committing, so a Stripe failure rolls back
    # the whole order/stock-decrement/cart-clear cleanly instead of
    # leaving a paid-for-nothing order stuck in the DB.
    db.flush()
    try:
        session = create_checkout_session(order.id, order.total)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"Stripe error: {str(e)}")

    payment.transaction_id = session.id
    db.commit()
    db.refresh(order)

    # Email/websocket failures shouldn't fail a checkout that already succeeded
    try:
        send_order_confirmation_email(current_user.email, order.id, order.total)
    except Exception:
        pass
    try:
        await manager.send_to_user(current_user.id, "order_status_updated", {"order_id": order.id, "status": order.order_status.value})
    except Exception:
        pass

    db.add(Notification(
        user_id=current_user.id,
        type="order_confirmed",
        message=f"Order #{order.id} confirmed for ${order.total:.2f}",
    ))
    db.commit()

    return CheckoutResponse(
        order_id=order.id,
        checkout_session_id=session.id,
        checkout_url=session.url,
        client_secret=session.get("client_secret") or "",
    )


@router.post("/checkout/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        event = construct_webhook_event(payload, sig_header)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        order_id = int(session["metadata"]["order_id"])
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.payment_status = PaymentStatus.PAID
            order.order_status = OrderStatus.PAID
            if order.payment:
                order.payment.status = PaymentTransactionStatus.SUCCEEDED
            db.commit()
            try:
                send_payment_status_email(order.user.email, order.id, success=True)
            except Exception:
                pass
            try:
                await manager.send_to_user(order.user_id, "order_status_updated", {"order_id": order.id, "status": order.order_status.value})
            except Exception:
                pass

            db.add(Notification(
                user_id=order.user_id,
                type="payment_success",
                message=f"Payment successful for order #{order.id}",
            ))
            db.commit()

    return {"received": True}


@router.get("/orders", response_model=List[OrderOut])
def list_my_orders(db=Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
