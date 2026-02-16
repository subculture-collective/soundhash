"""Analytics and reporting models."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .auth import User
    from .tenant import Tenant


class AnalyticsEvent(Base):  # type: ignore[misc,valid-type]
    """Track analytics events for business intelligence."""

    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    # Event details
    event_type: Mapped[str] = mapped_column(String(100))  # 'page_view', 'api_call', 'upload', 'match', etc.
    event_category: Mapped[str] = mapped_column(String(100))  # 'user_action', 'api', 'system'
    event_name: Mapped[str] = mapped_column(String(200))
    
    # Context
    session_id: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    referrer: Mapped[str | None] = mapped_column(String(1000))
    
    # Properties
    properties: Mapped[dict | None] = mapped_column(JSON)  # Flexible event properties
    
    # Metrics
    duration_ms: Mapped[int | None] = mapped_column()  # For timed events
    value: Mapped[float | None] = mapped_column()
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class DashboardConfig(Base):  # type: ignore[misc,valid-type]
    """Custom dashboard configurations for users."""

    __tablename__ = "dashboard_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))

    # Config details
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    is_default: Mapped[bool] = mapped_column(default=False)
    
    # Layout configuration (JSON with widget positions and settings)
    layout: Mapped[dict] = mapped_column(JSON)
    
    # Sharing
    is_public: Mapped[bool] = mapped_column(default=False)
    share_token: Mapped[str | None] = mapped_column(String(255), unique=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_viewed_at: Mapped[datetime | None] = mapped_column()

    # Relationships
    user: Mapped["User"] = relationship("User")  # type: ignore[assignment]


class ReportConfig(Base):  # type: ignore[misc,valid-type]
    """Custom report configurations."""

    __tablename__ = "report_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))

    # Report details
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    report_type: Mapped[str] = mapped_column(String(50))  # 'usage', 'revenue', 'matches', 'api', 'custom'
    
    # Configuration
    filters: Mapped[dict | None] = mapped_column(JSON)  # Report filters
    metrics: Mapped[dict | None] = mapped_column(JSON)  # Metrics to include
    dimensions: Mapped[dict | None] = mapped_column(JSON)  # Grouping dimensions
    visualization_type: Mapped[str | None] = mapped_column(String(50))  # 'table', 'chart', 'both'
    
    # Export settings
    export_format: Mapped[str | None] = mapped_column(String(20))  # 'pdf', 'csv', 'excel'
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User")  # type: ignore[assignment]
    scheduled_reports: Mapped[list["ScheduledReport"]] = relationship("ScheduledReport", back_populates="report_config", cascade="all, delete-orphan")  # type: ignore[assignment]


class ScheduledReport(Base):  # type: ignore[misc,valid-type]
    """Scheduled report delivery."""

    __tablename__ = "scheduled_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_config_id: Mapped[int] = mapped_column(ForeignKey("report_configs.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Schedule settings
    is_active: Mapped[bool] = mapped_column(default=True)
    frequency: Mapped[str] = mapped_column(String(20))  # 'daily', 'weekly', 'monthly'
    day_of_week: Mapped[int | None] = mapped_column()  # 0-6 for weekly reports
    day_of_month: Mapped[int | None] = mapped_column()  # 1-31 for monthly reports
    time_of_day: Mapped[str | None] = mapped_column(String(5))  # HH:MM format
    timezone: Mapped[str | None] = mapped_column(String(50), default="UTC")
    
    # Delivery settings
    recipients: Mapped[dict] = mapped_column(JSON)  # List of email addresses
    subject_template: Mapped[str | None] = mapped_column(String(500))
    message_template: Mapped[str | None] = mapped_column(Text)
    
    # Execution tracking
    last_run_at: Mapped[datetime | None] = mapped_column()
    last_run_status: Mapped[str | None] = mapped_column(String(20))  # 'success', 'failed'
    last_run_error: Mapped[str | None] = mapped_column(Text)
    next_run_at: Mapped[datetime | None] = mapped_column()
    run_count: Mapped[int | None] = mapped_column(default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    report_config: Mapped["ReportConfig"] = relationship("ReportConfig", back_populates="scheduled_reports")  # type: ignore[assignment]
    user: Mapped["User"] = relationship("User")  # type: ignore[assignment]


class APIUsageLog(Base):  # type: ignore[misc,valid-type]
    """Detailed API usage logs for analytics."""

    __tablename__ = "api_usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    api_key_id: Mapped[int | None] = mapped_column(ForeignKey("api_keys.id"))

    # Request details
    endpoint: Mapped[str] = mapped_column(String(500))
    method: Mapped[str] = mapped_column(String(10))  # GET, POST, etc.
    path_params: Mapped[dict | None] = mapped_column(JSON)
    query_params: Mapped[dict | None] = mapped_column(JSON)
    
    # Response details
    status_code: Mapped[int] = mapped_column()
    response_time_ms: Mapped[int | None] = mapped_column()
    response_size_bytes: Mapped[int | None] = mapped_column()
    
    # Context
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    
    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text)
    error_type: Mapped[str | None] = mapped_column(String(100))
    
    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class UserJourney(Base):  # type: ignore[misc,valid-type]
    """Track user journeys for funnel analysis."""

    __tablename__ = "user_journeys"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    session_id: Mapped[str] = mapped_column(String(255))

    # Journey details
    journey_type: Mapped[str] = mapped_column(String(50))  # 'signup', 'upload', 'match', etc.
    current_step: Mapped[str] = mapped_column(String(100))
    is_completed: Mapped[bool] = mapped_column(default=False)
    
    # Steps tracking
    steps_completed: Mapped[dict | None] = mapped_column(JSON)  # List of completed steps
    total_steps: Mapped[int | None] = mapped_column()
    
    # Drop-off analysis
    dropped_off: Mapped[bool] = mapped_column(default=False)
    drop_off_step: Mapped[str | None] = mapped_column(String(100))
    drop_off_reason: Mapped[str | None] = mapped_column(String(200))
    
    # Extra data
    extra_data: Mapped[dict | None] = mapped_column(JSON)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column()
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CohortAnalysis(Base):  # type: ignore[misc,valid-type]
    """Pre-calculated cohort analysis data."""

    __tablename__ = "cohort_analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))

    # Cohort definition
    cohort_name: Mapped[str] = mapped_column(String(200))
    cohort_date: Mapped[datetime] = mapped_column()  # Date when cohort was created
    cohort_type: Mapped[str] = mapped_column(String(50))  # 'signup', 'first_upload', etc.
    
    # Metrics by period
    period_number: Mapped[int] = mapped_column()  # 0, 1, 2, ... (days/weeks/months after cohort_date)
    period_type: Mapped[str] = mapped_column(String(20))  # 'day', 'week', 'month'
    
    # Cohort metrics
    cohort_size: Mapped[int] = mapped_column()  # Initial size
    active_users: Mapped[int | None] = mapped_column()
    retention_rate: Mapped[float | None] = mapped_column()
    revenue: Mapped[float | None] = mapped_column()
    
    # Additional metrics
    metrics: Mapped[dict | None] = mapped_column(JSON)
    
    # Timestamps
    calculated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class RevenueMetric(Base):  # type: ignore[misc,valid-type]
    """Revenue analytics and forecasting data."""

    __tablename__ = "revenue_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))

    # Period
    period_type: Mapped[str] = mapped_column(String(20))  # 'daily', 'weekly', 'monthly'
    period_start: Mapped[datetime] = mapped_column()
    period_end: Mapped[datetime] = mapped_column()
    
    # Revenue metrics
    total_revenue: Mapped[float | None] = mapped_column(default=0.0)
    mrr: Mapped[float | None] = mapped_column()  # Monthly Recurring Revenue
    arr: Mapped[float | None] = mapped_column()  # Annual Recurring Revenue
    
    # Customer metrics
    new_customers: Mapped[int | None] = mapped_column(default=0)
    churned_customers: Mapped[int | None] = mapped_column(default=0)
    active_customers: Mapped[int | None] = mapped_column(default=0)
    
    # Growth metrics
    revenue_growth_rate: Mapped[float | None] = mapped_column()
    customer_growth_rate: Mapped[float | None] = mapped_column()
    churn_rate: Mapped[float | None] = mapped_column()
    
    # Forecasting
    forecasted_revenue: Mapped[float | None] = mapped_column()
    confidence_interval_lower: Mapped[float | None] = mapped_column()
    confidence_interval_upper: Mapped[float | None] = mapped_column()
    
    # Metadata
    metrics: Mapped[dict | None] = mapped_column(JSON)  # Additional custom metrics
    
    # Timestamps
    calculated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
