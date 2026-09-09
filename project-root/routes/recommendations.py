from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from models.order import Order, OrderItem
from models.product import Product
from models.review import Review, ReviewStatus
from models.product_view import ProductView
from core.deps import get_optional_user
from models.user import User
from schemas.product import ProductOut

router = APIRouter(tags=["recommendations"])


@router.get("/recommendations/{user_id}", response_model=List[ProductOut])
def get_recommendations(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role.value not in ("admin", "staff"):
        raise HTTPException(status_code=403, detail="You can only view your own recommendations")

    purchased_product_ids = {
        row[0]
        for row in (
            db.query(OrderItem.product_id)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.user_id == user_id)
            .all()
        )
    }

    viewed_category_ids = {
        row[0]
        for row in (
            db.query(Product.category)
            .join(ProductView, ProductView.product_id == Product.id)
            .filter(ProductView.user_id == user_id)
            .distinct()
            .all()
        )
    }

    purchased_categories = set()
    if purchased_product_ids:
        purchased_categories = {
            row[0]
            for row in (
                db.query(Product.category)
                .filter(Product.id.in_(purchased_product_ids))
                .distinct()
                .all()
            )
        }

    query = db.query(Product)
    if purchased_product_ids:
        query = query.filter(~Product.id.in_(purchased_product_ids))

    purchased_categories = purchased_categories | viewed_category_ids

    if purchased_categories:
        recs = (
            query.filter(Product.category.in_(purchased_categories))
            .order_by(Product.popularity.desc())
            .limit(8)
            .all()
        )
        if len(recs) >= 4:
            return recs

    fallback = query.order_by(Product.popularity.desc()).limit(8).all()
    if fallback:
        return fallback

    return db.query(Product).order_by(Product.popularity.desc()).limit(8).all()


@router.get("/products/{product_id}/similar", response_model=List[ProductOut])
def get_similar_products(product_id: int, db: Session = Depends(get_db), current_user=Depends(get_optional_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if current_user:
        db.add(ProductView(user_id=current_user.id, product_id=product_id))
        db.commit()

    similar = (
        db.query(Product)
        .filter(Product.category == product.category, Product.id != product_id)
        .order_by(Product.popularity.desc())
        .limit(6)
        .all()
    )
    return similar


@router.get("/products/trending", response_model=List[ProductOut])
def get_trending_products(db: Session = Depends(get_db)):
    trending = (
        db.query(Product, func.count(OrderItem.id).label("order_count"), func.avg(Review.rating).label("avg_rating"))
        .outerjoin(OrderItem, OrderItem.product_id == Product.id)
        .outerjoin(Review, (Review.product_id == Product.id) & (Review.status == ReviewStatus.APPROVED))
        .group_by(Product.id)
        .order_by(func.count(OrderItem.id).desc(), func.avg(Review.rating).desc(), Product.popularity.desc())
        .limit(8)
        .all()
    )
    return [p for p, _, _ in trending]
