"""
Payment model — stored in the same database as orders and users.
Tracks M-Pesa STK Push transactions via Payhero.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    # Safaricom-style transaction ID (e.g. NDL4X7KQ2M)
    transaction_id = Column(String(10), unique=True, index=True, nullable=False)

    # Links to existing tables
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Payment details
    phone_number = Column(String(15), nullable=False)
    amount = Column(Float, nullable=False)

    # Payhero / M-Pesa references (filled after STK push response)
    payhero_reference = Column(String, nullable=True)
    checkout_request_id = Column(String, nullable=True)

    # Status tracking
    status = Column(String, default="pending")  # pending, processing, completed, failed, cancelled
    status_detail = Column(String, nullable=True)  # raw detail from Payhero

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    confirmed_at = Column(DateTime, nullable=True)

    # Relationships
    order = relationship("Order", backref="payment")
    user = relationship("User", back_populates="payments")
