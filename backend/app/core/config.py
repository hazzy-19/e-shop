from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "E-shop API"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # Database — defaults to SQLite for local dev if not set
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"

    # Telegram Bot — optional, app still boots without them
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_ADMIN_ID: int = 0

    # M-Pesa — all optional
    MPESA_CONSUMER_KEY: Optional[str] = None
    MPESA_CONSUMER_SECRET: Optional[str] = None
    MPESA_PASSKEY: Optional[str] = None
    MPESA_BUSINESS_SHORTCODE: Optional[str] = None
    MPESA_ENVIRONMENT: str = "sandbox"

    # Payhero Payment Gateway
    PAYHERO_API_USERNAME: Optional[str] = None
    PAYHERO_API_PASSWORD: Optional[str] = None
    PAYHERO_CHANNEL_ID: Optional[str] = None
    PAYHERO_CALLBACK_URL: str = "http://localhost:8000/api/payments/callback"

    # Termii Email (review prompts) — paste key when ready
    TERMII_API_KEY: Optional[str] = None
    TERMII_EMAIL_CONFIG_ID: Optional[str] = None

    # Frontend URL (used in email links)
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
