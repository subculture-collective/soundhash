"""Monetization API endpoints for affiliates, referrals, and revenue sharing."""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.dependencies import get_current_user
from src.database.connection import db_manager
from src.database.models import User
from src.monetization.affiliate_service import AffiliateService
from src.monetization.campaign_service import CampaignService
from src.monetization.marketplace_service import MarketplaceService
from src.monetization.referral_service import ReferralService
from src.monetization.revenue_service import RevenueService
from src.monetization.rewards_service import RewardsService

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Request/Response Models ====================


class AffiliateCreateRequest(BaseModel):
    """Request to create an affiliate program."""

    affiliate_name: str
    company_name: Optional[str] = None
    website: Optional[str] = None
    commission_rate: float = Field(default=0.20, ge=0, le=1)
    commission_duration_months: int = Field(default=3, ge=1, le=12)


class ReferralCodeResponse(BaseModel):
    """Response with referral code."""

    referral_code: str
    expires_at: Optional[str] = None


class MarketplaceItemRequest(BaseModel):
    """Request to create marketplace item."""

    item_type: str
    title: str
    description: str
    price: int = Field(gt=0)
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class CampaignCreateRequest(BaseModel):
    """Request to create a campaign."""

    name: str
    campaign_type: str
    offer_type: str
    start_date: datetime
    end_date: datetime
    discount_percentage: Optional[float] = None
    credit_amount: Optional[int] = None
    max_uses: Optional[int] = None


# ==================== Affiliate Endpoints ====================


@router.post("/affiliates")
async def create_affiliate(
    request: AffiliateCreateRequest, current_user: User = Depends(get_current_user)
):
    """Apply to become an affiliate partner."""
    try:
        session = db_manager.get_session()
        try:
            affiliate = AffiliateService.create_affiliate(
                session=session,
                user_id=current_user.id,
                affiliate_name=request.affiliate_name,
                company_name=request.company_name,
                website=request.website,
                commission_rate=request.commission_rate,
                commission_duration_months=request.commission_duration_months,
            )

            return {
                "id": affiliate.id,
                "affiliate_code": affiliate.affiliate_code,
                "status": affiliate.status,
                "commission_rate": affiliate.commission_rate,
                "message": "Affiliate application submitted. Pending approval.",
            }
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error creating affiliate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/affiliates/dashboard")
async def get_affiliate_dashboard(current_user: User = Depends(get_current_user)):
    """Get affiliate dashboard with earnings and performance metrics."""
    try:
        session = db_manager.get_session()
        try:
            # Find user's affiliate program
            from src.database.models import AffiliateProgram

            affiliate = (
                session.query(AffiliateProgram)
                .filter_by(user_id=current_user.id)
                .first()
            )

            if not affiliate:
                raise HTTPException(
                    status_code=404, detail="No affiliate program found for this user"
                )

            dashboard_data = AffiliateService.get_dashboard_data(
                session, affiliate.id
            )
            return dashboard_data

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching affiliate dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Referral Endpoints ====================


@router.get("/referrals/code")
async def get_referral_code(current_user: User = Depends(get_current_user)):
    """Get user's referral code."""
    referral_code = ReferralService.generate_referral_code(current_user.id)
    return ReferralCodeResponse(referral_code=referral_code)


@router.get("/referrals/stats")
async def get_referral_stats(current_user: User = Depends(get_current_user)):
    """Get user's referral statistics and rewards."""
    try:
        session = db_manager.get_session()
        try:
            stats = ReferralService.get_user_referrals(session, current_user.id)
            return stats
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error fetching referral stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/referrals/balance")
async def get_credit_balance(current_user: User = Depends(get_current_user)):
    """Get user's current API credit balance."""
    try:
        session = db_manager.get_session()
        try:
            balance = ReferralService.get_user_balance(session, current_user.id)
            return {"credit_balance": balance}
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error fetching credit balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Creator Revenue Endpoints ====================


@router.get("/revenue/creator")
async def get_creator_earnings(current_user: User = Depends(get_current_user)):
    """Get content creator earnings summary."""
    try:
        session = db_manager.get_session()
        try:
            earnings = RevenueService.get_creator_earnings(session, current_user.id)
            return earnings
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error fetching creator earnings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Marketplace Endpoints ====================


@router.post("/marketplace/items")
async def create_marketplace_item(
    request: MarketplaceItemRequest, current_user: User = Depends(get_current_user)
):
    """Create a new marketplace item."""
    try:
        session = db_manager.get_session()
        try:
            item = MarketplaceService.create_marketplace_item(
                session=session,
                seller_user_id=current_user.id,
                item_type=request.item_type,
                title=request.title,
                description=request.description,
                price=request.price,
                category=request.category,
                tags=request.tags,
            )

            return {
                "id": item.id,
                "title": item.title,
                "status": item.status,
                "price": item.price,
            }
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error creating marketplace item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/marketplace/items")
async def list_marketplace_items(
    item_type: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(default=20, le=100),
):
    """List marketplace items."""
    try:
        session = db_manager.get_session()
        try:
            from src.database.models import MarketplaceItem

            query = session.query(MarketplaceItem).filter_by(status="active")

            if item_type:
                query = query.filter_by(item_type=item_type)
            if category:
                query = query.filter_by(category=category)

            items = query.limit(limit).all()

            return {
                "items": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "description": item.description,
                        "item_type": item.item_type,
                        "category": item.category,
                        "price": item.price,
                        "purchase_count": item.purchase_count,
                        "average_rating": item.average_rating,
                    }
                    for item in items
                ]
            }
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error listing marketplace items: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketplace/items/{item_id}/purchase")
async def purchase_marketplace_item(
    item_id: int, current_user: User = Depends(get_current_user)
):
    """Purchase a marketplace item."""
    try:
        session = db_manager.get_session()
        try:
            transaction = MarketplaceService.purchase_item(
                session=session,
                item_id=item_id,
                buyer_user_id=current_user.id,
            )

            return {
                "transaction_id": transaction.id,
                "license_key": transaction.license_key,
                "download_url": transaction.download_url,
                "download_expires_at": (
                    transaction.download_expires_at.isoformat()
                    if transaction.download_expires_at
                    else None
                ),
            }
        finally:
            session.close()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error purchasing marketplace item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/marketplace/seller/earnings")
async def get_seller_earnings(current_user: User = Depends(get_current_user)):
    """Get marketplace seller earnings."""
    try:
        session = db_manager.get_session()
        try:
            earnings = MarketplaceService.get_seller_earnings(
                session, current_user.id
            )
            return earnings
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error fetching seller earnings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Rewards & Gamification Endpoints ====================


@router.get("/rewards/badges")
async def get_user_badges(current_user: User = Depends(get_current_user)):
    """Get user's earned badges."""
    try:
        session = db_manager.get_session()
        try:
            from src.database.models import UserBadge

            badges = (
                session.query(UserBadge)
                .filter_by(user_id=current_user.id)
                .order_by(UserBadge.earned_at.desc())
                .all()
            )

            return {
                "badges": [
                    {
                        "badge_id": badge.badge_id,
                        "badge_name": badge.badge_name,
                        "badge_description": badge.badge_description,
                        "badge_tier": badge.badge_tier,
                        "earned_at": (
                            badge.earned_at.isoformat() if badge.earned_at else None
                        ),
                    }
                    for badge in badges
                ]
            }
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error fetching user badges: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rewards/leaderboard")
async def get_leaderboard(
    category: str = Query(default="referrals"),
    period: str = Query(default="monthly"),
    limit: int = Query(default=100, le=100),
):
    """Get leaderboard for a category and time period."""
    try:
        session = db_manager.get_session()
        try:
            leaderboard = RewardsService.get_leaderboard(
                session, category, period, limit
            )
            return {"leaderboard": leaderboard}
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error fetching leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Campaign Endpoints ====================


@router.post("/campaigns")
async def create_campaign(
    request: CampaignCreateRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a promotional campaign (admin only)."""
    if not (current_user.is_admin and current_user.is_active):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        session = db_manager.get_session()
        try:
            campaign = CampaignService.create_campaign(
                session=session,
                created_by=current_user.id,
                name=request.name,
                campaign_type=request.campaign_type,
                offer_type=request.offer_type,
                start_date=request.start_date,
                end_date=request.end_date,
                discount_percentage=request.discount_percentage,
                credit_amount=request.credit_amount,
                max_uses=request.max_uses,
            )

            return {
                "id": campaign.id,
                "campaign_code": campaign.campaign_code,
                "name": campaign.name,
                "status": campaign.status,
            }
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns/{campaign_code}")
async def get_campaign(campaign_code: str):
    """Get campaign details by code."""
    try:
        session = db_manager.get_session()
        try:
            campaign = CampaignService.get_campaign_by_code(session, campaign_code)

            if not campaign:
                raise HTTPException(status_code=404, detail="Campaign not found")

            return {
                "campaign_code": campaign.campaign_code,
                "name": campaign.name,
                "campaign_type": campaign.campaign_type,
                "offer_type": campaign.offer_type,
                "discount_percentage": campaign.discount_percentage,
                "credit_amount": campaign.credit_amount,
                "is_active": campaign.is_active,
                "status": campaign.status,
                "start_date": (
                    campaign.start_date.isoformat() if campaign.start_date else None
                ),
                "end_date": (
                    campaign.end_date.isoformat() if campaign.end_date else None
                ),
            }
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns")
async def list_active_campaigns():
    """List all active campaigns."""
    try:
        session = db_manager.get_session()
        try:
            campaigns = CampaignService.get_active_campaigns(session)

            return {
                "campaigns": [
                    {
                        "campaign_code": c.campaign_code,
                        "name": c.name,
                        "offer_type": c.offer_type,
                        "discount_percentage": c.discount_percentage,
                        "credit_amount": c.credit_amount,
                    }
                    for c in campaigns
                ]
            }
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))
