from pathlib import Path
from pydantic_settings import BaseSettings

_BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str = f"sqlite:///{_BASE_DIR}/ecommerce.db"

    JWT_SECRET_KEY: str = "change_this_secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    AUTH0_DOMAIN: str = "your-tenant.auth0.com"
    AUTH0_CLIENT_ID: str = ""
    AUTH0_CLIENT_SECRET: str = ""
    AUTH0_AUDIENCE: str = ""

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_SUCCESS_URL: str = "http://localhost:3000/checkout/success"
    STRIPE_CANCEL_URL: str = "http://localhost:3000/checkout/cancel"

    SMTP_HOST: str = "smtp.sendgrid.net"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "no-reply@ecommerce.com"

    class Config:
        env_file = (_BASE_DIR / ".env", _BASE_DIR.parent / ".env", ".env")
        extra = "ignore"  # tolerate unrelated vars in the shared .env (e.g. DJANGO_*)


settings = Settings()