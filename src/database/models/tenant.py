"""Tenant and multi-tenancy models."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .auth import APIKey, User
    from .fingerprint import AudioFingerprint
    from .video import Channel, Video


class Tenant(Base):  # type: ignore[misc,valid-type]
    """Multi-tenant support for enterprise customers."""

    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True)  # URL-safe identifier

    # Contact
    admin_email: Mapped[str] = mapped_column(String(255))
    admin_name: Mapped[str | None] = mapped_column(String(255))

    # Branding
    logo_url: Mapped[str | None] = mapped_column(String(500))
    primary_color: Mapped[str | None] = mapped_column(String(7))  # Hex color
    custom_domain: Mapped[str | None] = mapped_column(String(255), unique=True)

    # Status
    is_active: Mapped[bool] = mapped_column(default=True)
    plan_tier: Mapped[str | None] = mapped_column(String(50))  # Links to subscription plan

    # Limits (can override plan defaults)
    max_users: Mapped[int | None] = mapped_column()
    max_api_calls_per_month: Mapped[int | None] = mapped_column()
    max_storage_gb: Mapped[int | None] = mapped_column()

    # Metadata
    settings: Mapped[dict | None] = mapped_column(JSON)  # Tenant-specific settings
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")  # type: ignore[assignment]
    channels: Mapped[list["Channel"]] = relationship("Channel", back_populates="tenant")  # type: ignore[assignment]
    videos: Mapped[list["Video"]] = relationship("Video", back_populates="tenant")  # type: ignore[assignment]
    fingerprints: Mapped[list["AudioFingerprint"]] = relationship("AudioFingerprint", back_populates="tenant")  # type: ignore[assignment]
