"""
Pydantic schemas for the Payhero payments module.
"""
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
import re


class PaymentInitiateRequest(BaseModel):
    """Customer initiates an M-Pesa payment."""
    order_id: int
    phone_number: str  # e.g. "0712345678" or "254712345678"

    @field_validator("phone_number")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        """Normalize Kenyan phone numbers to 2547XXXXXXXX format."""
        v = re.sub(r"[\s\-\+]", "", v)  # strip spaces, dashes, plus
        if v.startswith("0") and len(v) == 10:
            return "254" + v[1:]
        if v.startswith("254") and len(v) == 12:
            return v
        if v.startswith("7") and len(v) == 9:
            return "254" + v
        raise ValueError("Invalid Kenyan phone number. Use 07XXXXXXXX or 2547XXXXXXXX format.")


class PaymentInitiateResponse(BaseModel):
    """Returned after STK push is triggered."""
    transaction_id: str
    status: str
    message: str


class PaymentStatusResponse(BaseModel):
    """Returned when polling payment status."""
    transaction_id: str
    order_id: int
    amount: float
    phone_number: str
    status: str
    status_detail: Optional[str] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PayheroCallbackPayload(BaseModel):
    """
    Payload sent by Payhero to our callback URL.
    Fields may vary — we accept extras gracefully.
    """
    Amount: Optional[float] = None
    CheckoutRequestID: Optional[str] = None
    ExternalReference: Optional[str] = None
    MpesaReceiptNumber: Optional[str] = None
    Phone: Optional[str] = None
    ResultCode: Optional[int] = None
    ResultDesc: Optional[str] = None
    Status: Optional[str] = None

    class Config:
        extra = "allow"  # Payhero may send additional fields
