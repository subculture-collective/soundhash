"""Pydantic models for audio matching."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from src.api.models.common import IDMixin


class MatchRequest(BaseModel):
    """Match request model for finding audio matches."""

    audio_url: HttpUrl | None = Field(None, description="URL to audio/video file")
    video_url: HttpUrl | None = Field(None, description="YouTube video URL")
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence score")
    max_results: int = Field(default=10, ge=1, le=100, description="Maximum number of results")


class MatchSegment(BaseModel):
    """Matched segment information."""

    video_id: str
    title: str
    confidence: float
    similarity_score: float
    start_time: float
    end_time: float
    duration: float
    thumbnail_url: str | None = None
    video_url: str


class MatchResponse(BaseModel):
    """Match response with all matched segments."""

    query_id: int
    total_matches: int
    matches: list[MatchSegment]
    processing_time_ms: float
    created_at: datetime


class BulkMatchRequest(BaseModel):
    """Bulk match request for multiple queries."""

    queries: list[MatchRequest] = Field(..., max_length=10, description="Up to 10 queries")


class BulkMatchResponse(BaseModel):
    """Bulk match response."""

    results: list[MatchResponse]
    total_queries: int
    successful: int
    failed: int


class FingerprintResponse(IDMixin):
    """Fingerprint response model."""

    video_id: int
    start_time: float
    end_time: float
    fingerprint_hash: str
    sample_rate: int
    segment_length: float
    confidence_score: float | None = None
    peak_count: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



class FingerprintStats(BaseModel):
    """Fingerprint statistics."""

    total_fingerprints: int
    total_videos: int
    avg_confidence: float
    avg_peaks: float
    total_duration_hours: float
