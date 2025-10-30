"""Tests for SSO session manager."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.auth.sso.session_manager import SSOSessionManager
from src.database.models import Base, User, Tenant
from src.database.sso_models import SSOProvider, SSOSession


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def test_tenant(db_session: Session):
    """Create a test tenant."""
    tenant = Tenant(
        name="Test Tenant",
        slug="test-tenant",
        admin_email="admin@test.com",
        is_active=True,
    )

    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    return tenant


@pytest.fixture
def test_user(db_session: Session, test_tenant: Tenant):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        tenant_id=test_tenant.id,
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def test_provider(db_session: Session, test_tenant: Tenant):
    """Create a test SSO provider."""
    provider = SSOProvider(
        tenant_id=test_tenant.id,
        provider_type="oauth2_google",
        provider_name="Test OAuth",
        is_enabled=True,
    )

    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)

    return provider


def test_create_session(
    db_session: Session, test_user: User, test_provider: SSOProvider
):
    """Test creating an SSO session."""
    session_manager = SSOSessionManager(db_session)

    session = session_manager.create_session(
        user=test_user,
        provider=test_provider,
        device_id="test-device",
        device_name="Test Device",
        device_type="desktop",
        ip_address="192.168.1.1",
        user_agent="Test Agent",
        session_duration_hours=24,
    )

    assert session is not None
    assert session.user_id == test_user.id
    assert session.provider_id == test_provider.id
    assert session.device_name == "Test Device"
    assert session.is_active is True
    assert session.mfa_verified is False
    assert session.session_token is not None
    assert len(session.session_token) > 0


def test_get_session(
    db_session: Session, test_user: User, test_provider: SSOProvider
):
    """Test getting a session by token."""
    session_manager = SSOSessionManager(db_session)

    # Create session
    session = session_manager.create_session(
        user=test_user,
        provider=test_provider,
        ip_address="192.168.1.1",
        user_agent="Test Agent",
    )

    # Get session by token
    retrieved_session = session_manager.get_session(session.session_token)

    assert retrieved_session is not None
    assert retrieved_session.id == session.id
    assert retrieved_session.user_id == test_user.id


def test_get_session_expired(
    db_session: Session, test_user: User, test_provider: SSOProvider
):
    """Test getting an expired session."""
    session_manager = SSOSessionManager(db_session)

    # Create session with short duration
    session = session_manager.create_session(
        user=test_user,
        provider=test_provider,
        ip_address="192.168.1.1",
        user_agent="Test Agent",
        session_duration_hours=1,
    )

    # Manually expire the session
    session.expires_at = datetime.utcnow() - timedelta(hours=1)
    db_session.commit()

    # Should return None for expired session
    retrieved_session = session_manager.get_session(session.session_token)
    assert retrieved_session is None


def test_mark_mfa_verified(
    db_session: Session, test_user: User, test_provider: SSOProvider
):
    """Test marking session as MFA verified."""
    session_manager = SSOSessionManager(db_session)

    session = session_manager.create_session(
        user=test_user,
        provider=test_provider,
        ip_address="192.168.1.1",
        user_agent="Test Agent",
    )

    assert session.mfa_verified is False

    # Mark as MFA verified
    result = session_manager.mark_mfa_verified(session.id, "totp")
    assert result is True

    # Refresh session
    db_session.refresh(session)
    assert session.mfa_verified is True
    assert session.mfa_method == "totp"


def test_terminate_session(
    db_session: Session, test_user: User, test_provider: SSOProvider
):
    """Test terminating a session."""
    session_manager = SSOSessionManager(db_session)

    session = session_manager.create_session(
        user=test_user,
        provider=test_provider,
        ip_address="192.168.1.1",
        user_agent="Test Agent",
    )

    assert session.is_active is True

    # Terminate session
    result = session_manager.terminate_session(session.id)
    assert result is True

    # Refresh session
    db_session.refresh(session)
    assert session.is_active is False
    assert session.terminated_at is not None


def test_terminate_user_sessions(
    db_session: Session, test_user: User, test_provider: SSOProvider
):
    """Test terminating all user sessions."""
    session_manager = SSOSessionManager(db_session)

    # Create multiple sessions
    session1 = session_manager.create_session(
        user=test_user,
        provider=test_provider,
        ip_address="192.168.1.1",
        user_agent="Agent 1",
    )

    session2 = session_manager.create_session(
        user=test_user,
        provider=test_provider,
        ip_address="192.168.1.2",
        user_agent="Agent 2",
    )

    # Terminate all sessions
    count = session_manager.terminate_user_sessions(test_user)
    assert count == 2

    # Check that sessions are terminated
    db_session.refresh(session1)
    db_session.refresh(session2)

    assert session1.is_active is False
    assert session2.is_active is False


def test_extend_session(
    db_session: Session, test_user: User, test_provider: SSOProvider
):
    """Test extending session expiration."""
    session_manager = SSOSessionManager(db_session)

    session = session_manager.create_session(
        user=test_user,
        provider=test_provider,
        ip_address="192.168.1.1",
        user_agent="Test Agent",
        session_duration_hours=1,
    )

    original_expires_at = session.expires_at

    # Extend session
    result = session_manager.extend_session(session.id, additional_hours=2)
    assert result is True

    # Refresh session
    db_session.refresh(session)

    # Expiration should be extended
    assert session.expires_at > original_expires_at


def test_cleanup_expired_sessions(
    db_session: Session, test_user: User, test_provider: SSOProvider
):
    """Test cleaning up expired sessions."""
    session_manager = SSOSessionManager(db_session)

    # Create sessions
    session1 = session_manager.create_session(
        user=test_user,
        provider=test_provider,
        ip_address="192.168.1.1",
        user_agent="Agent 1",
    )

    session2 = session_manager.create_session(
        user=test_user,
        provider=test_provider,
        ip_address="192.168.1.2",
        user_agent="Agent 2",
    )

    # Expire one session
    session1.expires_at = datetime.utcnow() - timedelta(hours=1)
    db_session.commit()

    # Cleanup expired sessions
    count = session_manager.cleanup_expired_sessions()
    assert count == 1

    # Check sessions
    db_session.refresh(session1)
    db_session.refresh(session2)

    assert session1.is_active is False
    assert session2.is_active is True
