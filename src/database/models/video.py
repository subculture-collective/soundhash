"""Video and channel models."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .fingerprint import AudioFingerprint
    from .tenant import Tenant


class Channel(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    channel_id: Mapped[str] = mapped_column(String(255), unique=True)
    channel_name: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    subscriber_count: Mapped[int | None] = mapped_column()
    video_count: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_processed: Mapped[datetime | None] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="channels")  # type: ignore[assignment]
    videos: Mapped[list["Video"]] = relationship("Video", back_populates="channel")  # type: ignore[assignment]


class Video(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    video_id: Mapped[str] = mapped_column(String(255), unique=True)  # YouTube video ID
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"))
    title: Mapped[str | None] = mapped_column(String(1000))
    description: Mapped[str | None] = mapped_column(Text)
    duration: Mapped[float | None] = mapped_column()  # Duration in seconds
    view_count: Mapped[int | None] = mapped_column()
    like_count: Mapped[int | None] = mapped_column()
    upload_date: Mapped[datetime | None] = mapped_column()
    url: Mapped[str | None] = mapped_column(String(500))
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))

    # Processing status
    processed: Mapped[bool] = mapped_column(default=False)
    processing_started: Mapped[datetime | None] = mapped_column()
    processing_completed: Mapped[datetime | None] = mapped_column()
    processing_error: Mapped[str | None] = mapped_column(Text)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="videos")  # type: ignore[assignment]
    channel: Mapped["Channel"] = relationship("Channel", back_populates="videos")  # type: ignore[assignment]
    fingerprints: Mapped[list["AudioFingerprint"]] = relationship("AudioFingerprint", back_populates="video")  # type: ignore[assignment]
