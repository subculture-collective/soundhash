"""Tests for MFA service."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.auth.sso.mfa_service import MFAService
from src.database.models import Base, User
from src.database.sso_models import MFADevice


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
def test_user(db_session: Session):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def test_setup_totp(db_session: Session, test_user: User):
    """Test TOTP setup."""
    mfa_service = MFAService(db_session)

    secret, provisioning_uri = mfa_service.setup_totp(test_user, "Test Device")

    assert secret is not None
    assert len(secret) == 32  # Base32 encoded secret
    assert provisioning_uri is not None
    assert "otpauth://totp/" in provisioning_uri
    # Email is URL-encoded in the URI
    import urllib.parse
    assert urllib.parse.quote(test_user.email, safe='') in provisioning_uri

    # Check that MFA device was created
    device = (
        db_session.query(MFADevice)
        .filter(
            MFADevice.user_id == test_user.id,
            MFADevice.device_type == "totp",
        )
        .first()
    )

    assert device is not None
    assert device.device_name == "Test Device"
    assert device.is_verified is False
    assert device.is_active is False


def test_verify_totp_setup(db_session: Session, test_user: User):
    """Test TOTP verification during setup."""
    mfa_service = MFAService(db_session)

    # Setup TOTP
    secret, _ = mfa_service.setup_totp(test_user)

    # Generate a valid TOTP code
    import pyotp

    totp = pyotp.TOTP(secret)
    code = totp.now()

    # Verify the code
    result = mfa_service.verify_totp_setup(test_user, code)
    assert result is True

    # Check that device is now verified and active
    device = (
        db_session.query(MFADevice)
        .filter(
            MFADevice.user_id == test_user.id,
            MFADevice.device_type == "totp",
        )
        .first()
    )

    assert device.is_verified is True
    assert device.is_active is True


def test_verify_totp_code(db_session: Session, test_user: User):
    """Test TOTP code verification during authentication."""
    mfa_service = MFAService(db_session)

    # Setup and verify TOTP
    secret, _ = mfa_service.setup_totp(test_user)

    import pyotp

    totp = pyotp.TOTP(secret)
    code = totp.now()
    mfa_service.verify_totp_setup(test_user, code)

    # Verify a new code
    new_code = totp.now()
    result = mfa_service.verify_totp_code(test_user, new_code)
    assert result is True

    # Invalid code should fail
    result = mfa_service.verify_totp_code(test_user, "123456")
    assert result is False


def test_generate_backup_codes(db_session: Session, test_user: User):
    """Test backup code generation."""
    mfa_service = MFAService(db_session)

    codes = mfa_service.generate_backup_codes(test_user, count=10)

    assert len(codes) == 10
    assert all(len(code) == 8 for code in codes)

    # Check that backup codes device was created
    device = (
        db_session.query(MFADevice)
        .filter(
            MFADevice.user_id == test_user.id,
            MFADevice.device_type == "backup_codes",
        )
        .first()
    )

    assert device is not None
    assert len(device.backup_codes) == 10
    assert device.is_verified is True
    assert device.is_active is True


def test_verify_backup_code(db_session: Session, test_user: User):
    """Test backup code verification."""
    mfa_service = MFAService(db_session)

    # Generate backup codes
    codes = mfa_service.generate_backup_codes(test_user, count=5)

    # Verify a valid code
    result = mfa_service.verify_backup_code(test_user, codes[0])
    assert result is True

    # Verify device was updated - get fresh copy from DB
    device = (
        db_session.query(MFADevice)
        .filter(
            MFADevice.user_id == test_user.id,
            MFADevice.device_type == "backup_codes",
        )
        .first()
    )
    
    # Should have 4 codes left (started with 5, used 1)
    assert len(device.backup_codes) == 4

    # Invalid code should fail
    result = mfa_service.verify_backup_code(test_user, "INVALID")
    assert result is False


def test_get_user_mfa_devices(db_session: Session, test_user: User):
    """Test getting user's MFA devices."""
    mfa_service = MFAService(db_session)

    # Initially no devices
    devices = mfa_service.get_user_mfa_devices(test_user)
    assert len(devices) == 0

    # Setup TOTP
    secret, _ = mfa_service.setup_totp(test_user)
    import pyotp

    totp = pyotp.TOTP(secret)
    code = totp.now()
    mfa_service.verify_totp_setup(test_user, code)

    # Now should have one device
    devices = mfa_service.get_user_mfa_devices(test_user)
    assert len(devices) == 1
    assert devices[0].device_type == "totp"


def test_remove_mfa_device(db_session: Session, test_user: User):
    """Test removing an MFA device."""
    mfa_service = MFAService(db_session)

    # Setup TOTP
    secret, _ = mfa_service.setup_totp(test_user)
    import pyotp

    totp = pyotp.TOTP(secret)
    code = totp.now()
    mfa_service.verify_totp_setup(test_user, code)

    devices = mfa_service.get_user_mfa_devices(test_user)
    assert len(devices) == 1

    # Remove the device
    result = mfa_service.remove_mfa_device(test_user, devices[0].id)
    assert result is True

    # Should have no active devices now
    devices = mfa_service.get_user_mfa_devices(test_user)
    assert len(devices) == 0


def test_is_mfa_enabled(db_session: Session, test_user: User):
    """Test checking if MFA is enabled for a user."""
    mfa_service = MFAService(db_session)

    # Initially MFA is not enabled
    assert mfa_service.is_mfa_enabled(test_user) is False

    # Setup and verify TOTP
    secret, _ = mfa_service.setup_totp(test_user)
    import pyotp

    totp = pyotp.TOTP(secret)
    code = totp.now()
    mfa_service.verify_totp_setup(test_user, code)

    # Now MFA should be enabled
    assert mfa_service.is_mfa_enabled(test_user) is True
