from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.orders import models, schemas
from app.products.models import Product
from app.auth.models import User
from app.auth.deps import get_current_active_user, get_current_admin_user
from app.database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.OrderResponse)
async def create_order(
    order: schemas.OrderCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    total_amount = 0.0
    order_items_models = []
    
    for item in order.items:
        result = await db.execute(select(Product).where(Product.id == item.product_id))
        product = result.scalars().first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with id {item.product_id} not found")
        if product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for product {product.name}")
        
        product.stock -= item.quantity
        
        total_amount += product.price * item.quantity
        order_items_models.append(
            models.OrderItem(
                product_id=product.id,
                quantity=item.quantity,
                price_at_time=product.price
            )
        )
    
    db_order = models.Order(
        user_id=current_user.id,
        total_amount=total_amount,
        items=order_items_models
    )
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)
    
    result = await db.execute(
        select(models.Order)
        .options(selectinload(models.Order.items).selectinload(models.OrderItem.product))
        .where(models.Order.id == db_order.id)
    )
    final_order = result.scalars().first()
    
    # Send telegram notification dynamically imported from new bot location
    from app.bot.main import send_order_notification
    import asyncio
    asyncio.create_task(send_order_notification(final_order.id, final_order.total_amount))
    
    return final_order

@router.get("/me", response_model=List[schemas.OrderResponse])
async def get_my_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(models.Order)
        .options(selectinload(models.Order.items).selectinload(models.OrderItem.product))
        .where(models.Order.user_id == current_user.id)
    )
    return result.scalars().all()

@router.get("/", response_model=List[schemas.OrderResponse])
async def get_all_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.execute(
        select(models.Order)
        .options(selectinload(models.Order.items).selectinload(models.OrderItem.product))
    )
    return result.scalars().all()
