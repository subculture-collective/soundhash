"""Pydantic models for channels."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.api.models.common import IDMixin, TimestampMixin


class ChannelBase(BaseModel):
    """Base channel model."""

    channel_id: str
    channel_name: str | None = None
    description: str | None = None


class ChannelResponse(ChannelBase, IDMixin, TimestampMixin):
    """Channel response model."""

    subscriber_count: int | None = None
    video_count: int | None = None
    last_processed: datetime | None = None
    is_active: bool

    class Config:
        from_attributes = True


class ChannelIngestRequest(BaseModel):
    """Channel ingest request."""

    channel_url: str = Field(..., description="YouTube channel URL or channel ID")
    max_videos: int | None = Field(None, ge=1, le=1000, description="Maximum videos to process")
    skip_processed: bool = Field(default=True, description="Skip already processed videos")


class ChannelIngestResponse(BaseModel):
    """Channel ingest response."""

    channel_id: str
    channel_name: str
    videos_found: int
    videos_queued: int
    job_ids: list[int]
    message: str


class ChannelUpdate(BaseModel):
    """Channel update model."""

    is_active: bool | None = None
    channel_name: str | None = None
    description: str | None = None


class ChannelStats(BaseModel):
    """Channel statistics."""

    channel_id: str
    channel_name: str
    total_videos: int
    processed_videos: int
    total_fingerprints: int
    last_processed: datetime | None = None
