"""Admin routes."""

import math
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, text
from sqlalchemy.orm import Session

from src.api.dependencies import get_admin_user, get_db
from src.api.models.common import PaginatedResponse, PaginationParams, SuccessResponse
from src.database.models import Channel, ProcessingJob, User, Video

router = APIRouter()


@router.get("/stats")
async def get_system_stats(
    admin_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get system statistics (admin only)."""
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0

    total_channels = db.query(func.count(Channel.id)).scalar() or 0
    active_channels = db.query(func.count(Channel.id)).filter(Channel.is_active == True).scalar() or 0

    total_videos = db.query(func.count(Video.id)).scalar() or 0
    processed_videos = db.query(func.count(Video.id)).filter(Video.processed == True).scalar() or 0

    pending_jobs = db.query(func.count(ProcessingJob.id)).filter(
        ProcessingJob.status == 'pending'
    ).scalar() or 0

    running_jobs = db.query(func.count(ProcessingJob.id)).filter(
        ProcessingJob.status == 'running'
    ).scalar() or 0

    failed_jobs = db.query(func.count(ProcessingJob.id)).filter(
        ProcessingJob.status == 'failed'
    ).scalar() or 0

    return {
        "users": {
            "total": total_users,
            "active": active_users,
        },
        "channels": {
            "total": total_channels,
            "active": active_channels,
        },
        "videos": {
            "total": total_videos,
            "processed": processed_videos,
            "pending": total_videos - processed_videos,
        },
        "jobs": {
            "pending": pending_jobs,
            "running": running_jobs,
            "failed": failed_jobs,
        },
    }


@router.get("/jobs", response_model=PaginatedResponse[dict])
async def list_jobs(
    admin_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[Session, Depends(get_db)],
    pagination: PaginationParams = Depends(),
    status_filter: str | None = Query(None),
    job_type: str | None = Query(None),
):
    """List processing jobs (admin only)."""
    query = db.query(ProcessingJob)

    if status_filter:
        query = query.filter(ProcessingJob.status == status_filter)

    if job_type:
        query = query.filter(ProcessingJob.job_type == job_type)

    query = query.order_by(desc(ProcessingJob.created_at))

    total = query.count()
    offset = (pagination.page - 1) * pagination.per_page
    jobs = query.offset(offset).limit(pagination.per_page).all()

    return PaginatedResponse(
        data=[{
            "id": j.id,
            "job_type": j.job_type,
            "status": j.status,
            "target_id": j.target_id,
            "progress": j.progress,
            "current_step": j.current_step,
            "error_message": j.error_message,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
        } for j in jobs],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page),
    )


@router.post("/jobs/{job_id}/retry", response_model=SuccessResponse)
async def retry_job(
    job_id: int,
    admin_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retry a failed job (admin only)."""
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.status not in ['failed', 'completed']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only retry failed or completed jobs",
        )

    # Reset job status
    job.status = 'pending'
    job.progress = 0.0
    job.current_step = None
    job.error_message = None
    job.started_at = None
    job.completed_at = None
    job.retry_count += 1

    db.commit()

    return SuccessResponse(message="Job queued for retry")


@router.get("/users", response_model=PaginatedResponse[dict])
async def list_users(
    admin_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[Session, Depends(get_db)],
    pagination: PaginationParams = Depends(),
    is_active: bool | None = Query(None),
):
    """List all users (admin only)."""
    query = db.query(User)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    query = query.order_by(desc(User.created_at))

    total = query.count()
    offset = (pagination.page - 1) * pagination.per_page
    users = query.offset(offset).limit(pagination.per_page).all()

    return PaginatedResponse(
        data=[{
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "is_active": u.is_active,
            "is_admin": u.is_admin,
            "is_verified": u.is_verified,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None,
        } for u in users],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page),
    )


@router.delete("/users/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: int,
    admin_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Delete a user (admin only)."""
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()

    return SuccessResponse(message="User deleted successfully")


@router.post("/users/{user_id}/ban", response_model=SuccessResponse)
async def ban_user(
    user_id: int,
    admin_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Ban a user (admin only)."""
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot ban your own account",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.is_active = False
    db.commit()

    return SuccessResponse(message="User banned successfully")


@router.post("/users/{user_id}/unban", response_model=SuccessResponse)
async def unban_user(
    user_id: int,
    admin_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Unban a user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.is_active = True
    db.commit()

    return SuccessResponse(message="User unbanned successfully")


@router.post("/jobs/{job_id}/cancel", response_model=SuccessResponse)
async def cancel_job(
    job_id: int,
    admin_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Cancel a pending or running job (admin only)."""
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.status not in ['pending', 'running']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel pending or running jobs",
        )

    job.status = 'cancelled'
    job.error_message = "Cancelled by admin"
    db.commit()

    return SuccessResponse(message="Job cancelled successfully")


@router.get("/health")
async def admin_health_check(
    admin_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get detailed health check information (admin only)."""
    # Check database
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Check job queue health
    stuck_jobs = db.query(func.count(ProcessingJob.id)).filter(
        ProcessingJob.status == 'running',
        ProcessingJob.started_at < datetime.now(UTC) - timedelta(hours=2)
    ).scalar() or 0

    return {
        "status": "healthy" if db_status == "healthy" and stuck_jobs == 0 else "degraded",
        "database": db_status,
        "stuck_jobs": stuck_jobs,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/analytics")
async def get_analytics(
    admin_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[Session, Depends(get_db)],
    start_date: str | None = Query(None, description="Start date (ISO format)"),
    end_date: str | None = Query(None, description="End date (ISO format)"),
):
    """Get analytics data with optional date filtering (admin only)."""
    # Default to last 30 days
    if not start_date:
        start_dt = datetime.now(UTC) - timedelta(days=30)
    else:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid start_date format: '{start_date}'. Expected ISO format.",
            )
    
    if not end_date:
        end_dt = datetime.now(UTC)
    else:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid end_date format: '{end_date}'. Expected ISO format.",
            )

    # User growth over time - optimized with GROUP BY
    user_counts = db.query(
        func.date_trunc('day', User.created_at).label('day'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= start_dt,
        User.created_at <= end_dt
    ).group_by(
        func.date_trunc('day', User.created_at)
    ).order_by(
        func.date_trunc('day', User.created_at)
    ).all()

    # Build a dict for fast lookup
    user_counts_by_day = {
        day.strftime('%Y-%m-%d'): count for day, count in user_counts
    }

    user_growth = []
    current_date = start_dt
    while current_date <= end_dt:
        date_str = current_date.strftime('%Y-%m-%d')
        count = user_counts_by_day.get(date_str, 0)
        user_growth.append({
            "date": date_str,
            "count": count
        })
        current_date += timedelta(days=1)

    # Job status distribution
    job_status = []
    for status_name in ['pending', 'running', 'completed', 'failed', 'cancelled']:
        count = db.query(func.count(ProcessingJob.id)).filter(
            ProcessingJob.status == status_name,
            ProcessingJob.created_at >= start_dt,
            ProcessingJob.created_at <= end_dt
        ).scalar() or 0
        
        job_status.append({
            "status": status_name,
            "count": count
        })

    # Video processing stats
    videos_processed = db.query(func.count(Video.id)).filter(
        Video.processed,
        Video.created_at >= start_dt,
        Video.created_at <= end_dt
    ).scalar() or 0

    return {
        "user_growth": user_growth,
        "job_status": job_status,
        "videos_processed": videos_processed,
        "start_date": start_dt.isoformat(),
        "end_date": end_dt.isoformat(),
    }
