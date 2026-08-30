from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON

from core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), index=True, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    images = Column(JSON, default=list)
    popularity = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)