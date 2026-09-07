from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from models.order import Order, OrderItem, OrderStatus
from models.product import Product
from models.review import Review, ReviewStatus
from models.user import User
from schemas.review import ReviewCreate, ReviewOut, ProductReviewsOut

router = APIRouter(tags=["reviews"])


@router.post("/reviews", response_model=ReviewOut, status_code=201)
def create_review(
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    has_completed_order = (
        db.query(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(
            Order.user_id == current_user.id,
            OrderItem.product_id == payload.product_id,
            Order.order_status.in_([OrderStatus.DELIVERED, OrderStatus.PAID, OrderStatus.SHIPPED]),
        )
        .first()
    )
    if not has_completed_order:
        raise HTTPException(status_code=403, detail="You can only review products from a completed order")

    existing = (
        db.query(Review)
        .filter(Review.user_id == current_user.id, Review.product_id == payload.product_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="You have already reviewed this product")

    review = Review(
        user_id=current_user.id,
        product_id=payload.product_id,
        rating=payload.rating,
        comment=payload.comment,
        status=ReviewStatus.APPROVED,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/products/{product_id}/reviews", response_model=ProductReviewsOut)
def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    reviews = (
        db.query(Review)
        .filter(Review.product_id == product_id, Review.status == ReviewStatus.APPROVED)
        .order_by(Review.created_at.desc())
        .all()
    )

    agg = (
        db.query(func.avg(Review.rating), func.count(Review.id))
        .filter(Review.product_id == product_id, Review.status == ReviewStatus.APPROVED)
        .first()
    )
    average_rating = round(float(agg[0]), 2) if agg[0] is not None else 0.0
    total_reviews = agg[1] or 0

    return ProductReviewsOut(average_rating=average_rating, total_reviews=total_reviews, reviews=reviews)
