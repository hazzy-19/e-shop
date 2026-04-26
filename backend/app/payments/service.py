"""
Payment business logic:
  - Safaricom-style transaction ID generation
  - Initiate payment flow
  - Handle Payhero callbacks
  - Get payment status
"""
import random
import string
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.payments.models import Payment
from app.payments.client import initiate_stk_push, check_transaction_status
from app.orders.models import Order

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Transaction ID generator (Safaricom style)
# Format: NDL + 7 random uppercase alphanumeric
# Example: NDL4X7KQ2M, NDLR9B3W5P
# ──────────────────────────────────────────────

TX_PREFIX = "NDL"
TX_RANDOM_LENGTH = 7
TX_CHARS = string.ascii_uppercase + string.digits  # A-Z, 0-9


async def generate_transaction_id(db: AsyncSession) -> str:
    """
    Generate a unique Safaricom-style transaction ID.
    Retries up to 10 times on collision (statistically near-impossible).
    """
    for _ in range(10):
        random_part = "".join(random.choices(TX_CHARS, k=TX_RANDOM_LENGTH))
        tx_id = f"{TX_PREFIX}{random_part}"

        # Check uniqueness
        result = await db.execute(
            select(func.count()).where(Payment.transaction_id == tx_id)
        )
        if result.scalar() == 0:
            return tx_id

    raise Exception("Could not generate a unique transaction ID after 10 attempts")


async def initiate_payment(
    db: AsyncSession,
    user_id: int,
    order_id: int,
    phone_number: str,
) -> Payment:
    """
    Full payment initiation flow:
    1. Validate the order exists and belongs to the user
    2. Generate a unique transaction ID
    3. Create a Payment record
    4. Trigger STK push via Payhero
    5. Update record with Payhero references
    """
    # 1. Validate order
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == user_id)
    )
    order = result.scalars().first()
    if not order:
        raise ValueError(f"Order {order_id} not found or does not belong to this user")

    # Check if there's already a pending/completed payment for this order
    existing = await db.execute(
        select(Payment).where(
            Payment.order_id == order_id,
            Payment.status.in_(["pending", "processing", "completed"]),
        )
    )
    existing_payment = existing.scalars().first()
    if existing_payment:
        if existing_payment.status == "completed":
            raise ValueError("This order has already been paid for")
        # Return the existing pending payment instead of creating a new one
        return existing_payment

    # 2. Generate transaction ID
    tx_id = await generate_transaction_id(db)

    # 3. Create payment record
    payment = Payment(
        transaction_id=tx_id,
        order_id=order_id,
        user_id=user_id,
        phone_number=phone_number,
        amount=order.total_amount,
        status="pending",
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    # 4. Trigger STK push
    try:
        payhero_response = await initiate_stk_push(
            phone_number=phone_number,
            amount=order.total_amount,
            external_reference=tx_id,
        )

        # 5. Update with Payhero references
        payment.payhero_reference = str(payhero_response.get("reference", ""))
        payment.checkout_request_id = str(payhero_response.get("checkout_request_id", ""))
        payment.status = "processing"
        await db.commit()
        await db.refresh(payment)

        logger.info(f"Payment {tx_id} initiated — STK sent to {phone_number}")

    except Exception as e:
        # STK push failed — mark payment as failed
        payment.status = "failed"
        payment.status_detail = str(e)
        await db.commit()
        await db.refresh(payment)
        logger.error(f"Payment {tx_id} STK push failed: {e}")
        raise

    return payment


async def handle_callback(db: AsyncSession, payload: dict) -> Payment | None:
    """
    Process a Payhero callback (server-to-server notification).
    Updates the payment status based on the callback data.
    """
    external_ref = payload.get("ExternalReference") or payload.get("external_reference")
    if not external_ref:
        logger.warning(f"Callback received without ExternalReference: {payload}")
        return None

    result = await db.execute(
        select(Payment).where(Payment.transaction_id == external_ref)
    )
    payment = result.scalars().first()
    if not payment:
        logger.warning(f"Callback for unknown transaction: {external_ref}")
        return None

    # Determine status from callback
    result_code = payload.get("ResultCode")
    status_str = payload.get("Status", "").lower()
    mpesa_receipt = payload.get("MpesaReceiptNumber")

    if result_code == 0 or status_str == "success":
        payment.status = "completed"
        payment.confirmed_at = datetime.now(timezone.utc)
        if mpesa_receipt:
            payment.payhero_reference = mpesa_receipt
        # Update the order status too
        order_result = await db.execute(
            select(Order).where(Order.id == payment.order_id)
        )
        order = order_result.scalars().first()
        if order:
            order.status = "paid"
    else:
        payment.status = "failed"

    payment.status_detail = payload.get("ResultDesc", str(payload))
    await db.commit()
    await db.refresh(payment)

    logger.info(f"Callback processed: {external_ref} → {payment.status}")
    return payment


async def get_payment_status(db: AsyncSession, transaction_id: str) -> Payment | None:
    """Get the current payment status from our database."""
    result = await db.execute(
        select(Payment).where(Payment.transaction_id == transaction_id)
    )
    return result.scalars().first()


async def refresh_payment_from_payhero(db: AsyncSession, transaction_id: str) -> Payment | None:
    """
    Poll Payhero API for the latest status and update our database.
    Useful when the callback hasn't arrived yet.
    """
    payment = await get_payment_status(db, transaction_id)
    if not payment:
        return None

    # Don't poll if already finalized
    if payment.status in ("completed", "cancelled"):
        return payment

    try:
        payhero_data = await check_transaction_status(transaction_id)
        status_str = str(payhero_data.get("status", "")).lower()

        if status_str in ("success", "completed"):
            payment.status = "completed"
            payment.confirmed_at = datetime.now(timezone.utc)
            mpesa_receipt = payhero_data.get("mpesa_receipt_number")
            if mpesa_receipt:
                payment.payhero_reference = mpesa_receipt
            # Update order
            order_result = await db.execute(
                select(Order).where(Order.id == payment.order_id)
            )
            order = order_result.scalars().first()
            if order:
                order.status = "paid"
        elif status_str in ("failed", "cancelled"):
            payment.status = "failed"

        payment.status_detail = str(payhero_data.get("result_description", ""))
        await db.commit()
        await db.refresh(payment)

    except Exception as e:
        logger.warning(f"Could not refresh status from Payhero for {transaction_id}: {e}")

    return payment
