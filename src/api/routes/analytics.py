"""Analytics and Business Intelligence routes."""

import math
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, desc, func, text
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.api.models.common import PaginatedResponse, PaginationParams, SuccessResponse
from src.database.models import (
    APIUsageLog,
    AnalyticsEvent,
    CohortAnalysis,
    DashboardConfig,
    MatchResult,
    ReportConfig,
    RevenueMetric,
    ScheduledReport,
    User,
    UserJourney,
    Video,
)

router = APIRouter()


@router.post("/events")
async def track_event(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    event_type: str,
    event_category: str,
    event_name: str,
    properties: dict[str, Any] | None = None,
    duration_ms: int | None = None,
    value: float | None = None,
):
    """Track an analytics event."""
    event = AnalyticsEvent(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        event_type=event_type,
        event_category=event_category,
        event_name=event_name,
        properties=properties or {},
        duration_ms=duration_ms,
        value=value,
    )
    db.add(event)
    db.commit()
    
    return SuccessResponse(message="Event tracked successfully", data={"event_id": event.id})


@router.get("/overview")
async def get_analytics_overview(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
):
    """Get analytics overview with key metrics."""
    # Default to last 30 days
    if not end_date:
        end_date = datetime.now(UTC)
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Build base query filters
    filters = [AnalyticsEvent.created_at >= start_date, AnalyticsEvent.created_at <= end_date]
    
    if not current_user.is_admin:
        filters.append(AnalyticsEvent.user_id == current_user.id)
    elif current_user.tenant_id:
        filters.append(AnalyticsEvent.tenant_id == current_user.tenant_id)
    
    # Total events
    total_events = db.query(func.count(AnalyticsEvent.id)).filter(and_(*filters)).scalar() or 0
    
    # Events by category
    events_by_category = (
        db.query(AnalyticsEvent.event_category, func.count(AnalyticsEvent.id))
        .filter(and_(*filters))
        .group_by(AnalyticsEvent.event_category)
        .all()
    )
    
    # Active users
    active_users = (
        db.query(func.count(func.distinct(AnalyticsEvent.user_id)))
        .filter(and_(*filters))
        .scalar() or 0
    )
    
    # API calls
    api_filters = [APIUsageLog.timestamp >= start_date, APIUsageLog.timestamp <= end_date]
    if not current_user.is_admin:
        api_filters.append(APIUsageLog.user_id == current_user.id)
    elif current_user.tenant_id:
        api_filters.append(APIUsageLog.tenant_id == current_user.tenant_id)
    
    total_api_calls = db.query(func.count(APIUsageLog.id)).filter(and_(*api_filters)).scalar() or 0
    
    avg_response_time = (
        db.query(func.avg(APIUsageLog.response_time_ms))
        .filter(and_(*api_filters))
        .scalar() or 0
    )
    
    # Error rate
    error_count = (
        db.query(func.count(APIUsageLog.id))
        .filter(and_(*api_filters), APIUsageLog.status_code >= 400)
        .scalar() or 0
    )
    error_rate = (error_count / total_api_calls * 100) if total_api_calls > 0 else 0
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "metrics": {
            "total_events": total_events,
            "active_users": active_users,
            "api_calls": total_api_calls,
            "avg_response_time_ms": round(avg_response_time, 2),
            "error_rate": round(error_rate, 2),
        },
        "events_by_category": {cat: count for cat, count in events_by_category},
    }


@router.get("/api-usage")
async def get_api_usage_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    group_by: str = Query("day", regex="^(hour|day|week|month)$"),
):
    """Get API usage statistics grouped by time period."""
    if not end_date:
        end_date = datetime.now(UTC)
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Build filters
    filters = [APIUsageLog.timestamp >= start_date, APIUsageLog.timestamp <= end_date]
    if not current_user.is_admin:
        filters.append(APIUsageLog.user_id == current_user.id)
    elif current_user.tenant_id:
        filters.append(APIUsageLog.tenant_id == current_user.tenant_id)
    
    # Time grouping format
    date_trunc_format = {
        "hour": "hour",
        "day": "day",
        "week": "week",
        "month": "month",
    }[group_by]
    
    # Query usage over time
    usage_over_time = (
        db.query(
            func.date_trunc(date_trunc_format, APIUsageLog.timestamp).label("period"),
            func.count(APIUsageLog.id).label("count"),
            func.avg(APIUsageLog.response_time_ms).label("avg_response_time"),
        )
        .filter(and_(*filters))
        .group_by(text("period"))
        .order_by(text("period"))
        .all()
    )
    
    # Top endpoints
    top_endpoints = (
        db.query(
            APIUsageLog.endpoint,
            func.count(APIUsageLog.id).label("count"),
            func.avg(APIUsageLog.response_time_ms).label("avg_response_time"),
        )
        .filter(and_(*filters))
        .group_by(APIUsageLog.endpoint)
        .order_by(desc(text("count")))
        .limit(10)
        .all()
    )
    
    # Status code distribution
    status_distribution = (
        db.query(APIUsageLog.status_code, func.count(APIUsageLog.id))
        .filter(and_(*filters))
        .group_by(APIUsageLog.status_code)
        .all()
    )
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "group_by": group_by,
        },
        "usage_over_time": [
            {
                "period": row.period.isoformat(),
                "count": row.count,
                "avg_response_time_ms": round(row.avg_response_time, 2) if row.avg_response_time else 0,
            }
            for row in usage_over_time
        ],
        "top_endpoints": [
            {
                "endpoint": row.endpoint,
                "count": row.count,
                "avg_response_time_ms": round(row.avg_response_time, 2) if row.avg_response_time else 0,
            }
            for row in top_endpoints
        ],
        "status_distribution": {str(code): count for code, count in status_distribution},
    }


@router.get("/funnel")
async def get_funnel_analysis(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    journey_type: str = Query(...),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
):
    """Get funnel analysis for user journeys."""
    if not end_date:
        end_date = datetime.now(UTC)
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    filters = [
        UserJourney.journey_type == journey_type,
        UserJourney.started_at >= start_date,
        UserJourney.started_at <= end_date,
    ]
    
    if not current_user.is_admin:
        filters.append(UserJourney.user_id == current_user.id)
    
    # Total started
    total_started = db.query(func.count(UserJourney.id)).filter(and_(*filters)).scalar() or 0
    
    # Completed
    completed = (
        db.query(func.count(UserJourney.id))
        .filter(and_(*filters), UserJourney.is_completed == True)
        .scalar() or 0
    )
    
    # Dropped off
    dropped_off = (
        db.query(func.count(UserJourney.id))
        .filter(and_(*filters), UserJourney.dropped_off == True)
        .scalar() or 0
    )
    
    # Drop-off by step
    drop_off_by_step = (
        db.query(UserJourney.drop_off_step, func.count(UserJourney.id))
        .filter(and_(*filters), UserJourney.dropped_off == True)
        .group_by(UserJourney.drop_off_step)
        .all()
    )
    
    conversion_rate = (completed / total_started * 100) if total_started > 0 else 0
    
    return {
        "journey_type": journey_type,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "metrics": {
            "total_started": total_started,
            "completed": completed,
            "dropped_off": dropped_off,
            "in_progress": total_started - completed - dropped_off,
            "conversion_rate": round(conversion_rate, 2),
        },
        "drop_off_by_step": {step: count for step, count in drop_off_by_step if step},
    }


@router.get("/cohorts")
async def get_cohort_analysis(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    cohort_type: str = Query("signup"),
    period_type: str = Query("week", regex="^(day|week|month)$"),
):
    """Get cohort analysis data."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for cohort analysis",
        )
    
    filters = [CohortAnalysis.cohort_type == cohort_type, CohortAnalysis.period_type == period_type]
    
    if current_user.tenant_id:
        filters.append(CohortAnalysis.tenant_id == current_user.tenant_id)
    
    cohorts = (
        db.query(CohortAnalysis)
        .filter(and_(*filters))
        .order_by(CohortAnalysis.cohort_date, CohortAnalysis.period_number)
        .all()
    )
    
    # Group by cohort
    cohort_data = {}
    for cohort in cohorts:
        cohort_key = cohort.cohort_date.strftime("%Y-%m-%d")
        if cohort_key not in cohort_data:
            cohort_data[cohort_key] = {
                "cohort_date": cohort_key,
                "cohort_size": cohort.cohort_size,
                "periods": [],
            }
        
        cohort_data[cohort_key]["periods"].append({
            "period": cohort.period_number,
            "active_users": cohort.active_users,
            "retention_rate": round(cohort.retention_rate, 2) if cohort.retention_rate else 0,
            "revenue": cohort.revenue,
        })
    
    return {
        "cohort_type": cohort_type,
        "period_type": period_type,
        "cohorts": list(cohort_data.values()),
    }


@router.get("/revenue")
async def get_revenue_analytics(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    period_type: str = Query("monthly", regex="^(daily|weekly|monthly)$"),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
):
    """Get revenue analytics and forecasting."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for revenue analytics",
        )
    
    if not end_date:
        end_date = datetime.now(UTC)
    if not start_date:
        start_date = end_date - timedelta(days=365)
    
    filters = [
        RevenueMetric.period_type == period_type,
        RevenueMetric.period_start >= start_date,
        RevenueMetric.period_end <= end_date,
    ]
    
    if current_user.tenant_id:
        filters.append(RevenueMetric.tenant_id == current_user.tenant_id)
    
    metrics = (
        db.query(RevenueMetric)
        .filter(and_(*filters))
        .order_by(RevenueMetric.period_start)
        .all()
    )
    
    # Calculate summary
    total_revenue = sum(m.total_revenue for m in metrics if m.total_revenue)
    avg_mrr = sum(m.mrr for m in metrics if m.mrr) / len(metrics) if metrics else 0
    avg_arr = sum(m.arr for m in metrics if m.arr) / len(metrics) if metrics else 0
    
    return {
        "period_type": period_type,
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "avg_mrr": round(avg_mrr, 2),
            "avg_arr": round(avg_arr, 2),
        },
        "periods": [
            {
                "period_start": m.period_start.isoformat(),
                "period_end": m.period_end.isoformat(),
                "total_revenue": m.total_revenue,
                "mrr": m.mrr,
                "arr": m.arr,
                "new_customers": m.new_customers,
                "churned_customers": m.churned_customers,
                "active_customers": m.active_customers,
                "revenue_growth_rate": round(m.revenue_growth_rate, 2) if m.revenue_growth_rate else 0,
                "churn_rate": round(m.churn_rate, 2) if m.churn_rate else 0,
                "forecasted_revenue": m.forecasted_revenue,
            }
            for m in metrics
        ],
    }


# Dashboard configuration endpoints
@router.post("/dashboards", response_model=SuccessResponse)
async def create_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    name: str,
    description: str | None = None,
    layout: dict[str, Any] = {},
    is_default: bool = False,
):
    """Create a custom dashboard configuration."""
    # If setting as default, unset other defaults
    if is_default:
        db.query(DashboardConfig).filter(
            DashboardConfig.user_id == current_user.id,
            DashboardConfig.is_default == True,
        ).update({"is_default": False})
    
    dashboard = DashboardConfig(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        name=name,
        description=description,
        layout=layout,
        is_default=is_default,
    )
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)
    
    return SuccessResponse(
        message="Dashboard created successfully",
        data={"dashboard_id": dashboard.id},
    )


@router.get("/dashboards", response_model=PaginatedResponse[dict])
async def list_dashboards(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    pagination: PaginationParams = Depends(),
):
    """List user's custom dashboards."""
    query = db.query(DashboardConfig).filter(DashboardConfig.user_id == current_user.id)
    query = query.order_by(desc(DashboardConfig.is_default), desc(DashboardConfig.created_at))
    
    total = query.count()
    offset = (pagination.page - 1) * pagination.per_page
    dashboards = query.offset(offset).limit(pagination.per_page).all()
    
    return PaginatedResponse(
        data=[
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "is_default": d.is_default,
                "is_public": d.is_public,
                "created_at": d.created_at.isoformat(),
                "updated_at": d.updated_at.isoformat(),
            }
            for d in dashboards
        ],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        pages=math.ceil(total / pagination.per_page) if total > 0 else 0,
    )


@router.get("/dashboards/{dashboard_id}")
async def get_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    dashboard_id: int,
):
    """Get a specific dashboard configuration."""
    dashboard = db.query(DashboardConfig).filter(DashboardConfig.id == dashboard_id).first()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    # Check permissions
    if dashboard.user_id != current_user.id and not dashboard.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": dashboard.id,
        "name": dashboard.name,
        "description": dashboard.description,
        "layout": dashboard.layout,
        "is_default": dashboard.is_default,
        "is_public": dashboard.is_public,
        "created_at": dashboard.created_at.isoformat(),
        "updated_at": dashboard.updated_at.isoformat(),
    }


@router.put("/dashboards/{dashboard_id}")
async def update_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    dashboard_id: int,
    name: str | None = None,
    description: str | None = None,
    layout: dict[str, Any] | None = None,
    is_default: bool | None = None,
):
    """Update a dashboard configuration."""
    dashboard = db.query(DashboardConfig).filter(
        DashboardConfig.id == dashboard_id,
        DashboardConfig.user_id == current_user.id,
    ).first()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    if name is not None:
        dashboard.name = name
    if description is not None:
        dashboard.description = description
    if layout is not None:
        dashboard.layout = layout
    if is_default is not None:
        if is_default:
            # Unset other defaults
            db.query(DashboardConfig).filter(
                DashboardConfig.user_id == current_user.id,
                DashboardConfig.id != dashboard_id,
                DashboardConfig.is_default == True,
            ).update({"is_default": False})
        dashboard.is_default = is_default
    
    db.commit()
    
    return SuccessResponse(message="Dashboard updated successfully")


@router.delete("/dashboards/{dashboard_id}")
async def delete_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    dashboard_id: int,
):
    """Delete a dashboard configuration."""
    dashboard = db.query(DashboardConfig).filter(
        DashboardConfig.id == dashboard_id,
        DashboardConfig.user_id == current_user.id,
    ).first()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    db.delete(dashboard)
    db.commit()
    
    return SuccessResponse(message="Dashboard deleted successfully")


# Report configuration endpoints
@router.post("/reports", response_model=SuccessResponse)
async def create_report(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    name: str,
    report_type: str,
    description: str | None = None,
    filters: dict[str, Any] | None = None,
    metrics: list[str] | None = None,
    dimensions: list[str] | None = None,
    visualization_type: str = "both",
    export_format: str = "pdf",
):
    """Create a custom report configuration."""
    report = ReportConfig(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        name=name,
        description=description,
        report_type=report_type,
        filters=filters or {},
        metrics=metrics or [],
        dimensions=dimensions or [],
        visualization_type=visualization_type,
        export_format=export_format,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return SuccessResponse(
        message="Report configuration created successfully",
        data={"report_id": report.id},
    )


@router.get("/reports", response_model=PaginatedResponse[dict])
async def list_reports(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    pagination: PaginationParams = Depends(),
):
    """List user's report configurations."""
    query = db.query(ReportConfig).filter(ReportConfig.user_id == current_user.id)
    query = query.order_by(desc(ReportConfig.created_at))
    
    total = query.count()
    offset = (pagination.page - 1) * pagination.per_page
    reports = query.offset(offset).limit(pagination.per_page).all()
    
    return PaginatedResponse(
        data=[
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "report_type": r.report_type,
                "export_format": r.export_format,
                "created_at": r.created_at.isoformat(),
            }
            for r in reports
        ],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        pages=math.ceil(total / pagination.per_page) if total > 0 else 0,
    )


@router.get("/reports/{report_id}/generate")
async def generate_report(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    report_id: int,
    format: str = Query("json", regex="^(json|csv|pdf|excel)$"),
):
    """Generate a report based on configuration."""
    report = db.query(ReportConfig).filter(
        ReportConfig.id == report_id,
        ReportConfig.user_id == current_user.id,
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # TODO: Implement actual report generation logic
    # For now, return placeholder data
    return {
        "report_id": report.id,
        "name": report.name,
        "report_type": report.report_type,
        "generated_at": datetime.now(UTC).isoformat(),
        "format": format,
        "data": {
            "message": "Report generation not yet implemented",
        },
    }
