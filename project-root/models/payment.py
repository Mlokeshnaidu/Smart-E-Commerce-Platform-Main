import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from core.database import Base


class PaymentTransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), default="stripe")
    transaction_id = Column(String(255), nullable=True)
    status = Column(
        Enum(PaymentTransactionStatus, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        default=PaymentTransactionStatus.PENDING,
    )
    timestamp = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="payment")