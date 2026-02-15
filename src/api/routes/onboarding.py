"""Onboarding and tutorial routes."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.api.models.onboarding import (
    OnboardingProgressCreate,
    OnboardingProgressResponse,
    OnboardingProgressUpdate,
    OnboardingStatsResponse,
    TutorialProgressCreate,
    TutorialProgressResponse,
    TutorialProgressUpdate,
    UserPreferenceCreate,
    UserPreferenceResponse,
    UserPreferenceUpdate,
)
from src.database.models import OnboardingProgress, TutorialProgress, User, UserPreference

router = APIRouter()


@router.get("/progress", response_model=OnboardingProgressResponse)
async def get_onboarding_progress(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get current user's onboarding progress."""
    progress = db.query(OnboardingProgress).filter(OnboardingProgress.user_id == current_user.id).first()

    if not progress:
        # Create new progress record if doesn't exist
        progress = OnboardingProgress(
            user_id=current_user.id,
            current_step=0,
            is_completed=False,
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)

    return progress


@router.post("/progress", response_model=OnboardingProgressResponse, status_code=status.HTTP_201_CREATED)
async def create_onboarding_progress(
    progress_data: OnboardingProgressCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create or reset onboarding progress for current user."""
    existing = db.query(OnboardingProgress).filter(OnboardingProgress.user_id == current_user.id).first()

    if existing:
        # Reset existing progress
        existing.current_step = progress_data.current_step
        existing.use_case = progress_data.use_case
        existing.is_completed = progress_data.is_completed
        existing.welcome_completed = False
        existing.use_case_selected = False
        existing.api_key_generated = False
        existing.first_upload_completed = False
        existing.dashboard_explored = False
        existing.integration_started = False
        existing.tour_completed = False
        existing.tour_dismissed = False
        existing.tour_last_step = 0
        existing.sample_data_generated = False
        existing.started_at = datetime.now(timezone.utc)
        existing.completed_at = None
        db.commit()
        db.refresh(existing)
        return existing

    # Create new progress
    progress = OnboardingProgress(
        user_id=current_user.id,
        current_step=progress_data.current_step,
        use_case=progress_data.use_case,
        is_completed=progress_data.is_completed,
    )
    db.add(progress)
    db.commit()
    db.refresh(progress)

    return progress


@router.patch("/progress", response_model=OnboardingProgressResponse)
async def update_onboarding_progress(
    progress_data: OnboardingProgressUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update onboarding progress for current user."""
    progress = db.query(OnboardingProgress).filter(OnboardingProgress.user_id == current_user.id).first()

    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding progress not found",
        )

    # Update fields if provided
    update_data = progress_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(progress, field, value)

    # Set completion timestamp if completed
    if progress_data.is_completed and progress.completed_at is None:
        progress.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(progress)

    return progress


@router.get("/tutorials", response_model=list[TutorialProgressResponse])
async def list_tutorial_progress(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get all tutorial progress for current user."""
    tutorials = db.query(TutorialProgress).filter(TutorialProgress.user_id == current_user.id).all()
    return tutorials


@router.get("/tutorials/{tutorial_id}", response_model=TutorialProgressResponse)
async def get_tutorial_progress(
    tutorial_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get progress for a specific tutorial."""
    tutorial = (
        db.query(TutorialProgress)
        .filter(
            TutorialProgress.user_id == current_user.id,
            TutorialProgress.tutorial_id == tutorial_id,
        )
        .first()
    )

    if not tutorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutorial progress not found",
        )

    return tutorial


@router.post("/tutorials", response_model=TutorialProgressResponse, status_code=status.HTTP_201_CREATED)
async def create_tutorial_progress(
    tutorial_data: TutorialProgressCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Start tracking a new tutorial."""
    existing = (
        db.query(TutorialProgress)
        .filter(
            TutorialProgress.user_id == current_user.id,
            TutorialProgress.tutorial_id == tutorial_data.tutorial_id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tutorial progress already exists",
        )

    tutorial = TutorialProgress(
        user_id=current_user.id,
        tutorial_id=tutorial_data.tutorial_id,
        total_steps=tutorial_data.total_steps,
    )
    db.add(tutorial)
    db.commit()
    db.refresh(tutorial)

    return tutorial


@router.patch("/tutorials/{tutorial_id}", response_model=TutorialProgressResponse)
async def update_tutorial_progress(
    tutorial_id: str,
    tutorial_data: TutorialProgressUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update tutorial progress."""
    tutorial = (
        db.query(TutorialProgress)
        .filter(
            TutorialProgress.user_id == current_user.id,
            TutorialProgress.tutorial_id == tutorial_id,
        )
        .first()
    )

    if not tutorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutorial progress not found",
        )

    # Update fields
    update_data = tutorial_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tutorial, field, value)

    # Update last viewed timestamp
    tutorial.last_viewed_at = datetime.now(timezone.utc)

    # Set completion timestamp if completed
    if tutorial_data.is_completed and tutorial.completed_at is None:
        tutorial.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(tutorial)

    return tutorial


@router.get("/preferences", response_model=UserPreferenceResponse)
async def get_user_preferences(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get user preferences."""
    preferences = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()

    if not preferences:
        # Create default preferences
        preferences = UserPreference(user_id=current_user.id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)

    return preferences


@router.post("/preferences", response_model=UserPreferenceResponse, status_code=status.HTTP_201_CREATED)
async def create_user_preferences(
    preference_data: UserPreferenceCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create user preferences."""
    existing = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User preferences already exist",
        )

    preferences = UserPreference(
        user_id=current_user.id,
        **preference_data.model_dump(),
    )
    db.add(preferences)
    db.commit()
    db.refresh(preferences)

    return preferences


@router.patch("/preferences", response_model=UserPreferenceResponse)
async def update_user_preferences(
    preference_data: UserPreferenceUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update user preferences."""
    preferences = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()

    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User preferences not found",
        )

    # Update fields
    update_data = preference_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)

    db.commit()
    db.refresh(preferences)

    return preferences


@router.get("/stats", response_model=OnboardingStatsResponse)
async def get_onboarding_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get onboarding statistics (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Total users with onboarding progress
    total_users = db.query(OnboardingProgress).count()

    # Completed users
    completed_users = db.query(OnboardingProgress).filter(OnboardingProgress.is_completed.is_(True)).count()

    # Completion rate
    completion_rate = (completed_users / total_users * 100) if total_users > 0 else 0

    # Average completion time
    avg_seconds = (
        db.query(
            func.avg(
                func.extract('epoch', OnboardingProgress.completed_at) - func.extract('epoch', OnboardingProgress.started_at)
            )
        )
        .filter(
            OnboardingProgress.is_completed.is_(True),
            OnboardingProgress.completed_at.isnot(None),
            OnboardingProgress.started_at.isnot(None),
        )
        .scalar()
    )
    avg_time = avg_seconds / 60 if avg_seconds is not None else None

    # Step completion rates
    step_fields = [
        "welcome_completed",
        "use_case_selected",
        "api_key_generated",
        "first_upload_completed",
        "dashboard_explored",
        "integration_started",
    ]

    step_completion_rates = {}
    for field in step_fields:
        completed = db.query(OnboardingProgress).filter(getattr(OnboardingProgress, field).is_(True)).count()
        step_completion_rates[field] = (completed / total_users * 100) if total_users > 0 else 0

    # Use case distribution
    use_case_counts = (
        db.query(OnboardingProgress.use_case, func.count(OnboardingProgress.id))
        .filter(OnboardingProgress.use_case.isnot(None))
        .group_by(OnboardingProgress.use_case)
        .all()
    )

    use_case_distribution = {use_case: count for use_case, count in use_case_counts}

    return OnboardingStatsResponse(
        total_users=total_users,
        completed_users=completed_users,
        completion_rate=completion_rate,
        avg_completion_time_minutes=avg_time,
        step_completion_rates=step_completion_rates,
        use_case_distribution=use_case_distribution,
    )
