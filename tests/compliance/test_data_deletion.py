"""Tests for data deletion service."""

import pytest
from sqlalchemy.orm import Session

from src.api.auth import get_password_hash, hash_api_key  # noqa: E402
from src.compliance.data_deletion import DataDeletionService
from src.database.models import APIKey, User, UserConsent


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user with associated data."""

    user = User(
        username="deletion_test_user",
        email="deletion@test.com",
        hashed_password=get_password_hash("password123"),
        full_name="Deletion Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Add some associated data
    api_key = APIKey(
        user_id=user.id,
        key_name="test_key",
        key_hash=hash_api_key("test_key_value"),
        key_prefix="tk_test",
        is_active=True,
    )
    db_session.add(api_key)

    consent = UserConsent(
        user_id=user.id,
        consent_type="privacy_policy",
        consent_version="1.0",
        given=True,
        given_at=user.created_at,
    )
    db_session.add(consent)
    db_session.commit()

    return user


@pytest.fixture
def data_deletion_service():
    """Create data deletion service instance."""
    return DataDeletionService()


def test_create_deletion_request(
    db_session: Session, test_user: User, data_deletion_service: DataDeletionService
):
    """Test creating a data deletion request."""
    deletion_request = data_deletion_service.create_deletion_request(
        user_id=test_user.id,
        deletion_type="full",
        reason="User requested account closure",
        ip_address="192.168.1.1",
        session=db_session,
    )

    assert deletion_request is not None
    assert deletion_request.user_id == test_user.id
    assert deletion_request.deletion_type == "full"
    assert deletion_request.status == "pending"
    assert deletion_request.verification_token is not None


def test_verify_deletion_request(
    db_session: Session, test_user: User, data_deletion_service: DataDeletionService
):
    """Test verifying a deletion request."""
    # Create deletion request
    deletion_request = data_deletion_service.create_deletion_request(
        user_id=test_user.id, deletion_type="full", session=db_session
    )

    token = deletion_request.verification_token

    # Verify the request
    success = data_deletion_service.verify_deletion_request(
        request_id=deletion_request.id, verification_token=token, session=db_session
    )

    assert success is True

    # Check status changed
    db_session.refresh(deletion_request)
    assert deletion_request.status == "processing"
    assert deletion_request.verified_at is not None


def test_verify_with_invalid_token(
    db_session: Session, test_user: User, data_deletion_service: DataDeletionService
):
    """Test verification with invalid token fails."""
    deletion_request = data_deletion_service.create_deletion_request(
        user_id=test_user.id, session=db_session
    )

    success = data_deletion_service.verify_deletion_request(
        request_id=deletion_request.id, verification_token="invalid_token", session=db_session
    )

    assert success is False


def test_process_full_deletion(
    db_session: Session, test_user: User, data_deletion_service: DataDeletionService
):
    """Test processing a full deletion request."""
    user_id = test_user.id

    # Create and verify deletion request
    deletion_request = data_deletion_service.create_deletion_request(
        user_id=user_id, deletion_type="full", session=db_session
    )

    data_deletion_service.verify_deletion_request(
        request_id=deletion_request.id,
        verification_token=deletion_request.verification_token,
        session=db_session,
    )

    # Process deletion
    success = data_deletion_service.process_deletion_request(
        request_id=deletion_request.id, session=db_session
    )

    assert success is True

    # Verify user and related data deleted
    user = db_session.query(User).filter_by(id=user_id).first()
    assert user is None

    api_keys = db_session.query(APIKey).filter_by(user_id=user_id).all()
    assert len(api_keys) == 0

    consents = db_session.query(UserConsent).filter_by(user_id=user_id).all()
    assert len(consents) == 0


def test_process_anonymization(
    db_session: Session, test_user: User, data_deletion_service: DataDeletionService
):
    """Test processing an anonymization request."""
    user_id = test_user.id
    original_username = test_user.username
    original_email = test_user.email

    # Create and verify anonymization request
    deletion_request = data_deletion_service.create_deletion_request(
        user_id=user_id, deletion_type="anonymize", session=db_session
    )

    data_deletion_service.verify_deletion_request(
        request_id=deletion_request.id,
        verification_token=deletion_request.verification_token,
        session=db_session,
    )

    # Process anonymization
    success = data_deletion_service.process_deletion_request(
        request_id=deletion_request.id, session=db_session
    )

    assert success is True

    # Verify user still exists but is anonymized
    user = db_session.query(User).filter_by(id=user_id).first()
    assert user is not None
    assert user.username != original_username
    assert user.email != original_email
    assert user.username.startswith("deleted_user_")
    assert user.is_active is False


def test_process_partial_deletion(
    db_session: Session, test_user: User, data_deletion_service: DataDeletionService
):
    """Test processing a partial deletion request."""
    user_id = test_user.id

    # Create and verify partial deletion request
    deletion_request = data_deletion_service.create_deletion_request(
        user_id=user_id, deletion_type="partial", data_types=["api_keys"], session=db_session
    )

    data_deletion_service.verify_deletion_request(
        request_id=deletion_request.id,
        verification_token=deletion_request.verification_token,
        session=db_session,
    )

    # Process partial deletion
    success = data_deletion_service.process_deletion_request(
        request_id=deletion_request.id, session=db_session
    )

    assert success is True

    # Verify only API keys deleted, user and consents remain
    user = db_session.query(User).filter_by(id=user_id).first()
    assert user is not None

    api_keys = db_session.query(APIKey).filter_by(user_id=user_id).all()
    assert len(api_keys) == 0

    consents = db_session.query(UserConsent).filter_by(user_id=user_id).all()
    assert len(consents) > 0  # Consents should still exist
