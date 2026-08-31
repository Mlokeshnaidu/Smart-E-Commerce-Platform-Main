from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from models.return_request import ReturnStatus


class ReturnRequestCreate(BaseModel):
    reason: str
    comment: Optional[str] = None


class ReturnRequestOut(BaseModel):
    id: int
    order_id: int
    user_id: int
    reason: str
    comment: Optional[str] = None
    status: ReturnStatus
    created_at: datetime

    class Config:
        from_attributes = True
