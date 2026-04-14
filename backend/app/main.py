import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.database import engine, Base

# Import all models to ensure they are registered with Base.metadata BEFORE create_all
from app.auth import models as auth_models
from app.products import models as product_models
from app.orders import models as order_models

# Routers
from app.auth.router import router as auth_router
from app.categories.router import router as categories_router
from app.products.router import router as products_router
from app.orders.router import router as orders_router

from app.bot.main import start_bot, stop_bot
from app.core.firebase import initialize_firebase

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_firebase()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await start_bot()
    yield
    await stop_bot()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(categories_router, prefix="/api/categories", tags=["categories"])
app.include_router(products_router, prefix="/api/products", tags=["products"])
app.include_router(orders_router, prefix="/api/orders", tags=["orders"])

# Serve locally uploaded product images (from bot photo uploads)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "images")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static/images", StaticFiles(directory=STATIC_DIR), name="static_images")

@app.get("/")
def read_root():
    return {"message": "Welcome to E-shop API"}
