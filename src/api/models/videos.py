"""Pydantic models for videos."""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from src.api.models.common import IDMixin, TimestampMixin


class VideoBase(BaseModel):
    """Base video model."""

    video_id: str
    title: str | None = None
    description: str | None = None
    url: str | None = None
    thumbnail_url: str | None = None


class VideoResponse(VideoBase, IDMixin, TimestampMixin):
    """Video response model."""

    channel_id: int
    duration: float | None = None
    view_count: int | None = None
    like_count: int | None = None
    upload_date: datetime | None = None
    processed: bool
    processing_started: datetime | None = None
    processing_completed: datetime | None = None
    processing_error: str | None = None

    class Config:
        from_attributes = True


class VideoUploadRequest(BaseModel):
    """Video upload request."""

    video_url: HttpUrl = Field(..., description="YouTube video URL or video ID")
    priority: int = Field(default=0, ge=0, le=10, description="Processing priority (0-10)")


class VideoUploadResponse(BaseModel):
    """Video upload response."""

    video_id: str
    job_id: int
    status: str
    message: str


class VideoProcessingStatus(BaseModel):
    """Video processing status."""

    video_id: str
    status: str
    progress: float = Field(..., ge=0.0, le=1.0)
    current_step: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class VideoListFilter(BaseModel):
    """Video list filter parameters."""

    channel_id: int | None = None
    processed: bool | None = None
    search: str | None = Field(None, max_length=255, description="Search in title/description")
    order_by: str = Field(default="created_at", description="Field to order by")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
