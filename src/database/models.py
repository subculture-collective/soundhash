from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeMeta, Mapped, relationship

Base: DeclarativeMeta = declarative_base()  # type: ignore[assignment]


class Channel(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    channel_id = Column(String(255), unique=True, nullable=False)
    channel_name = Column(String(500))
    description = Column(Text)
    subscriber_count = Column(Integer)
    video_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_processed = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Relationships
    videos: Mapped[list["Video"]] = relationship("Video", back_populates="channel")  # type: ignore[assignment]


class Video(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)
    video_id = Column(String(255), unique=True, nullable=False)  # YouTube video ID
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    title = Column(String(1000))
    description = Column(Text)
    duration = Column(Float)  # Duration in seconds
    view_count = Column(Integer)
    like_count = Column(Integer)
    upload_date = Column(DateTime)
    url = Column(String(500))
    thumbnail_url = Column(String(500))

    # Processing status
    processed = Column(Boolean, default=False)
    processing_started = Column(DateTime)
    processing_completed = Column(DateTime)
    processing_error = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    channel: Mapped["Channel"] = relationship("Channel", back_populates="videos")  # type: ignore[assignment]
    fingerprints: Mapped[list["AudioFingerprint"]] = relationship("AudioFingerprint", back_populates="video")  # type: ignore[assignment]


class AudioFingerprint(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "audio_fingerprints"

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)

    # Time segments
    start_time = Column(Float, nullable=False)  # Start time in seconds
    end_time = Column(Float, nullable=False)  # End time in seconds

    # Fingerprint data
    fingerprint_hash = Column(String(64), nullable=False)  # MD5 hash for quick lookup
    fingerprint_data = Column(LargeBinary)  # Serialized fingerprint data

    # Audio characteristics
    sample_rate = Column(Integer, default=22050)
    segment_length = Column(Float)  # Length of this segment

    # Quality metrics
    confidence_score = Column(Float)  # Confidence in fingerprint quality
    peak_count = Column(Integer)  # Number of spectral peaks detected

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    video: Mapped["Video"] = relationship("Video", back_populates="fingerprints")  # type: ignore[assignment]


class MatchResult(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True)
    query_fingerprint_id = Column(Integer, ForeignKey("audio_fingerprints.id"))
    matched_fingerprint_id = Column(Integer, ForeignKey("audio_fingerprints.id"))

    # Match quality
    similarity_score = Column(Float, nullable=False)
    match_confidence = Column(Float)

    # Query metadata
    query_source = Column(String(50))  # 'twitter', 'reddit', 'manual'
    query_url = Column(String(1000))  # Original query URL
    query_user = Column(String(100))  # Username who requested

    # Response metadata
    responded = Column(Boolean, default=False)
    response_sent_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)


class ProcessingJob(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True)
    job_type = Column(String(50))  # 'channel_ingest', 'video_process', 'fingerprint_extract'
    status = Column(String(20))  # 'pending', 'running', 'completed', 'failed'

    # Job data
    target_id = Column(String(255))  # Channel ID or Video ID
    parameters = Column(Text)  # JSON parameters

    # Progress tracking
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    current_step = Column(String(200))

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)


# Indexes for performance
Index("idx_videos_channel_id", Video.channel_id)
Index("idx_videos_video_id", Video.video_id)
Index("idx_videos_processed", Video.processed)
Index("idx_fingerprints_video_id", AudioFingerprint.video_id)
Index("idx_fingerprints_hash", AudioFingerprint.fingerprint_hash)
Index("idx_fingerprints_time", AudioFingerprint.start_time, AudioFingerprint.end_time)
Index("idx_match_results_similarity", MatchResult.similarity_score)
Index("idx_processing_jobs_status", ProcessingJob.status)
Index("idx_processing_jobs_type", ProcessingJob.job_type)
