"""Tests for analytics endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_track_event(client: TestClient, auth_headers: dict):
    """Test tracking an analytics event."""
    response = client.post(
        "/api/v1/analytics/events",
        headers=auth_headers,
        params={
            "event_type": "page_view",
            "event_category": "user_action",
            "event_name": "view_dashboard",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "event_id" in data["data"]


def test_get_analytics_overview(client: TestClient, auth_headers: dict):
    """Test getting analytics overview."""
    response = client.get("/api/v1/analytics/overview", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "period" in data
    assert "metrics" in data
    assert "total_events" in data["metrics"]
    assert "active_users" in data["metrics"]
    assert "api_calls" in data["metrics"]


def test_get_api_usage_stats(client: TestClient, auth_headers: dict):
    """Test getting API usage statistics."""
    response = client.get(
        "/api/v1/analytics/api-usage",
        headers=auth_headers,
        params={"group_by": "day"},
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "period" in data
    assert "usage_over_time" in data
    assert "top_endpoints" in data
    assert "status_distribution" in data


def test_get_funnel_analysis(client: TestClient, auth_headers: dict):
    """Test getting funnel analysis."""
    response = client.get(
        "/api/v1/analytics/funnel",
        headers=auth_headers,
        params={"journey_type": "signup"},
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["journey_type"] == "signup"
    assert "metrics" in data
    assert "total_started" in data["metrics"]
    assert "conversion_rate" in data["metrics"]


def test_create_dashboard_config(client: TestClient, auth_headers: dict):
    """Test creating a custom dashboard configuration."""
    response = client.post(
        "/api/v1/analytics/dashboards",
        headers=auth_headers,
        params={
            "name": "Test Dashboard",
            "description": "A test dashboard",
            "is_default": False,
        },
        json={"layout": {"widgets": []}},
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "dashboard_id" in data["data"]


def test_list_dashboards(client: TestClient, auth_headers: dict):
    """Test listing user dashboards."""
    response = client.get("/api/v1/analytics/dashboards", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert "page" in data


def test_create_report_config(client: TestClient, auth_headers: dict):
    """Test creating a report configuration."""
    response = client.post(
        "/api/v1/analytics/reports",
        headers=auth_headers,
        params={
            "name": "Test Report",
            "report_type": "usage",
            "export_format": "pdf",
        },
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "report_id" in data["data"]


def test_list_reports(client: TestClient, auth_headers: dict):
    """Test listing user reports."""
    response = client.get("/api/v1/analytics/reports", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
    assert "total" in data


def test_cohort_analysis_requires_admin(client: TestClient, auth_headers: dict):
    """Test that cohort analysis requires admin access."""
    response = client.get(
        "/api/v1/analytics/cohorts",
        headers=auth_headers,
        params={"cohort_type": "signup"},
    )
    assert response.status_code == 403


def test_revenue_analytics_requires_admin(client: TestClient, auth_headers: dict):
    """Test that revenue analytics requires admin access."""
    response = client.get(
        "/api/v1/analytics/revenue",
        headers=auth_headers,
        params={"period_type": "monthly"},
    )
    assert response.status_code == 403


def test_cohort_analysis_admin(client: TestClient, admin_headers: dict):
    """Test cohort analysis with admin access."""
    response = client.get(
        "/api/v1/analytics/cohorts",
        headers=admin_headers,
        params={"cohort_type": "signup", "period_type": "week"},
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["cohort_type"] == "signup"
    assert data["period_type"] == "week"
    assert "cohorts" in data


def test_revenue_analytics_admin(client: TestClient, admin_headers: dict):
    """Test revenue analytics with admin access."""
    response = client.get(
        "/api/v1/analytics/revenue",
        headers=admin_headers,
        params={"period_type": "monthly"},
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["period_type"] == "monthly"
    assert "summary" in data
    assert "periods" in data
