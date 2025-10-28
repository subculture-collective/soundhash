"""Fingerprint routes."""

import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.api.models.common import PaginatedResponse, PaginationParams
from src.api.models.matches import FingerprintResponse, FingerprintStats
from src.database.models import AudioFingerprint, User, Video

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[FingerprintResponse])
async def list_fingerprints(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    pagination: PaginationParams = Depends(),
    video_id: int | None = Query(None),
):
    """List audio fingerprints."""
    query = db.query(AudioFingerprint)
    
    if video_id:
        query = query.filter(AudioFingerprint.video_id == video_id)
    
    query = query.order_by(desc(AudioFingerprint.created_at))
    
    total = query.count()
    offset = (pagination.page - 1) * pagination.per_page
    fingerprints = query.offset(offset).limit(pagination.per_page).all()
    
    return PaginatedResponse(
        data=fingerprints,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page),
    )


@router.get("/stats", response_model=FingerprintStats)
async def get_fingerprint_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get fingerprint statistics."""
    total_fingerprints = db.query(func.count(AudioFingerprint.id)).scalar() or 0
    
    total_videos = db.query(func.count(func.distinct(AudioFingerprint.video_id))).scalar() or 0
    
    avg_confidence = db.query(func.avg(AudioFingerprint.confidence_score)).scalar() or 0.0
    
    avg_peaks = db.query(func.avg(AudioFingerprint.peak_count)).scalar() or 0.0
    
    total_duration = db.query(func.sum(AudioFingerprint.segment_length)).scalar() or 0.0
    total_duration_hours = total_duration / 3600.0
    
    return FingerprintStats(
        total_fingerprints=total_fingerprints,
        total_videos=total_videos,
        avg_confidence=float(avg_confidence),
        avg_peaks=float(avg_peaks),
        total_duration_hours=total_duration_hours,
    )


@router.get("/{fingerprint_id}", response_model=FingerprintResponse)
async def get_fingerprint(
    fingerprint_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get fingerprint details."""
    fingerprint = db.query(AudioFingerprint).filter(AudioFingerprint.id == fingerprint_id).first()
    
    if not fingerprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fingerprint not found",
        )
    
    return fingerprint
