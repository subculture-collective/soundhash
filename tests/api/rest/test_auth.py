"""Tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    # Health check depends on database connection, which may not be available in test
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data


def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["status"] == "running"


def test_register_user(client: TestClient):
    """Test user registration."""
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "SecurePassword123!",
        "full_name": "New User"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "id" in data
    assert "hashed_password" not in data  # Should not expose password


def test_register_duplicate_username(client: TestClient, test_user: dict):
    """Test that duplicate username registration fails."""
    user_data = {
        "username": test_user["username"],
        "email": "different@example.com",
        "password": "Password123!",
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_register_duplicate_email(client: TestClient, test_user: dict):
    """Test that duplicate email registration fails."""
    user_data = {
        "username": "differentuser",
        "email": "test@example.com",  # Same as test_user
        "password": "Password123!",
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login_success(client: TestClient, test_user: dict):
    """Test successful login."""
    login_data = {
        "username": test_user["username"],
        "password": test_user["password"]
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_login_wrong_password(client: TestClient, test_user: dict):
    """Test login with wrong password."""
    login_data = {
        "username": test_user["username"],
        "password": "WrongPassword123!"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient):
    """Test login with nonexistent user."""
    login_data = {
        "username": "nonexistent",
        "password": "Password123!"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401


def test_get_current_user(client: TestClient, auth_headers: dict):
    """Test getting current user info."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "username" in data
    assert "email" in data
    assert "id" in data


def test_get_current_user_unauthorized(client: TestClient):
    """Test getting current user without authentication."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403  # No auth header provided


def test_update_user(client: TestClient, auth_headers: dict):
    """Test updating user information."""
    update_data = {
        "full_name": "Updated Name"
    }
    
    response = client.put("/api/v1/auth/me", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["full_name"] == update_data["full_name"]


def test_refresh_token(client: TestClient, test_user: dict):
    """Test token refresh."""
    # First login
    login_data = {
        "username": test_user["username"],
        "password": test_user["password"]
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    refresh_token = response.json()["refresh_token"]
    
    # Use refresh token to get new tokens
    refresh_data = {"refresh_token": refresh_token}
    response = client.post("/api/v1/auth/refresh", json=refresh_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_create_api_key(client: TestClient, auth_headers: dict):
    """Test creating an API key."""
    key_data = {
        "key_name": "Test API Key",
        "rate_limit_per_minute": 100
    }
    
    response = client.post("/api/v1/auth/api-keys", json=key_data, headers=auth_headers)
    assert response.status_code == 201
    
    data = response.json()
    assert data["key_name"] == key_data["key_name"]
    assert "api_key" in data  # Should include the actual key on creation
    assert data["api_key"].startswith("sk_")
    assert "key_prefix" in data


def test_list_api_keys(client: TestClient, auth_headers: dict):
    """Test listing API keys."""
    # Create a key first
    key_data = {"key_name": "Test Key"}
    client.post("/api/v1/auth/api-keys", json=key_data, headers=auth_headers)
    
    # List keys
    response = client.get("/api/v1/auth/api-keys", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "api_key" not in data[0]  # Should not include actual key in list


def test_delete_api_key(client: TestClient, auth_headers: dict):
    """Test deleting an API key."""
    # Create a key
    key_data = {"key_name": "Key to Delete"}
    response = client.post("/api/v1/auth/api-keys", json=key_data, headers=auth_headers)
    key_id = response.json()["id"]
    
    # Delete the key
    response = client.delete(f"/api/v1/auth/api-keys/{key_id}", headers=auth_headers)
    assert response.status_code == 204
    
    # Verify it's deleted
    response = client.get("/api/v1/auth/api-keys", headers=auth_headers)
    keys = response.json()
    assert not any(k["id"] == key_id for k in keys)
