from datetime import datetime

from pydantic import BaseModel

from models.payment import PaymentTransactionStatus


class PaymentOut(BaseModel):
    id: int
    order_id: int
    amount: float
    payment_method: str
    transaction_id: str | None
    status: PaymentTransactionStatus
    timestamp: datetime

    class Config:
        from_attributes = True
