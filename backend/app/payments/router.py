"""
Payment API router.
Endpoints:
  POST /api/payments/initiate — Initiate M-Pesa STK Push
  POST /api/payments/callback — Receive Payhero confirmation (no auth)
  GET  /api/payments/status/{transaction_id} — Poll payment status
  GET  /api/payments/my — List all payments for current user
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.auth.deps import get_current_active_user
from app.auth.models import User
from app.payments import schemas
from app.payments.models import Payment
from app.payments.service import (
    initiate_payment,
    handle_callback,
    get_payment_status,
    refresh_payment_from_payhero,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ──────────────────────── Initiate Payment ────────────────────────

@router.post("/initiate", response_model=schemas.PaymentInitiateResponse)
async def initiate_payment_endpoint(
    body: schemas.PaymentInitiateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Initiate an M-Pesa STK Push for an order.
    The customer will receive a prompt on their phone.
    """
    try:
        payment = await initiate_payment(
            db=db,
            user_id=current_user.id,
            order_id=body.order_id,
            phone_number=body.phone_number,
        )
        return schemas.PaymentInitiateResponse(
            transaction_id=payment.transaction_id,
            status=payment.status,
            message="STK Push sent. Please check your phone and enter your M-Pesa PIN.",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Payment initiation failed: {e}")
        raise HTTPException(
            status_code=502,
            detail="Failed to initiate payment. Please try again.",
        )


# ──────────────────────── Payhero Callback ────────────────────────

@router.post("/callback")
async def payhero_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Webhook endpoint for Payhero.
    No authentication — Payhero's server calls this directly.
    """
    try:
        payload = await request.json()
        logger.info(f"Payhero callback received: {payload}")
        payment = await handle_callback(db, payload)
        if payment:
            return {"status": "ok", "transaction_id": payment.transaction_id}
        return {"status": "ignored", "message": "No matching transaction found"}
    except Exception as e:
        logger.error(f"Callback processing error: {e}")
        return {"status": "error", "message": str(e)}


# ──────────────────────── Payment Status ────────────────────────

@router.get("/status/{transaction_id}", response_model=schemas.PaymentStatusResponse)
async def payment_status_endpoint(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Poll the status of a payment.
    If the payment is still pending/processing, also checks Payhero API.
    """
    # First try to refresh from Payhero if not finalized
    payment = await refresh_payment_from_payhero(db, transaction_id)

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Security: only the owner or admin can check
    if payment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to view this payment")

    return schemas.PaymentStatusResponse(
        transaction_id=payment.transaction_id,
        order_id=payment.order_id,
        amount=payment.amount,
        phone_number=payment.phone_number,
        status=payment.status,
        status_detail=payment.status_detail,
        created_at=payment.created_at,
        confirmed_at=payment.confirmed_at,
    )


# ──────────────────────── My Payments ────────────────────────

@router.get("/my", response_model=List[schemas.PaymentStatusResponse])
async def my_payments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all payments for the currently logged-in user."""
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
    )
    payments = result.scalars().all()
    return [
        schemas.PaymentStatusResponse(
            transaction_id=p.transaction_id,
            order_id=p.order_id,
            amount=p.amount,
            phone_number=p.phone_number,
            status=p.status,
            status_detail=p.status_detail,
            created_at=p.created_at,
            confirmed_at=p.confirmed_at,
        )
        for p in payments
    ]
