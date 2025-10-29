"""Tests for email API routes."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from src.api.main import app


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock authenticated user."""
    from src.api.models.auth import UserResponse

    return UserResponse(
        id=1,
        username="testuser",
        email="test@example.com",
        is_active=True,
        is_admin=False,
        is_verified=True,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )


def test_get_email_preferences_creates_default(client, mock_current_user):
    """Test getting email preferences creates default if not exists."""
    with patch("src.api.routes.email.get_current_user", return_value=mock_current_user):
        with patch("src.api.routes.email.get_db") as mock_db:
            mock_session = MagicMock()
            mock_db.return_value = mock_session

            # No existing preferences
            mock_session.query.return_value.filter_by.return_value.first.return_value = None

            response = client.get("/api/v1/email/preferences")

            # Should create new preferences
            assert response.status_code == 200
            assert mock_session.add.called


def test_update_email_preferences(client, mock_current_user):
    """Test updating email preferences."""
    with patch("src.api.routes.email.get_current_user", return_value=mock_current_user):
        with patch("src.api.routes.email.get_db") as mock_db:
            mock_session = MagicMock()
            mock_db.return_value = mock_session

            from src.database.models import EmailPreference

            mock_pref = EmailPreference(
                id=1,
                user_id=1,
                receive_match_found=True,
            )
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_pref

            response = client.put(
                "/api/v1/email/preferences",
                json={"receive_match_found": False},
            )

            assert response.status_code == 200
            assert mock_pref.receive_match_found is False


def test_unsubscribe_from_emails(client):
    """Test unsubscribing from emails."""
    with patch("src.api.routes.email.get_db") as mock_db:
        mock_session = MagicMock()
        mock_db.return_value = mock_session

        from src.database.models import User, EmailPreference

        mock_user = User(id=1, email="test@example.com")
        mock_pref = EmailPreference(id=1, user_id=1)

        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            mock_user,
            mock_pref,
        ]

        response = client.post(
            "/api/v1/email/unsubscribe",
            json={"email": "test@example.com"},
        )

        assert response.status_code == 200
        assert mock_pref.unsubscribed_at is not None
