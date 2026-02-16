"""Authentication and user management models."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .billing import Invoice, Subscription
    from .email import EmailLog, EmailPreference
    from .tenant import Tenant


class User(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255))

    # Multi-tenant support
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    role: Mapped[str | None] = mapped_column(String(50), default="member")  # owner, admin, member

    # User status
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_verified: Mapped[bool] = mapped_column(default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login: Mapped[datetime | None] = mapped_column()

    # Stripe customer ID for billing
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), unique=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")  # type: ignore[assignment]
    api_keys: Mapped[list["APIKey"]] = relationship("APIKey", back_populates="user")  # type: ignore[assignment]
    email_preferences: Mapped["EmailPreference"] = relationship("EmailPreference", back_populates="user", uselist=False)  # type: ignore[assignment]
    email_logs: Mapped[list["EmailLog"]] = relationship("EmailLog", back_populates="user")  # type: ignore[assignment]
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="user", uselist=False)  # type: ignore[assignment]
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="user")  # type: ignore[assignment]


class APIKey(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    key_name: Mapped[str] = mapped_column(String(100))
    key_hash: Mapped[str] = mapped_column(String(255), unique=True)
    key_prefix: Mapped[str] = mapped_column(String(20))  # First few chars for identification

    # Permissions
    scopes: Mapped[dict | None] = mapped_column(JSON)  # ["read", "write", "admin"]

    # Rate limiting
    rate_limit_per_minute: Mapped[int] = mapped_column(default=60)

    # Status
    is_active: Mapped[bool] = mapped_column(default=True)
    expires_at: Mapped[datetime | None] = mapped_column()
    last_used_at: Mapped[datetime | None] = mapped_column()

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")  # type: ignore[assignment]
    user: Mapped["User"] = relationship("User", back_populates="api_keys")  # type: ignore[assignment]
