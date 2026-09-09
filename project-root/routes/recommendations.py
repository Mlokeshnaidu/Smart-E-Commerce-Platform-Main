from collections import Counter
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user, get_optional_user
from models.order import Order, OrderItem
from models.product import Product
from models.product_view import ProductView
from models.review import Review, ReviewStatus
from models.user import User
from schemas.product import ProductOut

router = APIRouter(tags=["recommendations"])


def _get_purchased_product_ids(user_id: int, db: Session) -> set:
    rows = (
        db.query(OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id)
        .all()
    )
    return {r[0] for r in rows}


def _get_viewed_product_ids(user_id: int, db: Session, limit: int = 20) -> list:
    rows = (
        db.query(ProductView.product_id)
        .filter(ProductView.user_id == user_id)
        .order_by(ProductView.viewed_at.desc())
        .limit(limit)
        .all()
    )
    seen = []
    for (pid,) in rows:
        if pid not in seen:
            seen.append(pid)
    return seen


def _get_most_viewed_product_ids(db: Session, limit: int = 10) -> list:
    rows = (
        db.query(ProductView.product_id, func.count(ProductView.id).label("view_count"))
        .group_by(ProductView.product_id)
        .order_by(func.count(ProductView.id).desc())
        .limit(limit)
        .all()
    )
    return [pid for pid, _ in rows]


def _get_top_rated_product_ids(db: Session, limit: int = 10) -> list:
    rows = (
        db.query(Review.product_id, func.avg(Review.rating).label("avg_rating"))
        .filter(Review.status == ReviewStatus.APPROVED)
        .group_by(Review.product_id)
        .order_by(func.avg(Review.rating).desc(), func.count(Review.id).desc())
        .limit(limit)
        .all()
    )
    return [pid for pid, _ in rows]


def _score_similarity(source, candidate):
    score = 50.0
    src_price = float(source.price) if source.price else 0.0
    cand_price = float(candidate.price) if candidate.price else 0.0
    if src_price and cand_price:
        higher = max(src_price, cand_price)
        diff = abs(src_price - cand_price)
        if higher > 0:
            score += max(0.0, 1 - diff / higher) * 30
    score += min(candidate.popularity or 0, 20)
    return score


def _get_similar_product_ids(product_id: int, db: Session, limit: int = 6) -> list:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return []

    candidates = (
        db.query(Product)
        .filter(Product.category == product.category, Product.id != product_id)
        .all()
    )

    scored = [(item.id, _score_similarity(product, item)) for item in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [pid for pid, _ in scored[:limit]]


@router.get("/recommendations/{user_id}", response_model=List[ProductOut])
def get_recommendations(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role.value not in ("admin", "staff"):
        raise HTTPException(status_code=403, detail="You can only view your own recommendations")

    scores = Counter()

    viewed_ids = _get_viewed_product_ids(user_id, db)
    for pid in viewed_ids:
        scores[pid] += 5

    purchased_ids = _get_purchased_product_ids(user_id, db)
    for pid in purchased_ids:
        scores[pid] += 8

    source_ids = list(dict.fromkeys(viewed_ids[:5] + list(purchased_ids)[:5]))
    for pid in source_ids:
        for sim_id in _get_similar_product_ids(pid, db, limit=5):
            scores[sim_id] += 10

    for rank, pid in enumerate(_get_most_viewed_product_ids(db, limit=10)):
        scores[pid] += max(10 - rank, 1)

    for rank, pid in enumerate(_get_top_rated_product_ids(db, limit=10)):
        scores[pid] += max(8 - rank, 1)

    ranked_ids = [pid for pid, _ in scores.most_common() if pid not in purchased_ids]

    if not ranked_ids:
        return db.query(Product).order_by(Product.popularity.desc()).limit(8).all()

    products = db.query(Product).filter(Product.id.in_(ranked_ids)).all()
    product_map = {p.id: p for p in products}
    return [product_map[pid] for pid in ranked_ids if pid in product_map][:8]


@router.get("/products/{product_id}/similar", response_model=List[ProductOut])
def get_similar_products(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if current_user:
        db.add(ProductView(user_id=current_user.id, product_id=product_id))
        db.commit()

    similar_ids = _get_similar_product_ids(product_id, db, limit=6)
    if not similar_ids:
        return []

    products = db.query(Product).filter(Product.id.in_(similar_ids)).all()
    product_map = {p.id: p for p in products}
    return [product_map[pid] for pid in similar_ids if pid in product_map]


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