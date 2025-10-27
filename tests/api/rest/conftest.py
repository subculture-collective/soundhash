"""Shared fixtures for REST API tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.dependencies import get_db
from src.api.main import app
from src.database.models import APIKey, Base, User


@pytest.fixture
def test_db():
    """Create a test database."""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db: Session):
    """Create a test client with overridden dependencies."""
    
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(client: TestClient):
    """Create a test user and return credentials."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    
    return {
        "username": user_data["username"],
        "password": user_data["password"],
        "user_id": response.json()["id"]
    }


@pytest.fixture
def auth_headers(client: TestClient, test_user: dict):
    """Get authentication headers for a test user."""
    login_data = {
        "username": test_user["username"],
        "password": test_user["password"]
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(client: TestClient, test_db: Session):
    """Create an admin user and return credentials."""
    from src.api.auth import get_password_hash
    from src.database.models import User
    
    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPassword123!"),
        full_name="Admin User",
        is_active=True,
        is_admin=True,
        is_verified=True,
    )
    
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    
    return {
        "username": "admin",
        "password": "AdminPassword123!",
        "user_id": admin.id
    }


@pytest.fixture
def admin_headers(client: TestClient, admin_user: dict):
    """Get authentication headers for an admin user."""
    login_data = {
        "username": admin_user["username"],
        "password": admin_user["password"]
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}
