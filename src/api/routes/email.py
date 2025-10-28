"""Email management API routes."""

import secrets
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.api.models.auth import UserResponse
from src.api.models.email import (
    EmailCampaignCreate,
    EmailCampaignResponse,
    EmailLogResponse,
    EmailPreferenceResponse,
    EmailPreferenceUpdate,
    UnsubscribeRequest,
    UnsubscribeResponse,
)
from src.database.models import EmailCampaign, EmailLog, EmailPreference, User

router = APIRouter(prefix="/email", tags=["email"])


@router.get("/preferences", response_model=EmailPreferenceResponse)
async def get_email_preferences(
    current_user: UserResponse = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get current user's email preferences."""
    preference = db.query(EmailPreference).filter_by(user_id=current_user.id).first()

    if not preference:
        # Create default preferences
        preference = EmailPreference(user_id=current_user.id)
        db.add(preference)
        db.commit()
        db.refresh(preference)

    return preference


@router.put("/preferences", response_model=EmailPreferenceResponse)
async def update_email_preferences(
    updates: EmailPreferenceUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update email preferences."""
    preference = db.query(EmailPreference).filter_by(user_id=current_user.id).first()

    if not preference:
        preference = EmailPreference(user_id=current_user.id)
        db.add(preference)

    # Update provided fields
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preference, field, value)

    preference.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(preference)

    return preference


@router.post("/unsubscribe", response_model=UnsubscribeResponse)
async def unsubscribe_from_emails(
    request: UnsubscribeRequest, db: Session = Depends(get_db)
):
    """Unsubscribe from all marketing emails."""
    # Find user by email
    user = db.query(User).filter_by(email=request.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Email not found"
        )

    # Get or create preferences
    preference = db.query(EmailPreference).filter_by(user_id=user.id).first()

    if not preference:
        preference = EmailPreference(user_id=user.id)
        db.add(preference)

    # Verify token if provided
    if request.token and preference.unsubscribe_token != request.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid unsubscribe token"
        )

    # Mark as unsubscribed
    preference.unsubscribed_at = datetime.utcnow()
    if not preference.unsubscribe_token:
        preference.unsubscribe_token = secrets.token_urlsafe(32)

    db.commit()

    return UnsubscribeResponse(
        success=True, message="Successfully unsubscribed from all marketing emails"
    )


@router.post("/resubscribe", response_model=UnsubscribeResponse)
async def resubscribe_to_emails(
    current_user: UserResponse = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Resubscribe to marketing emails."""
    preference = db.query(EmailPreference).filter_by(user_id=current_user.id).first()

    if not preference:
        return UnsubscribeResponse(
            success=True, message="You are already subscribed to emails"
        )

    preference.unsubscribed_at = None
    db.commit()

    return UnsubscribeResponse(success=True, message="Successfully resubscribed to emails")


@router.get("/logs", response_model=List[EmailLogResponse])
async def get_email_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get email logs for current user."""
    query = db.query(EmailLog).filter_by(user_id=current_user.id)

    if category:
        query = query.filter_by(category=category)

    logs = query.order_by(EmailLog.created_at.desc()).offset(skip).limit(limit).all()

    return logs


@router.get("/campaigns", response_model=List[EmailCampaignResponse])
async def list_email_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List email campaigns (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    query = db.query(EmailCampaign)

    if status:
        query = query.filter_by(status=status)

    campaigns = query.order_by(EmailCampaign.created_at.desc()).offset(skip).limit(limit).all()

    return campaigns


@router.post("/campaigns", response_model=EmailCampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_email_campaign(
    campaign: EmailCampaignCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new email campaign (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    db_campaign = EmailCampaign(**campaign.model_dump())
    db_campaign.status = "draft"

    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)

    return db_campaign


@router.get("/campaigns/{campaign_id}", response_model=EmailCampaignResponse)
async def get_email_campaign(
    campaign_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get email campaign details (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    campaign = db.query(EmailCampaign).filter_by(id=campaign_id).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )

    return campaign


@router.get("/tracking/open/{email_log_id}")
async def track_email_open(email_log_id: int, db: Session = Depends(get_db)):
    """Track email open event (typically called via tracking pixel)."""
    from src.email.service import email_service

    success = await email_service.track_email_open(email_log_id)

    if success:
        # Return 1x1 transparent GIF
        from fastapi.responses import Response

        gif_data = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00"
            b"\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00"
            b"\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02"
            b"\x44\x01\x00\x3b"
        )
        return Response(content=gif_data, media_type="image/gif")

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.get("/tracking/click/{email_log_id}")
async def track_email_click(
    email_log_id: int, redirect_url: str = Query(...), db: Session = Depends(get_db)
):
    """Track email click event and redirect."""
    from src.email.service import email_service
    from fastapi.responses import RedirectResponse

    await email_service.track_email_click(email_log_id)

    return RedirectResponse(url=redirect_url)
