from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ReviewCreate(BaseModel):
    product_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    product_id: int
    user_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime
    user_email: Optional[str] = None      # populated in router

    class Config:
        from_attributes = True


class ProductRatingSummary(BaseModel):
    product_id: int
    avg_rating: float
    review_count: int
    like_count: int
    user_liked: bool = False              # True if current user liked it
    user_reviewed: bool = False           # True if current user already reviewed
