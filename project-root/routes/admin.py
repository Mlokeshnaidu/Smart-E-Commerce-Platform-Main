from sqlalchemy import func
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.rbac import require_roles
from models.order import Order, OrderItem, OrderStatus
from models.product import Product
from models.user import User, UserRole

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/analytics/overview")
def analytics_overview(db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))):
    total_orders = db.query(func.count(Order.id)).scalar()
    total_revenue = db.query(func.coalesce(func.sum(Order.total), 0)).filter(Order.order_status != OrderStatus.CANCELLED).scalar()
    total_products = db.query(func.count(Product.id)).scalar()
    total_customers = db.query(func.count(User.id)).filter(User.role == UserRole.CUSTOMER).scalar()
    return {
        "total_orders": total_orders,
        "total_revenue": round(float(total_revenue), 2),
        "total_products": total_products,
        "total_customers": total_customers,
    }


@router.get("/analytics/top-products")
def top_products(db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))):
    results = (
        db.query(Product.id, Product.name, func.sum(OrderItem.quantity).label("units_sold"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.id, Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(10)
        .all()
    )
    return [{"product_id": r.id, "name": r.name, "units_sold": int(r.units_sold)} for r in results]


@router.get("/analytics/orders-by-status")
def orders_by_status(db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))):
    results = db.query(Order.order_status, func.count(Order.id)).group_by(Order.order_status).all()
    return {status.value: count for status, count in results}
