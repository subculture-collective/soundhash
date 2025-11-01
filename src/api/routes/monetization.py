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
    file_url: Optional[str] = None
    version: Optional[str] = None
    license_type: Optional[str] = None


class MarketplaceReviewRequest(BaseModel):
    """Request to create a review."""

    rating: int = Field(ge=1, le=5)
    title: Optional[str] = None
    review_text: Optional[str] = None


class MarketplaceVersionRequest(BaseModel):
    """Request to create a new version."""

    version_number: str
    file_url: str
    release_notes: Optional[str] = None
    changelog: Optional[dict] = None


class MarketplaceSearchRequest(BaseModel):
    """Request to search marketplace items."""

    query: Optional[str] = None
    item_type: Optional[str] = None
    category: Optional[str] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    tags: Optional[List[str]] = None
    sort_by: str = "relevance"
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


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


@router.post("/marketplace/items/{item_id}/reviews")
async def create_review(
    item_id: int,
    request: MarketplaceReviewRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a review for a marketplace item."""
    try:
        session = db_manager.get_session()
        try:
            review = MarketplaceService.create_review(
                session=session,
                marketplace_item_id=item_id,
                user_id=current_user.id,
                rating=request.rating,
                title=request.title,
                review_text=request.review_text,
            )

            return {
                "id": review.id,
                "rating": review.rating,
                "title": review.title,
                "is_verified_purchase": review.is_verified_purchase,
                "created_at": review.created_at.isoformat() if review.created_at else None,
            }
        finally:
            session.close()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/marketplace/items/{item_id}/reviews")
async def get_item_reviews(
    item_id: int,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Get reviews for a marketplace item."""
    try:
        session = db_manager.get_session()
        try:
            reviews = MarketplaceService.get_item_reviews(
                session, item_id, limit=limit, offset=offset
            )
            return {"reviews": reviews, "limit": limit, "offset": offset}
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error fetching reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketplace/items/{item_id}/versions")
async def create_item_version(
    item_id: int,
    request: MarketplaceVersionRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a new version for a marketplace item."""
    try:
        session = db_manager.get_session()
        try:
            # Verify user owns the item
            from src.database.models import MarketplaceItem

            item = session.query(MarketplaceItem).filter_by(id=item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            if item.seller_user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized")

            version = MarketplaceService.create_item_version(
                session=session,
                marketplace_item_id=item_id,
                version_number=request.version_number,
                file_url=request.file_url,
                release_notes=request.release_notes,
                changelog=request.changelog,
            )

            return {
                "id": version.id,
                "version_number": version.version_number,
                "file_url": version.file_url,
                "is_latest": version.is_latest,
                "created_at": version.created_at.isoformat() if version.created_at else None,
            }
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketplace/search")
async def search_marketplace(request: MarketplaceSearchRequest):
    """Search marketplace items with advanced filtering."""
    try:
        session = db_manager.get_session()
        try:
            results = MarketplaceService.search_items(
                session=session,
                query=request.query,
                item_type=request.item_type,
                category=request.category,
                min_rating=request.min_rating,
                tags=request.tags,
                sort_by=request.sort_by,
                limit=request.limit,
                offset=request.offset,
            )
            return results
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error searching marketplace: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/marketplace/seller/analytics")
async def get_seller_analytics(current_user: User = Depends(get_current_user)):
    """Get comprehensive analytics for seller."""
    try:
        session = db_manager.get_session()
        try:
            analytics = MarketplaceService.get_seller_analytics(
                session, current_user.id
            )
            return analytics
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error fetching seller analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketplace/seller/stripe-connect")
async def setup_stripe_connect(
    stripe_account_id: str, current_user: User = Depends(get_current_user)
):
    """Set up Stripe Connect for seller payouts."""
    try:
        session = db_manager.get_session()
        try:
            account = MarketplaceService.setup_stripe_connect(
                session=session,
                user_id=current_user.id,
                stripe_account_id=stripe_account_id,
            )

            return {
                "stripe_account_id": account.stripe_account_id,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "details_submitted": account.details_submitted,
            }
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error setting up Stripe Connect: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketplace/seller/payout")
async def process_seller_payout(current_user: User = Depends(get_current_user)):
    """Process payout for seller via Stripe Connect."""
    try:
        session = db_manager.get_session()
        try:
            result = MarketplaceService.process_payout(
                session, current_user.id
            )
            return result
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error processing payout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketplace/items/{item_id}/quality-check")
async def run_quality_check(
    item_id: int,
    check_type: str = "security_scan",
    current_user: User = Depends(get_current_user),
):
    """Run quality check on a marketplace item."""
    try:
        session = db_manager.get_session()
        try:
            # Verify user owns the item or is admin
            from src.database.models import MarketplaceItem

            item = session.query(MarketplaceItem).filter_by(id=item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            if item.seller_user_id != current_user.id and not current_user.is_admin:
                raise HTTPException(status_code=403, detail="Not authorized")

            check = MarketplaceService.run_quality_check(
                session=session,
                marketplace_item_id=item_id,
                check_type=check_type,
            )

            return {
                "id": check.id,
                "check_type": check.check_type,
                "status": check.status,
                "result_summary": check.result_summary,
                "issues_found": check.issues_found,
            }
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running quality check: {e}")
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
    if not current_user.is_admin:
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
