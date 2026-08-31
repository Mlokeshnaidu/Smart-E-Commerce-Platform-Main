import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from core.database import Base


class ReturnStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(String(255), nullable=False)
    comment = Column(Text, nullable=True)
    status = Column(
        Enum(ReturnStatus, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        default=ReturnStatus.PENDING,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="return_requests")
    user = relationship("User")
