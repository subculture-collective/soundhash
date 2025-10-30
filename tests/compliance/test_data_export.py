"""Tests for data export service."""

import json
import os

import pytest
from sqlalchemy.orm import Session

from src.api.auth import get_password_hash  # noqa: E402
from src.compliance.data_export import DataExportService
from src.database.models import User


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""

    user = User(
        username="export_test_user",
        email="export@test.com",
        hashed_password=get_password_hash("password123"),
        full_name="Export Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def data_export_service():
    """Create data export service instance."""
    return DataExportService()


def test_create_export_request(
    db_session: Session, test_user: User, data_export_service: DataExportService
):
    """Test creating a data export request."""
    export_request = data_export_service.create_export_request(
        user_id=test_user.id,
        request_type="full_export",
        format="json",
        ip_address="192.168.1.1",
        session=db_session,
    )

    assert export_request is not None
    assert export_request.user_id == test_user.id
    assert export_request.request_type == "full_export"
    assert export_request.format == "json"
    assert export_request.status == "pending"
    assert export_request.ip_address == "192.168.1.1"


def test_create_partial_export_request(
    db_session: Session, test_user: User, data_export_service: DataExportService
):
    """Test creating a partial data export request."""
    data_types = ["user_profile", "api_keys", "consents"]

    export_request = data_export_service.create_export_request(
        user_id=test_user.id,
        request_type="specific_data",
        data_types=data_types,
        format="json",
        session=db_session,
    )

    assert export_request.request_type == "specific_data"
    assert export_request.data_types == data_types


def test_process_export_request(
    db_session: Session, test_user: User, data_export_service: DataExportService
):
    """Test processing a data export request."""
    # Create export request
    export_request = data_export_service.create_export_request(
        user_id=test_user.id, format="json", session=db_session
    )

    # Process the request
    file_path = data_export_service.process_export_request(
        export_request.id, session=db_session
    )

    assert file_path is not None
    assert os.path.exists(file_path)

    # Verify file contents
    with open(file_path, "r") as f:
        data = json.load(f)
        assert "user_profile" in data
        assert data["user_profile"]["username"] == test_user.username
        assert data["user_profile"]["email"] == test_user.email

    # Verify request status updated
    db_session.refresh(export_request)
    assert export_request.status == "completed"
    assert export_request.file_path == file_path
    assert export_request.file_size_bytes > 0

    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)


def test_record_download(
    db_session: Session, test_user: User, data_export_service: DataExportService
):
    """Test recording export download."""
    # Create and process export
    export_request = data_export_service.create_export_request(
        user_id=test_user.id, session=db_session
    )

    # Record download
    success = data_export_service.record_download(export_request.id, session=db_session)
    assert success is True

    # Verify download recorded
    db_session.refresh(export_request)
    assert export_request.download_count == 1
    assert export_request.last_downloaded_at is not None

    # Record another download
    data_export_service.record_download(export_request.id, session=db_session)
    db_session.refresh(export_request)
    assert export_request.download_count == 2


def test_export_request_expiration(
    db_session: Session, test_user: User, data_export_service: DataExportService
):
    """Test that export requests have expiration dates."""
    export_request = data_export_service.create_export_request(
        user_id=test_user.id, session=db_session
    )

    assert export_request.expires_at is not None
    assert export_request.expires_at > export_request.requested_at
