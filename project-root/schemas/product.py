from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    price: float
    stock: int = 0
    images: List[str] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    images: Optional[List[str]] = None


class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    price: float
    stock: int
    images: List[str]
    popularity: int
    created_at: datetime

    class Config:
        from_attributes = True