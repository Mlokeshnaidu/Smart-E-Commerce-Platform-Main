import os
import sys
from pathlib import Path

# Add project-root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.database import Base, engine, SessionLocal
from core.security import hash_password
from models.user import User, UserRole
from models.product import Product
from models.cart import Cart, CartItem
from models.order import Order, OrderItem, OrderStatus, PaymentStatus
from models.payment import Payment, PaymentTransactionStatus
from models.notification import Notification

def seed():
    print("🌱 Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("🌱 Seeding Users...")
        users_data = [
            {"name": "Admin User", "email": "admin@example.com", "password": "Password123!", "role": UserRole.ADMIN},
            {"name": "Staff Manager", "email": "staff@example.com", "password": "Password123!", "role": UserRole.STAFF},
            {"name": "Alice Customer", "email": "customer@example.com", "password": "Password123!", "role": UserRole.CUSTOMER},
            {"name": "John Doe", "email": "john.doe@example.com", "password": "Password123!", "role": UserRole.CUSTOMER},
            {"name": "Jane Smith", "email": "jane.smith@example.com", "password": "Password123!", "role": UserRole.CUSTOMER},
        ]

        user_map = {}
        for u in users_data:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                user = User(
                    name=u["name"],
                    email=u["email"],
                    password=hash_password(u["password"]),
                    role=u["role"],
                    is_active=True,
                )
                db.add(user)
                db.flush()
                user_map[u["email"]] = user
            else:
                existing.role = u["role"]
                existing.password = hash_password(u["password"])
                user_map[u["email"]] = existing

        print("🌱 Seeding Products Catalog...")
        products_data = [
            {
                "name": "Sony WH-1000XM5 Wireless Headphones",
                "description": "Industry-leading noise canceling wireless headphones with auto NC optimizer and crystal clear hands-free calling.",
                "category": "Electronics",
                "price": 349.99,
                "stock": 25,
                "popularity": 95,
                "images": ["https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop"],
            },
            {
                "name": "Apple MacBook Air 15-inch M3",
                "description": "Supercharged by M3 chip, Liquid Retina display, 18 hours of battery life, and ultra-thin aluminum enclosure.",
                "category": "Electronics",
                "price": 1299.00,
                "stock": 14,
                "popularity": 98,
                "images": ["https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&auto=format&fit=crop"],
            },
            {
                "name": "Logitech MX Master 3S Wireless Mouse",
                "description": "Quiet clicks, 8K DPI any-surface tracking, and ultra-fast MagSpeed scrolling for ultimate productivity.",
                "category": "Accessories",
                "price": 99.99,
                "stock": 40,
                "popularity": 88,
                "images": ["https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=600&auto=format&fit=crop"],
            },
            {
                "name": "RGB Mechanical Gaming Keyboard",
                "description": "Custom hot-swappable tactile switches with customizable per-key RGB backlighting and aluminum top frame.",
                "category": "Accessories",
                "price": 119.50,
                "stock": 18,
                "popularity": 76,
                "images": ["https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600&auto=format&fit=crop"],
            },
            {
                "name": "Minimalist Leather Commuter Backpack",
                "description": "Handcrafted top-grain leather with padded laptop sleeve, water-resistant zippers, and sleek modern silhouette.",
                "category": "Apparel",
                "price": 89.00,
                "stock": 4,  # Low Stock Alert
                "popularity": 62,
                "images": ["https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop"],
            },
            {
                "name": "Smart LED Desk Lamp Pro",
                "description": "Adjustable color temperature, ambient light auto-sensor, wireless charging base, and voice assistant integration.",
                "category": "Home",
                "price": 49.99,
                "stock": 2,  # Critical Stock Alert
                "popularity": 54,
                "images": ["https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=600&auto=format&fit=crop"],
            },
            {
                "name": "Ergonomic Mesh Office Chair",
                "description": "High-back breathable mesh chair with dynamic lumbar support, 3D armrests, and synchro-tilt mechanism.",
                "category": "Home",
                "price": 289.00,
                "stock": 7,  # Low Stock Alert
                "popularity": 82,
                "images": ["https://images.unsplash.com/photo-1580481077197-2a4c6a51d9eb?w=600&auto=format&fit=crop"],
            },
            {
                "name": "Organic Heavyweight Cotton Hoodie",
                "description": "100% GOTS-certified organic cotton with double-lined hood and reinforced stitching for supreme comfort.",
                "category": "Apparel",
                "price": 59.99,
                "stock": 35,
                "popularity": 65,
                "images": ["https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=600&auto=format&fit=crop"],
            },
        ]

        prod_map = {}
        for p in products_data:
            existing = db.query(Product).filter(Product.name == p["name"]).first()
            if not existing:
                prod = Product(**p)
                db.add(prod)
                db.flush()
                prod_map[p["name"]] = prod
            else:
                prod_map[p["name"]] = existing

        print("🌱 Seeding Carts...")
        cust1 = user_map["customer@example.com"]
        cart1 = db.query(Cart).filter(Cart.user_id == cust1.id).first()
        if not cart1:
            cart1 = Cart(user_id=cust1.id)
            db.add(cart1)
            db.flush()

        # Add cart item if empty
        if not cart1.items and "Sony WH-1000XM5 Wireless Headphones" in prod_map:
            p = prod_map["Sony WH-1000XM5 Wireless Headphones"]
            db.add(CartItem(cart_id=cart1.id, product_id=p.id, quantity=1))

        print("🌱 Seeding Orders & Payments...")
        if db.query(Order).count() == 0:
            sample_orders = [
                {
                    "user": user_map["customer@example.com"],
                    "total": 349.99,
                    "order_status": OrderStatus.DELIVERED,
                    "payment_status": PaymentStatus.PAID,
                    "items": [(prod_map["Sony WH-1000XM5 Wireless Headphones"], 1, 349.99)],
                },
                {
                    "user": user_map["john.doe@example.com"],
                    "total": 1398.99,
                    "order_status": OrderStatus.SHIPPED,
                    "payment_status": PaymentStatus.PAID,
                    "items": [
                        (prod_map["Apple MacBook Air 15-inch M3"], 1, 1299.00),
                        (prod_map["Logitech MX Master 3S Wireless Mouse"], 1, 99.99),
                    ],
                },
                {
                    "user": user_map["jane.smith@example.com"],
                    "total": 239.00,
                    "order_status": OrderStatus.PAID,
                    "payment_status": PaymentStatus.PAID,
                    "items": [
                        (prod_map["RGB Mechanical Gaming Keyboard"], 2, 119.50),
                    ],
                },
                {
                    "user": user_map["customer@example.com"],
                    "total": 138.99,
                    "order_status": OrderStatus.PENDING,
                    "payment_status": PaymentStatus.UNPAID,
                    "items": [
                        (prod_map["Minimalist Leather Commuter Backpack"], 1, 89.00),
                        (prod_map["Smart LED Desk Lamp Pro"], 1, 49.99),
                    ],
                },
            ]

            for o_data in sample_orders:
                order = Order(
                    user_id=o_data["user"].id,
                    total=o_data["total"],
                    order_status=o_data["order_status"],
                    payment_status=o_data["payment_status"],
                )
                db.add(order)
                db.flush()

                for prod_obj, qty, pr in o_data["items"]:
                    db.add(OrderItem(order_id=order.id, product_id=prod_obj.id, quantity=qty, price=pr))

                payment = Payment(
                    order_id=order.id,
                    amount=order.total,
                    payment_method="stripe",
                    transaction_id=f"pi_seed_{order.id}_{order.user_id}",
                    status=PaymentTransactionStatus.SUCCEEDED if order.payment_status == PaymentStatus.PAID else PaymentTransactionStatus.PENDING,
                )
                db.add(payment)

                db.add(Notification(
                    user_id=order.user_id,
                    type="order_confirmed",
                    message=f"Order #{order.id} placed successfully for ${order.total:.2f}",
                    read_status=False,
                ))

        db.commit()
        print("✅ Database successfully seeded with demo users, catalog products, orders, payments, and notifications!")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed()
