import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship

from core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    STAFF = "staff"
    CUSTOMER = "customer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=True)
    role = Column(
        Enum(UserRole, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        default=UserRole.CUSTOMER,
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    auth0_id = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    cart = relationship("Cart", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user")
    notifications = relationship("Notification", back_populates="user")