"""Tests for consent management service."""

import pytest
from sqlalchemy.orm import Session

from src.compliance.consent_manager import ConsentManager
from src.database.models import User, UserConsent


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    from src.api.auth import get_password_hash

    user = User(
        username="consent_test_user",
        email="consent@test.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_record_consent(db_session: Session, test_user: User):
    """Test recording user consent."""
    consent = ConsentManager.record_consent(
        user_id=test_user.id,
        consent_type="privacy_policy",
        consent_version="1.0",
        given=True,
        ip_address="192.168.1.1",
        session=db_session,
    )

    assert consent is not None
    assert consent.user_id == test_user.id
    assert consent.consent_type == "privacy_policy"
    assert consent.consent_version == "1.0"
    assert consent.given is True
    assert consent.ip_address == "192.168.1.1"


def test_withdraw_consent(db_session: Session, test_user: User):
    """Test withdrawing consent."""
    # First, give consent
    ConsentManager.record_consent(
        user_id=test_user.id,
        consent_type="marketing",
        consent_version="1.0",
        given=True,
        session=db_session,
    )

    # Then withdraw it
    success = ConsentManager.withdraw_consent(
        user_id=test_user.id, consent_type="marketing", session=db_session
    )

    assert success is True

    # Verify withdrawal was recorded
    consents = db_session.query(UserConsent).filter_by(
        user_id=test_user.id, consent_type="marketing"
    ).order_by(UserConsent.created_at.desc()).all()

    assert len(consents) >= 2
    assert consents[0].given is False  # Most recent should be withdrawal


def test_withdraw_nonexistent_consent(db_session: Session, test_user: User):
    """Test withdrawing consent that was never given."""
    success = ConsentManager.withdraw_consent(
        user_id=test_user.id, consent_type="nonexistent", session=db_session
    )

    assert success is False


def test_check_consent(db_session: Session, test_user: User):
    """Test checking if user has given consent."""
    # No consent initially
    has_consent = ConsentManager.check_consent(
        user_id=test_user.id, consent_type="terms_of_service", session=db_session
    )
    assert has_consent is False

    # Give consent
    ConsentManager.record_consent(
        user_id=test_user.id,
        consent_type="terms_of_service",
        consent_version="1.0",
        given=True,
        session=db_session,
    )

    # Check again
    has_consent = ConsentManager.check_consent(
        user_id=test_user.id, consent_type="terms_of_service", session=db_session
    )
    assert has_consent is True


def test_check_consent_after_withdrawal(db_session: Session, test_user: User):
    """Test checking consent after it's been withdrawn."""
    # Give consent
    ConsentManager.record_consent(
        user_id=test_user.id,
        consent_type="analytics",
        consent_version="1.0",
        given=True,
        session=db_session,
    )

    # Withdraw consent
    ConsentManager.withdraw_consent(
        user_id=test_user.id, consent_type="analytics", session=db_session
    )

    # Check consent status
    has_consent = ConsentManager.check_consent(
        user_id=test_user.id, consent_type="analytics", session=db_session
    )
    assert has_consent is False


def test_get_consent_history(db_session: Session, test_user: User):
    """Test retrieving consent history."""
    # Record multiple consents
    ConsentManager.record_consent(
        user_id=test_user.id, consent_type="type1", consent_version="1.0", given=True, session=db_session
    )
    ConsentManager.record_consent(
        user_id=test_user.id, consent_type="type2", consent_version="1.0", given=True, session=db_session
    )

    # Get all history
    history = ConsentManager.get_consent_history(user_id=test_user.id, session=db_session)
    assert len(history) >= 2

    # Get filtered history
    filtered_history = ConsentManager.get_consent_history(
        user_id=test_user.id, consent_type="type1", session=db_session
    )
    assert len(filtered_history) >= 1
    assert all(c.consent_type == "type1" for c in filtered_history)


def test_consent_with_metadata(db_session: Session, test_user: User):
    """Test recording consent with additional metadata."""
    metadata = {"source": "registration_form", "campaign": "summer_2025"}

    consent = ConsentManager.record_consent(
        user_id=test_user.id,
        consent_type="marketing",
        consent_version="2.0",
        given=True,
        metadata=metadata,
        session=db_session,
    )

    assert consent.extra_metadata == metadata
