from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from models.review import ReviewStatus


class ReviewCreate(BaseModel):
    product_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    user_id: int
    product_id: int
    rating: int
    comment: Optional[str] = None
    status: ReviewStatus
    created_at: datetime

    class Config:
        from_attributes = True


class ProductReviewsOut(BaseModel):
    average_rating: float
    total_reviews: int
    reviews: List[ReviewOut]
