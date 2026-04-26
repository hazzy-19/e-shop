"""
Review prompt email scheduler.

Runs every hour as a background asyncio task.
Finds orders that were delivered 3+ days ago and haven't had a review prompt sent.
Sends an email to the customer for each product in that order.

Email channel: Termii (https://termii.com)
Set TERMII_API_KEY in .env to activate. If blank, logs the would-be email.
"""
import asyncio
import logging
import httpx
from datetime import datetime, timezone, timedelta
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import async_session
from app.orders.models import Order, OrderItem
from app.auth.models import User
from app.products.models import Product
from app.core.config import settings

logger = logging.getLogger(__name__)

REVIEW_DELAY_DAYS = 3
CHECK_INTERVAL_SECONDS = 3600  # run every hour


async def _send_review_email(to_email: str, product_name: str, product_id: int):
    """Send a review request email via Termii or log if not configured."""
    subject = f"How was your {product_name}? Leave a review!"
    review_url = f"{settings.FRONTEND_URL}/product/{product_id}#reviews"
    body = (
        f"Hi there!\n\n"
        f"We hope you're enjoying your {product_name}.\n"
        f"Could you take a moment to leave a review? It helps other shoppers.\n\n"
        f"Review here: {review_url}\n\n"
        f"Thank you for shopping with us!\n"
        f"— The eshop team"
    )

    if not settings.TERMII_API_KEY:
        logger.info(
            f"[REVIEW EMAIL - no Termii key] To: {to_email} | "
            f"Subject: {subject} | Product: {product_name}"
        )
        return

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.ng.termii.com/api/email/otp/send",
                json={
                    "api_key": settings.TERMII_API_KEY,
                    "email_address": to_email,
                    "code": subject,
                    "email_configuration_id": settings.TERMII_EMAIL_CONFIG_ID or "",
                },
            )
            if resp.status_code == 200:
                logger.info(f"Review email sent to {to_email} for product {product_name}")
            else:
                logger.warning(f"Termii returned {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Failed to send review email to {to_email}: {e}")


async def _check_and_send_prompts():
    """Find orders delivered 3+ days ago with no review prompt sent."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=REVIEW_DELAY_DAYS)
    async with async_session() as db:
        result = await db.execute(
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.owner),
            )
            .where(
                Order.status == "delivered",
                Order.delivered_at <= cutoff,
                Order.review_prompt_sent == False,  # noqa: E712
            )
        )
        orders = result.scalars().all()

        for order in orders:
            user: User = order.owner
            if not user or not user.email:
                continue
            for item in order.items:
                product: Product = item.product
                if not product:
                    continue
                await _send_review_email(user.email, product.name, product.id)

            order.review_prompt_sent = True

        if orders:
            await db.commit()
            logger.info(f"Review prompts sent for {len(orders)} order(s).")


async def run_scheduler():
    """Long-running background task — runs forever, checks every hour."""
    logger.info("Review prompt scheduler started.")
    while True:
        try:
            await _check_and_send_prompts()
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
