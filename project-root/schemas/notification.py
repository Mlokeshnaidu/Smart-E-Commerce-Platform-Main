from datetime import datetime

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    user_id: int
    type: str
    message: str
    read_status: bool
    timestamp: datetime

    class Config:
        from_attributes = True


class MarkReadRequest(BaseModel):
    notification_id: int
