"""
Reviews & Likes router.

Endpoints:
  GET  /api/reviews/{product_id}          → list reviews for a product
  POST /api/reviews/                      → submit a review (verified purchases only)
  GET  /api/reviews/{product_id}/summary  → avg rating, like count, user state
  POST /api/reviews/{product_id}/like     → toggle like (add or remove)
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.reviews import models, schemas
from app.auth.models import User
from app.auth.deps import get_current_active_user
from app.orders.models import Order, OrderItem
from app.database import get_db

router = APIRouter()


# ── helper: did this user buy this product? ───────────────────────
async def _user_bought_product(db: AsyncSession, user_id: int, product_id: int) -> bool:
    result = await db.execute(
        select(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Order.user_id == user_id,
            OrderItem.product_id == product_id,
            Order.status.in_(["delivered", "paid", "shipped"]),
        )
    )
    return result.scalars().first() is not None


# ── GET /api/reviews/{product_id} ────────────────────────────────
@router.get("/{product_id}", response_model=List[schemas.ReviewResponse])
async def get_reviews(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Review)
        .where(models.Review.product_id == product_id)
        .order_by(models.Review.created_at.desc())
    )
    reviews = result.scalars().all()

    # Add user email to each review response
    out = []
    for r in reviews:
        user_res = await db.execute(select(User).where(User.id == r.user_id))
        user = user_res.scalars().first()
        d = schemas.ReviewResponse.model_validate(r)
        d.user_email = user.email if user else None
        out.append(d)
    return out


# ── GET /api/reviews/{product_id}/summary ────────────────────────
@router.get("/{product_id}/summary", response_model=schemas.ProductRatingSummary)
async def get_summary(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Avg rating + count
    agg = await db.execute(
        select(func.avg(models.Review.rating), func.count(models.Review.id))
        .where(models.Review.product_id == product_id)
    )
    avg_rating, review_count = agg.one()

    # Like count
    like_agg = await db.execute(
        select(func.count(models.Like.id)).where(models.Like.product_id == product_id)
    )
    like_count = like_agg.scalar() or 0

    # Did the current user like it?
    user_like = await db.execute(
        select(models.Like).where(
            models.Like.product_id == product_id,
            models.Like.user_id == current_user.id,
        )
    )
    user_liked = user_like.scalars().first() is not None

    # Did the current user already review it?
    user_rev = await db.execute(
        select(models.Review).where(
            models.Review.product_id == product_id,
            models.Review.user_id == current_user.id,
        )
    )
    user_reviewed = user_rev.scalars().first() is not None

    return schemas.ProductRatingSummary(
        product_id=product_id,
        avg_rating=round(float(avg_rating or 0), 1),
        review_count=review_count or 0,
        like_count=like_count,
        user_liked=user_liked,
        user_reviewed=user_reviewed,
    )


# ── GET /api/reviews/{product_id}/summary (anonymous) ────────────
@router.get("/{product_id}/public-summary")
async def get_public_summary(product_id: int, db: AsyncSession = Depends(get_db)):
    agg = await db.execute(
        select(func.avg(models.Review.rating), func.count(models.Review.id))
        .where(models.Review.product_id == product_id)
    )
    avg_rating, review_count = agg.one()
    like_agg = await db.execute(
        select(func.count(models.Like.id)).where(models.Like.product_id == product_id)
    )
    like_count = like_agg.scalar() or 0
    return {
        "product_id": product_id,
        "avg_rating": round(float(avg_rating or 0), 1),
        "review_count": review_count or 0,
        "like_count": like_count,
    }


# ── POST /api/reviews/ ────────────────────────────────────────────
@router.post("/", response_model=schemas.ReviewResponse, status_code=status.HTTP_201_CREATED)
async def submit_review(
    data: schemas.ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Verified purchase check
    purchased = await _user_bought_product(db, current_user.id, data.product_id)
    if not purchased:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only review products you have purchased and received.",
        )

    # One review per user per product
    existing = await db.execute(
        select(models.Review).where(
            models.Review.product_id == data.product_id,
            models.Review.user_id == current_user.id,
        )
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this product.",
        )

    review = models.Review(
        product_id=data.product_id,
        user_id=current_user.id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    resp = schemas.ReviewResponse.model_validate(review)
    resp.user_email = current_user.email
    return resp


# ── POST /api/reviews/{product_id}/like ──────────────────────────
@router.post("/{product_id}/like")
async def toggle_like(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    existing = await db.execute(
        select(models.Like).where(
            models.Like.product_id == product_id,
            models.Like.user_id == current_user.id,
        )
    )
    like = existing.scalars().first()

    if like:
        await db.delete(like)
        await db.commit()
        liked = False
    else:
        db.add(models.Like(product_id=product_id, user_id=current_user.id))
        await db.commit()
        liked = True

    # Return updated count
    count_res = await db.execute(
        select(func.count(models.Like.id)).where(models.Like.product_id == product_id)
    )
    return {"liked": liked, "like_count": count_res.scalar() or 0}
