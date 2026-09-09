from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.database import Base, engine
from routes import auth, users, products, cart, checkout, notifications, admin, returns, reviews, recommendations

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart E-Commerce Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_STATIC_DIR = Path(__file__).resolve().parent / "static"
_STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(recommendations.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(checkout.router)
app.include_router(notifications.router)
app.include_router(admin.router)
app.include_router(returns.router)
app.include_router(reviews.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}