"""Base classes, mixins, and enums for database models."""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import CheckConstraint, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamp fields."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class JobStatus(str, Enum):
    """Processing job status values."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WebhookStatus(str, Enum):
    """Webhook status values."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"


class WebhookEventStatus(str, Enum):
    """Webhook event processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class WebhookDeliveryStatus(str, Enum):
    """Webhook delivery status values."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class EmailStatus(str, Enum):
    """Email sending status values."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"
    COMPLAINED = "complained"


class SubscriptionStatus(str, Enum):
    """Subscription status values."""

    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"


class InvoiceStatus(str, Enum):
    """Invoice status values."""

    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


class MarketplaceItemStatus(str, Enum):
    """Marketplace item status values."""

    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    SUSPENDED = "suspended"


class TransactionStatus(str, Enum):
    """Transaction status values."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


def add_status_constraint(table_name: str, column_name: str, allowed_values: list[str]) -> CheckConstraint:
    """Helper to create CHECK constraint for status columns.
    
    Args:
        table_name: Name of the table
        column_name: Name of the status column
        allowed_values: List of allowed status values
        
    Returns:
        CheckConstraint object
    """
    constraint_name = f"ck_{table_name}_{column_name}"
    values_str = ", ".join(f"'{v}'" for v in allowed_values)
    return CheckConstraint(
        f"{column_name} IN ({values_str})",
        name=constraint_name,
    )
