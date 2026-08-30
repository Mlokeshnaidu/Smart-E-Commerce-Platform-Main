import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from core.database import get_db
from core.rbac import require_roles
from models.product import Product
from models.user import User, UserRole
from schemas.product import ProductCreate, ProductUpdate, ProductOut

router = APIRouter(prefix="/products", tags=["products"])

_UPLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "uploads" / "products"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/", response_model=list[ProductOut])
def list_products(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
    sort_by_popularity: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if in_stock is True:
        query = query.filter(Product.stock > 0)
    if in_stock is False:
        query = query.filter(Product.stock == 0)
    if sort_by_popularity:
        query = query.order_by(Product.popularity.desc())
    return query.all()


@router.get("/category/{category}", response_model=list[ProductOut])
def get_by_category(category: str, db: Session = Depends(get_db)):
    return db.query(Product).filter(Product.category == category).all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN))):
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN))):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN))):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()


@router.post("/{product_id}/images", response_model=ProductOut, status_code=201)
async def upload_product_images(
    product_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    saved_urls = []
    for upload in files:
        filename = f"{uuid.uuid4().hex}_{upload.filename}"
        with open(_UPLOAD_DIR / filename, "wb") as f:
            f.write(await upload.read())
        saved_urls.append(f"/static/uploads/products/{filename}")
    product.images = list(product.images or []) + saved_urls
    db.commit()
    db.refresh(product)
    return product