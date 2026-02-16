"""Processing job model for background task tracking and management."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

if TYPE_CHECKING:
    pass


class ProcessingJob(Base):  # type: ignore[misc,valid-type]
    """Model for tracking background processing jobs."""

    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_type: Mapped[str | None] = mapped_column(String(50))  # 'channel_ingest', 'video_process', 'fingerprint_extract'
    status: Mapped[str | None] = mapped_column(String(20))  # 'pending', 'running', 'completed', 'failed'

    # Job data
    target_id: Mapped[str | None] = mapped_column(String(255))  # Channel ID or Video ID
    parameters: Mapped[str | None] = mapped_column(Text)  # JSON parameters

    # Progress tracking
    progress: Mapped[float] = mapped_column(default=0.0)  # 0.0 to 1.0
    current_step: Mapped[str | None] = mapped_column(String(200))

    # Timing
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(default=0)
    max_retries: Mapped[int] = mapped_column(default=3)
