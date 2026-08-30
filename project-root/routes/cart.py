from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from models.cart import Cart, CartItem
from models.product import Product
from models.user import User
from schemas.cart import CartItemCreate, CartItemUpdate, CartOut, CartItemOut
from utils.websocket_manager import manager

router = APIRouter(prefix="/cart", tags=["cart"])

TAX_RATE = 0.08


def _get_or_create_cart(db: Session, user: User) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def _build_cart_out(cart: Cart) -> CartOut:
    items = []
    cart_total = 0.0
    for item in cart.items:
        item_total = item.product.price * item.quantity
        cart_total += item_total
        items.append(CartItemOut(id=item.id, product=item.product, quantity=item.quantity, item_total=item_total))
    tax = round(cart_total * TAX_RATE, 2)
    return CartOut(id=cart.id, items=items, cart_total=round(cart_total, 2), tax=tax, grand_total=round(cart_total + tax, 2))


@router.get("/", response_model=CartOut)
def view_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart = _get_or_create_cart(db, current_user)
    return _build_cart_out(cart)


async def _notify_cart_updated(user_id: int, cart_out: CartOut) -> None:
    try:
        await manager.send_to_user(user_id, "cart_updated", cart_out.model_dump(mode="json"))
    except Exception:
        pass


@router.post("/add", response_model=CartOut)
async def add_to_cart(payload: CartItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    cart = _get_or_create_cart(db, current_user)
    item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == payload.product_id).first()
    new_quantity = (item.quantity if item else 0) + payload.quantity
    if new_quantity > product.stock:
        raise HTTPException(status_code=400, detail=f"Only {product.stock} in stock")

    if item:
        item.quantity = new_quantity
    else:
        item = CartItem(cart_id=cart.id, product_id=payload.product_id, quantity=payload.quantity)
        db.add(item)
    db.commit()
    db.refresh(cart)
    cart_out = _build_cart_out(cart)
    await _notify_cart_updated(current_user.id, cart_out)
    return cart_out


@router.put("/update", response_model=CartOut)
async def update_cart_item(payload: CartItemUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart = _get_or_create_cart(db, current_user)
    item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == payload.product_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not in cart")
    if payload.quantity <= 0:
        db.delete(item)
    else:
        if payload.quantity > item.product.stock:
            raise HTTPException(status_code=400, detail=f"Only {item.product.stock} in stock")
        item.quantity = payload.quantity
    db.commit()
    db.refresh(cart)
    cart_out = _build_cart_out(cart)
    await _notify_cart_updated(current_user.id, cart_out)
    return cart_out


@router.delete("/remove", response_model=CartOut)
async def remove_from_cart(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart = _get_or_create_cart(db, current_user)
    item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == product_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not in cart")
    db.delete(item)
    db.commit()
    db.refresh(cart)
    cart_out = _build_cart_out(cart)
    await _notify_cart_updated(current_user.id, cart_out)
    return cart_out