"""Billing and subscription models."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

if TYPE_CHECKING:
    from .user import User


class Subscription(Base):  # type: ignore[misc,valid-type]
    """User subscription model for billing."""

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    # Stripe IDs
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    stripe_price_id: Mapped[str | None] = mapped_column(String(255))

    # Plan details
    plan_tier: Mapped[str] = mapped_column(String(50))  # free, pro, enterprise
    billing_period: Mapped[str | None] = mapped_column(String(20))  # monthly, yearly

    # Status
    status: Mapped[str | None] = mapped_column(String(50))  # active, cancelled, past_due, trialing, incomplete
    trial_end: Mapped[datetime | None] = mapped_column()
    current_period_start: Mapped[datetime | None] = mapped_column()
    current_period_end: Mapped[datetime | None] = mapped_column()
    cancel_at_period_end: Mapped[bool] = mapped_column(default=False)
    cancelled_at: Mapped[datetime | None] = mapped_column()

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscription")  # type: ignore[assignment]
    usage_records: Mapped[list["UsageRecord"]] = relationship("UsageRecord", back_populates="subscription")  # type: ignore[assignment]


class UsageRecord(Base):  # type: ignore[misc,valid-type]
    """Usage tracking for billing periods."""

    __tablename__ = "usage_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"))

    # Usage metrics
    api_calls: Mapped[int | None] = mapped_column(default=0)
    videos_processed: Mapped[int | None] = mapped_column(default=0)
    matches_performed: Mapped[int | None] = mapped_column(default=0)
    storage_used_mb: Mapped[float | None] = mapped_column(default=0)

    # Billing period
    period_start: Mapped[datetime] = mapped_column()
    period_end: Mapped[datetime] = mapped_column()

    # Stripe
    stripe_usage_record_id: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Relationships
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="usage_records")  # type: ignore[assignment]


class Invoice(Base):  # type: ignore[misc,valid-type]
    """Invoice records from Stripe."""

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    subscription_id: Mapped[int | None] = mapped_column(ForeignKey("subscriptions.id"))

    # Stripe
    stripe_invoice_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255))

    # Details
    amount_due: Mapped[int | None] = mapped_column()  # In cents
    amount_paid: Mapped[int | None] = mapped_column()
    amount_remaining: Mapped[int | None] = mapped_column()
    currency: Mapped[str | None] = mapped_column(String(3), default="usd")

    # Status
    status: Mapped[str | None] = mapped_column(String(50))  # draft, open, paid, void, uncollectible
    paid: Mapped[bool] = mapped_column(default=False)

    # URLs
    invoice_pdf: Mapped[str | None] = mapped_column(String(500))
    hosted_invoice_url: Mapped[str | None] = mapped_column(String(500))

    # Dates
    created: Mapped[datetime | None] = mapped_column()
    due_date: Mapped[datetime | None] = mapped_column()
    paid_at: Mapped[datetime | None] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="invoices")  # type: ignore[assignment]
