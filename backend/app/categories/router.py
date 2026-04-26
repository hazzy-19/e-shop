from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.categories import models, schemas
from app.auth.deps import get_current_admin_user
from app.auth.models import User
from app.database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.CategoryResponse])
async def read_categories(db: AsyncSession = Depends(get_db)):
    # Fetch top-level categories and load subcategories
    result = await db.execute(
        select(models.Category)
        .where(models.Category.parent_id == None, models.Category.is_active == True)
        .options(selectinload(models.Category.subcategories))
    )
    categories = result.scalars().all()
    return categories

@router.post("/", response_model=schemas.CategoryResponse)
async def create_category(
    category: schemas.CategoryCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    db_category = models.Category(**category.model_dump())
    db.add(db_category)
    try:
        await db.commit()
        await db.refresh(db_category)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Category with this name or slug might already exist.")
    return db_category

@router.put("/{category_id}", response_model=schemas.CategoryResponse)
async def update_category(
    category_id: int,
    category: schemas.CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(models.Category).where(models.Category.id == category_id))
    db_category = result.scalars().first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = category.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    
    await db.commit()
    await db.refresh(db_category)
    return db_category

@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(models.Category).where(models.Category.id == category_id))
    db_category = result.scalars().first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db_category.is_active = False
    await db.commit()
    return {"ok": True, "masked": True}
