"""Channel management routes."""

import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.api.middleware import limiter
from src.api.models.channels import (
    ChannelIngestRequest,
    ChannelIngestResponse,
    ChannelResponse,
    ChannelStats,
    ChannelUpdate,
)
from src.api.models.common import PaginatedResponse, PaginationParams, SuccessResponse
from src.database.models import AudioFingerprint, Channel, User, Video

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ChannelResponse])
async def list_channels(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    pagination: PaginationParams = Depends(),
    is_active: bool | None = Query(None),
):
    """List ingested channels."""
    query = db.query(Channel)
    
    if is_active is not None:
        query = query.filter(Channel.is_active == is_active)
    
    query = query.order_by(desc(Channel.created_at))
    
    total = query.count()
    offset = (pagination.page - 1) * pagination.per_page
    channels = query.offset(offset).limit(pagination.per_page).all()
    
    return PaginatedResponse(
        data=channels,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page),
    )


@router.post("/ingest", response_model=ChannelIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_channel(
    ingest_data: ChannelIngestRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Ingest a new YouTube channel."""
    # Extract channel ID from URL
    channel_url = ingest_data.channel_url
    
    # Simple extraction - in production would use YouTube API
    if "channel/" in channel_url:
        channel_id = channel_url.split("channel/")[-1].split("/")[0].split("?")[0]
    elif "@" in channel_url:
        channel_id = channel_url.split("@")[-1].split("/")[0].split("?")[0]
    else:
        channel_id = channel_url
    
    # Check if channel exists
    existing_channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()
    
    if existing_channel:
        channel_name = existing_channel.channel_name or channel_id
        
        # In production, would trigger ingestion job here
        return ChannelIngestResponse(
            channel_id=channel_id,
            channel_name=channel_name,
            videos_found=0,
            videos_queued=0,
            job_ids=[],
            message="Channel already exists. Use reprocess to update.",
        )
    
    # Create new channel
    new_channel = Channel(
        channel_id=channel_id,
        channel_name=channel_id,  # Would fetch from YouTube API
        is_active=True,
    )
    db.add(new_channel)
    db.commit()
    db.refresh(new_channel)
    
    # In production, would:
    # 1. Fetch channel metadata from YouTube API
    # 2. List videos using YouTube API
    # 3. Create video records
    # 4. Create processing jobs
    
    return ChannelIngestResponse(
        channel_id=channel_id,
        channel_name=channel_id,
        videos_found=0,
        videos_queued=0,
        job_ids=[],
        message="Channel created. In production, would queue videos for processing.",
    )


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get channel details."""
    channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )
    
    return channel


@router.get("/{channel_id}/videos", response_model=PaginatedResponse[dict])
async def get_channel_videos(
    channel_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    pagination: PaginationParams = Depends(),
):
    """Get videos for a channel."""
    # Find channel
    channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )
    
    # Get videos
    query = db.query(Video).filter(Video.channel_id == channel.id).order_by(desc(Video.created_at))
    
    total = query.count()
    offset = (pagination.page - 1) * pagination.per_page
    videos = query.offset(offset).limit(pagination.per_page).all()
    
    return PaginatedResponse(
        data=[{
            "id": v.id,
            "video_id": v.video_id,
            "title": v.title,
            "processed": v.processed,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        } for v in videos],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page),
    )


@router.get("/{channel_id}/stats", response_model=ChannelStats)
async def get_channel_stats(
    channel_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get channel statistics."""
    channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )
    
    # Count videos
    total_videos = db.query(func.count(Video.id)).filter(Video.channel_id == channel.id).scalar()
    
    processed_videos = db.query(func.count(Video.id)).filter(
        Video.channel_id == channel.id,
        Video.processed == True
    ).scalar()
    
    # Count fingerprints
    total_fingerprints = db.query(func.count(AudioFingerprint.id)).join(
        Video, AudioFingerprint.video_id == Video.id
    ).filter(Video.channel_id == channel.id).scalar()
    
    return ChannelStats(
        channel_id=channel.channel_id,
        channel_name=channel.channel_name or channel.channel_id,
        total_videos=total_videos or 0,
        processed_videos=processed_videos or 0,
        total_fingerprints=total_fingerprints or 0,
        last_processed=channel.last_processed,
    )


@router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: str,
    update_data: ChannelUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update channel settings."""
    channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )
    
    if update_data.is_active is not None:
        channel.is_active = update_data.is_active
    
    if update_data.channel_name is not None:
        channel.channel_name = update_data.channel_name
    
    if update_data.description is not None:
        channel.description = update_data.description
    
    db.commit()
    db.refresh(channel)
    
    return channel


@router.delete("/{channel_id}", response_model=SuccessResponse)
async def delete_channel(
    channel_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Delete a channel."""
    channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )
    
    # Note: In production, should handle cascade deletion of videos and fingerprints
    db.delete(channel)
    db.commit()
    
    return SuccessResponse(message="Channel deleted successfully")
