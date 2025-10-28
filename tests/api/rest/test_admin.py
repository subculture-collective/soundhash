"""Tests for admin endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_admin_stats_unauthorized(client: TestClient, auth_headers: dict):
    """Test that non-admin users cannot access admin stats."""
    response = client.get("/api/v1/admin/stats", headers=auth_headers)
    assert response.status_code == 403


def test_admin_stats_success(client: TestClient, admin_headers: dict):
    """Test getting system statistics as admin."""
    response = client.get("/api/v1/admin/stats", headers=admin_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "users" in data
    assert "channels" in data
    assert "videos" in data
    assert "jobs" in data
    
    # Check structure
    assert "total" in data["users"]
    assert "active" in data["users"]


def test_list_jobs_admin(client: TestClient, admin_headers: dict):
    """Test listing processing jobs as admin."""
    response = client.get("/api/v1/admin/jobs", headers=admin_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data


def test_list_users_admin(client: TestClient, admin_headers: dict):
    """Test listing users as admin."""
    response = client.get("/api/v1/admin/users", headers=admin_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert len(data["data"]) >= 1  # At least the admin user


def test_list_users_unauthorized(client: TestClient, auth_headers: dict):
    """Test that non-admin users cannot list all users."""
    response = client.get("/api/v1/admin/users", headers=auth_headers)
    assert response.status_code == 403


def test_delete_user_as_admin(client: TestClient, admin_headers: dict, test_user: dict):
    """Test deleting a user as admin."""
    user_id = test_user["user_id"]
    
    response = client.delete(f"/api/v1/admin/users/{user_id}", headers=admin_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True


def test_admin_cannot_delete_self(client: TestClient, admin_headers: dict, admin_user: dict):
    """Test that admin cannot delete their own account."""
    user_id = admin_user["user_id"]
    
    response = client.delete(f"/api/v1/admin/users/{user_id}", headers=admin_headers)
    assert response.status_code == 400
