"""
Async HTTP client for the Payhero API.
Handles Basic Auth, STK Push initiation, and transaction status checks.
"""
import base64
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

PAYHERO_BASE_URL = "https://backend.payhero.co.ke/api/v2"


def _get_auth_header() -> str:
    """Build the Basic Auth header from settings."""
    username = settings.PAYHERO_API_USERNAME or ""
    password = settings.PAYHERO_API_PASSWORD or ""
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


async def initiate_stk_push(
    phone_number: str,
    amount: float,
    external_reference: str,
    callback_url: str | None = None,
) -> dict:
    """
    Trigger an M-Pesa STK Push via Payhero.
    
    Args:
        phone_number: Customer phone in 2547XXXXXXXX format
        amount: Amount in KES
        external_reference: Our transaction ID (e.g. NDL4X7KQ2M)
        callback_url: Override callback URL (defaults to settings)
    
    Returns:
        Payhero API response dict
    """
    url = f"{PAYHERO_BASE_URL}/payments"
    headers = {
        "Authorization": _get_auth_header(),
        "Content-Type": "application/json",
    }
    payload = {
        "amount": amount,
        "phone_number": phone_number,
        "channel_id": int(settings.PAYHERO_CHANNEL_ID) if settings.PAYHERO_CHANNEL_ID else 0,
        "provider": "m-pesa",
        "external_reference": external_reference,
        "callback_url": callback_url or settings.PAYHERO_CALLBACK_URL,
    }

    logger.info(f"Initiating STK Push: {external_reference} → {phone_number} for KES {amount}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)

    data = response.json()

    if response.status_code not in (200, 201):
        logger.error(f"Payhero STK Push failed: {response.status_code} — {data}")
        raise Exception(f"Payhero API error: {data.get('message', response.text)}")

    logger.info(f"STK Push initiated successfully: {data}")
    return data


async def check_transaction_status(external_reference: str) -> dict:
    """
    Check the status of a transaction via Payhero API.
    
    Args:
        external_reference: Our transaction ID
    
    Returns:
        Payhero status response dict
    """
    url = f"{PAYHERO_BASE_URL}/transactions/status/{external_reference}"
    headers = {
        "Authorization": _get_auth_header(),
    }

    logger.info(f"Checking transaction status: {external_reference}")

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, headers=headers)

    data = response.json()

    if response.status_code != 200:
        logger.error(f"Payhero status check failed: {response.status_code} — {data}")
        raise Exception(f"Payhero API error: {data.get('message', response.text)}")

    return data
