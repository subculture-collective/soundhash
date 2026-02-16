"""Audio fingerprint and matching models."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .tenant import Tenant
    from .video import Video


class AudioFingerprint(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "audio_fingerprints"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"))

    # Time segments
    start_time: Mapped[float] = mapped_column()  # Start time in seconds
    end_time: Mapped[float] = mapped_column()  # End time in seconds

    # Fingerprint data
    fingerprint_hash: Mapped[str] = mapped_column(String(64))  # MD5 hash for quick lookup
    fingerprint_data: Mapped[bytes | None] = mapped_column(LargeBinary)  # Serialized fingerprint data

    # Audio characteristics
    sample_rate: Mapped[int | None] = mapped_column(default=22050)
    segment_length: Mapped[float | None] = mapped_column()  # Length of this segment

    # Fingerprint extraction parameters (for cache invalidation)
    n_fft: Mapped[int] = mapped_column(default=2048)  # FFT window size used for extraction
    hop_length: Mapped[int] = mapped_column(default=512)  # Hop length used for extraction

    # Quality metrics
    confidence_score: Mapped[float | None] = mapped_column()  # Confidence in fingerprint quality
    peak_count: Mapped[int | None] = mapped_column()  # Number of spectral peaks detected

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="fingerprints")  # type: ignore[assignment]
    video: Mapped["Video"] = relationship("Video", back_populates="fingerprints")  # type: ignore[assignment]


class MatchResult(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    query_fingerprint_id: Mapped[int | None] = mapped_column(ForeignKey("audio_fingerprints.id"))
    matched_fingerprint_id: Mapped[int | None] = mapped_column(ForeignKey("audio_fingerprints.id"))

    # Match quality
    similarity_score: Mapped[float] = mapped_column()
    match_confidence: Mapped[float | None] = mapped_column()

    # Query metadata
    query_source: Mapped[str | None] = mapped_column(String(50))  # 'twitter', 'reddit', 'manual'
    query_url: Mapped[str | None] = mapped_column(String(1000))  # Original query URL
    query_user: Mapped[str | None] = mapped_column(String(100))  # Username who requested

    # Response metadata
    responded: Mapped[bool] = mapped_column(default=False)
    response_sent_at: Mapped[datetime | None] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
