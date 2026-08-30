from datetime import datetime
from typing import List

from pydantic import BaseModel

from models.order import OrderStatus, PaymentStatus


class OrderItemOut(BaseModel):
    product_id: int
    quantity: int
    price: float

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    user_id: int
    total: float
    payment_status: PaymentStatus
    order_status: OrderStatus
    created_at: datetime
    items: List[OrderItemOut]

    class Config:
        from_attributes = True


class CheckoutResponse(BaseModel):
    order_id: int
    checkout_session_id: str
    checkout_url: str
    client_secret: str
