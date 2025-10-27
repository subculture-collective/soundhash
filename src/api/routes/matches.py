"""Audio matching routes."""

import math
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.api.middleware import limiter
from src.api.models.common import PaginatedResponse, PaginationParams
from src.api.models.matches import (
    BulkMatchRequest,
    BulkMatchResponse,
    MatchRequest,
    MatchResponse,
    MatchSegment,
)
from src.database.models import AudioFingerprint, MatchResult, User, Video

router = APIRouter()


@router.post("/find", response_model=MatchResponse)
async def find_matches(
    match_request: MatchRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Find audio matches for uploaded clip or URL."""
    start_time = time.time()
    
    # Validate request
    if not match_request.audio_url and not match_request.video_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either audio_url or video_url must be provided",
        )
    
    # In production, this would:
    # 1. Download the audio/video from URL
    # 2. Extract audio fingerprint
    # 3. Compare against database fingerprints
    # 4. Return top matches
    
    # For now, return mock data to demonstrate structure
    mock_matches = []
    
    # Query some videos as examples
    videos = db.query(Video).filter(Video.processed == True).limit(match_request.max_results).all()
    
    for idx, video in enumerate(videos):
        mock_matches.append(MatchSegment(
            video_id=video.video_id,
            title=video.title or "Untitled Video",
            confidence=0.95 - (idx * 0.05),  # Mock decreasing confidence
            similarity_score=0.92 - (idx * 0.04),
            start_time=0.0,
            end_time=90.0,
            duration=90.0,
            thumbnail_url=video.thumbnail_url,
            video_url=video.url or f"https://youtube.com/watch?v={video.video_id}",
        ))
    
    processing_time = (time.time() - start_time) * 1000
    
    return MatchResponse(
        query_id=0,  # Would be actual query ID
        total_matches=len(mock_matches),
        matches=mock_matches,
        processing_time_ms=processing_time,
        created_at=db.query(Video).first().created_at if videos else None,
    )


@router.get("/{match_id}", response_model=dict)
async def get_match_details(
    match_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get details of a specific match."""
    match = db.query(MatchResult).filter(MatchResult.id == match_id).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )
    
    return {
        "id": match.id,
        "query_fingerprint_id": match.query_fingerprint_id,
        "matched_fingerprint_id": match.matched_fingerprint_id,
        "similarity_score": match.similarity_score,
        "match_confidence": match.match_confidence,
        "query_source": match.query_source,
        "query_url": match.query_url,
        "query_user": match.query_user,
        "created_at": match.created_at.isoformat() if match.created_at else None,
    }


@router.get("/", response_model=PaginatedResponse[dict])
async def list_matches(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    pagination: PaginationParams = Depends(),
):
    """List user's match queries."""
    # In production, would filter by user
    query = db.query(MatchResult).order_by(desc(MatchResult.created_at))
    
    total = query.count()
    offset = (pagination.page - 1) * pagination.per_page
    matches = query.offset(offset).limit(pagination.per_page).all()
    
    return PaginatedResponse(
        data=[{
            "id": m.id,
            "similarity_score": m.similarity_score,
            "query_source": m.query_source,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        } for m in matches],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page),
    )


@router.post("/bulk", response_model=BulkMatchResponse)
async def bulk_match(
    bulk_request: BulkMatchRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Batch match multiple audio clips."""
    results = []
    successful = 0
    failed = 0
    
    for query in bulk_request.queries:
        try:
            # Process each query
            # In production, would actually process the query
            result = MatchResponse(
                query_id=0,
                total_matches=0,
                matches=[],
                processing_time_ms=0.0,
                created_at=db.query(Video).first().created_at if db.query(Video).first() else None,
            )
            results.append(result)
            successful += 1
        except Exception:
            failed += 1
    
    return BulkMatchResponse(
        results=results,
        total_queries=len(bulk_request.queries),
        successful=successful,
        failed=failed,
    )
