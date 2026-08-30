from pydantic import BaseModel

from schemas.product import ProductOut


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    product_id: int
    quantity: int


class CartItemOut(BaseModel):
    id: int
    product: ProductOut
    quantity: int
    item_total: float

    class Config:
        from_attributes = True


class CartOut(BaseModel):
    id: int
    items: list[CartItemOut]
    cart_total: float
    tax: float
    grand_total: float