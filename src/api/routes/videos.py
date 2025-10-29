"""Video management routes."""

import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.api.models.common import PaginatedResponse, PaginationParams, SuccessResponse
from src.api.models.videos import (
    VideoProcessingStatus,
    VideoResponse,
    VideoUploadRequest,
    VideoUploadResponse,
)
from src.database.models import ProcessingJob, User, Video
from src.database.repositories import get_job_repository, get_video_repository

router = APIRouter()


@router.post("/upload", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    video_data: VideoUploadRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Upload a video URL for processing."""
    # Extract video ID from URL
    video_url = str(video_data.video_url)
    video_id = video_url.split("v=")[-1].split("&")[0] if "v=" in video_url else video_url.split("/")[-1]

    # Check if video already exists
    video_repo = get_video_repository()
    existing_video = video_repo.get_by_video_id(video_id)

    if existing_video:
        # Check if there's already a pending/running job
        job_repo = get_job_repository()
        existing_job = job_repo.job_exists(
            'video_process',
            video_id,
            statuses=['pending', 'running']
        )

        if existing_job:
            return VideoUploadResponse(
                video_id=video_id,
                job_id=existing_job,
                status="already_queued",
                message="Video is already queued for processing",
            )

        # Create new processing job
        job = job_repo.create_job(
            job_type='video_process',
            target_id=video_id,
            parameters=f'{{"priority": {video_data.priority}}}',
        )

        return VideoUploadResponse(
            video_id=video_id,
            job_id=job.id,
            status="queued",
            message="Video queued for reprocessing",
        )

    # Get or create a default channel for user uploads
    from src.database.models import Channel
    default_channel = db.query(Channel).filter(Channel.channel_id == "user_uploads").first()
    if not default_channel:
        default_channel = Channel(
            channel_id="user_uploads",
            channel_name="User Uploads",
            description="Default channel for user-uploaded videos",
            is_active=True,
        )
        db.add(default_channel)
        db.commit()
        db.refresh(default_channel)

    # Create video record
    new_video = Video(
        video_id=video_id,
        url=video_url,
        channel_id=default_channel.id,
        processed=False,
    )
    db.add(new_video)
    db.commit()
    db.refresh(new_video)

    # Create processing job
    job_repo = get_job_repository()
    job = job_repo.create_job(
        job_type='video_process',
        target_id=video_id,
        parameters=f'{{"priority": {video_data.priority}}}',
    )

    return VideoUploadResponse(
        video_id=video_id,
        job_id=job.id,
        status="queued",
        message="Video queued for processing",
    )


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get video metadata by ID."""
    video = db.query(Video).filter(Video.video_id == video_id).first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    return video


@router.get("/", response_model=PaginatedResponse[VideoResponse])
async def list_videos(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    pagination: PaginationParams = Depends(),
    channel_id: int | None = Query(None),
    processed: bool | None = Query(None),
    search: str | None = Query(None, max_length=255),
    order_by: str = Query("created_at"),
    order_dir: str = Query("desc", pattern="^(asc|desc)$"),
):
    """List videos with filters and pagination."""
    query = db.query(Video)

    # Apply filters
    if channel_id:
        query = query.filter(Video.channel_id == channel_id)

    if processed is not None:
        query = query.filter(Video.processed == processed)

    if search:
        query = query.filter(
            or_(
                Video.title.ilike(f"%{search}%"),
                Video.description.ilike(f"%{search}%"),
                Video.video_id.ilike(f"%{search}%"),
            )
        )

    # Apply ordering
    order_column = getattr(Video, order_by, Video.created_at)
    if order_dir == "desc":
        query = query.order_by(desc(order_column))
    else:
        query = query.order_by(asc(order_column))

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (pagination.page - 1) * pagination.per_page
    videos = query.offset(offset).limit(pagination.per_page).all()

    return PaginatedResponse(
        data=videos,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page),
    )


@router.get("/{video_id}/status", response_model=VideoProcessingStatus)
async def get_video_status(
    video_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get video processing status."""
    # Find the video
    video = db.query(Video).filter(Video.video_id == video_id).first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    # Find the latest processing job
    job = db.query(ProcessingJob).filter(
        ProcessingJob.target_id == video_id,
        ProcessingJob.job_type == 'video_process'
    ).order_by(desc(ProcessingJob.created_at)).first()

    if not job:
        return VideoProcessingStatus(
            video_id=video_id,
            status="not_started",
            progress=0.0,
            current_step=None,
            error_message=None,
            started_at=None,
            completed_at=None,
        )

    return VideoProcessingStatus(
        video_id=video_id,
        status=job.status,
        progress=job.progress,
        current_step=job.current_step,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.post("/{video_id}/reprocess", response_model=VideoUploadResponse)
async def reprocess_video(
    video_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Trigger video reprocessing."""
    video = db.query(Video).filter(Video.video_id == video_id).first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    # Check for existing pending/running jobs
    job_repo = get_job_repository()
    existing_job = job_repo.job_exists(
        'video_process',
        video_id,
        statuses=['pending', 'running']
    )

    if existing_job:
        return VideoUploadResponse(
            video_id=video_id,
            job_id=existing_job,
            status="already_queued",
            message="Video is already queued for processing",
        )

    # Create new job
    job = job_repo.create_job(
        job_type='video_process',
        target_id=video_id,
        parameters='{"priority": 5}',
    )

    return VideoUploadResponse(
        video_id=video_id,
        job_id=job.id,
        status="queued",
        message="Video queued for reprocessing",
    )


@router.delete("/{video_id}", response_model=SuccessResponse)
async def delete_video(
    video_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Delete a video (admin only - simplified for now)."""
    video = db.query(Video).filter(Video.video_id == video_id).first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    # Note: In production, should also delete associated fingerprints and jobs
    db.delete(video)
    db.commit()

    return SuccessResponse(message="Video deleted successfully")
