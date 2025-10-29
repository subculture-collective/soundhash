"""Tests for multi-tenant models and functionality."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import APIKey, AudioFingerprint, Base, Channel, Tenant, User, Video


@pytest.fixture
def test_db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_tenant(test_db_session):
    """Create a sample tenant for testing."""
    tenant = Tenant(
        name="Test Company",
        slug="test-company",
        admin_email="admin@testcompany.com",
        admin_name="Test Admin",
        plan_tier="enterprise",
        is_active=True,
        max_users=100,
        max_api_calls_per_month=1000000,
        max_storage_gb=1000,
        settings={"webhook_url": "https://example.com/webhook"},
    )
    test_db_session.add(tenant)
    test_db_session.commit()
    return tenant


@pytest.fixture
def sample_tenant_user(test_db_session, sample_tenant):
    """Create a sample user belonging to a tenant."""
    user = User(
        username="tenant_user",
        email="user@testcompany.com",
        hashed_password="hashed_password_here",
        full_name="Tenant User",
        tenant_id=sample_tenant.id,
        role="admin",
        is_active=True,
        is_admin=False,
        is_verified=True,
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


@pytest.fixture
def sample_tenant_api_key(test_db_session, sample_tenant, sample_tenant_user):
    """Create a sample API key for a tenant."""
    api_key = APIKey(
        tenant_id=sample_tenant.id,
        user_id=sample_tenant_user.id,
        key_name="Production API Key",
        key_hash="test_hash",
        key_prefix="test_pre",
        scopes=["read", "write"],
        rate_limit_per_minute=100,
        is_active=True,
    )
    test_db_session.add(api_key)
    test_db_session.commit()
    return api_key


class TestTenantModel:
    """Test the Tenant model."""

    def test_create_tenant(self, test_db_session):
        """Test creating a tenant."""
        tenant = Tenant(
            name="New Company",
            slug="new-company",
            admin_email="admin@newcompany.com",
            admin_name="New Admin",
            plan_tier="professional",
        )
        test_db_session.add(tenant)
        test_db_session.commit()

        assert tenant.id is not None
        assert tenant.name == "New Company"
        assert tenant.slug == "new-company"
        assert tenant.is_active is True
        assert tenant.settings is None

    def test_tenant_with_branding(self, test_db_session):
        """Test creating a tenant with branding information."""
        tenant = Tenant(
            name="Branded Company",
            slug="branded-company",
            admin_email="admin@branded.com",
            logo_url="https://example.com/logo.png",
            primary_color="#FF5733",
            custom_domain="branded.example.com",
        )
        test_db_session.add(tenant)
        test_db_session.commit()

        assert tenant.logo_url == "https://example.com/logo.png"
        assert tenant.primary_color == "#FF5733"
        assert tenant.custom_domain == "branded.example.com"

    def test_tenant_with_settings(self, test_db_session):
        """Test creating a tenant with custom settings."""
        tenant = Tenant(
            name="Settings Company",
            slug="settings-company",
            admin_email="admin@settings.com",
            settings={
                "max_concurrent_jobs": 5,
                "enable_webhooks": True,
                "webhook_url": "https://example.com/webhook",
            },
        )
        test_db_session.add(tenant)
        test_db_session.commit()

        assert tenant.settings["max_concurrent_jobs"] == 5
        assert tenant.settings["enable_webhooks"] is True

    def test_tenant_relationships(self, sample_tenant, sample_tenant_user):
        """Test tenant relationships with users."""
        assert len(sample_tenant.users) == 1
        assert sample_tenant.users[0].id == sample_tenant_user.id
        assert sample_tenant_user.tenant.id == sample_tenant.id


class TestUserTenantIntegration:
    """Test User model integration with tenants."""

    def test_user_with_tenant(self, test_db_session, sample_tenant):
        """Test creating a user with tenant association."""
        user = User(
            username="test_user",
            email="test@example.com",
            hashed_password="hashed",
            tenant_id=sample_tenant.id,
            role="member",
        )
        test_db_session.add(user)
        test_db_session.commit()

        assert user.tenant_id == sample_tenant.id
        assert user.role == "member"
        assert user.tenant.slug == "test-company"

    def test_user_without_tenant(self, test_db_session):
        """Test creating a user without tenant (super admin)."""
        user = User(
            username="super_admin",
            email="admin@soundhash.io",
            hashed_password="hashed",
            is_admin=True,
        )
        test_db_session.add(user)
        test_db_session.commit()

        assert user.tenant_id is None
        assert user.is_admin is True


class TestAPIKeyTenantIntegration:
    """Test APIKey model integration with tenants."""

    def test_api_key_with_tenant(self, sample_tenant_api_key, sample_tenant):
        """Test API key associated with tenant."""
        assert sample_tenant_api_key.tenant_id == sample_tenant.id
        assert sample_tenant_api_key.tenant.slug == "test-company"
        assert sample_tenant_api_key.scopes == ["read", "write"]

    def test_api_key_scopes(self, test_db_session, sample_tenant, sample_tenant_user):
        """Test API key with different scope configurations."""
        readonly_key = APIKey(
            tenant_id=sample_tenant.id,
            user_id=sample_tenant_user.id,
            key_name="Read-only Key",
            key_hash="readonly_hash",
            key_prefix="ro_key",
            scopes=["read"],
            rate_limit_per_minute=60,
        )
        test_db_session.add(readonly_key)
        test_db_session.commit()

        assert readonly_key.scopes == ["read"]
        assert "write" not in readonly_key.scopes


class TestTenantDataIsolation:
    """Test tenant data isolation with channels, videos, and fingerprints."""

    def test_channel_with_tenant(self, test_db_session, sample_tenant):
        """Test creating a channel with tenant association."""
        channel = Channel(
            tenant_id=sample_tenant.id,
            channel_id="UC_TEST_TENANT_CHANNEL",
            channel_name="Tenant Channel",
        )
        test_db_session.add(channel)
        test_db_session.commit()

        assert channel.tenant_id == sample_tenant.id
        assert channel.tenant.slug == "test-company"

    def test_video_with_tenant(self, test_db_session, sample_tenant):
        """Test creating a video with tenant association."""
        # First create a channel
        channel = Channel(
            tenant_id=sample_tenant.id,
            channel_id="UC_TEST",
            channel_name="Test Channel",
        )
        test_db_session.add(channel)
        test_db_session.commit()

        video = Video(
            tenant_id=sample_tenant.id,
            video_id="TEST_VIDEO",
            channel_id=channel.id,
            title="Tenant Video",
        )
        test_db_session.add(video)
        test_db_session.commit()

        assert video.tenant_id == sample_tenant.id
        assert video.tenant.slug == "test-company"

    def test_fingerprint_with_tenant(self, test_db_session, sample_tenant):
        """Test creating a fingerprint with tenant association."""
        # Create channel and video first
        channel = Channel(
            tenant_id=sample_tenant.id,
            channel_id="UC_TEST",
            channel_name="Test Channel",
        )
        test_db_session.add(channel)
        test_db_session.commit()

        video = Video(
            tenant_id=sample_tenant.id,
            video_id="TEST_VIDEO",
            channel_id=channel.id,
            title="Tenant Video",
        )
        test_db_session.add(video)
        test_db_session.commit()

        fingerprint = AudioFingerprint(
            tenant_id=sample_tenant.id,
            video_id=video.id,
            start_time=0.0,
            end_time=10.0,
            fingerprint_hash="tenant_hash",
            fingerprint_data=b"tenant_data",
        )
        test_db_session.add(fingerprint)
        test_db_session.commit()

        assert fingerprint.tenant_id == sample_tenant.id
        assert fingerprint.tenant.slug == "test-company"

    def test_multiple_tenants_isolation(self, test_db_session):
        """Test data isolation between multiple tenants."""
        # Create two tenants
        tenant1 = Tenant(
            name="Company A",
            slug="company-a",
            admin_email="admin@companya.com",
        )
        tenant2 = Tenant(
            name="Company B",
            slug="company-b",
            admin_email="admin@companyb.com",
        )
        test_db_session.add(tenant1)
        test_db_session.add(tenant2)
        test_db_session.commit()

        # Create channels for each tenant
        channel1 = Channel(
            tenant_id=tenant1.id,
            channel_id="UC_TENANT1",
            channel_name="Tenant 1 Channel",
        )
        channel2 = Channel(
            tenant_id=tenant2.id,
            channel_id="UC_TENANT2",
            channel_name="Tenant 2 Channel",
        )
        test_db_session.add(channel1)
        test_db_session.add(channel2)
        test_db_session.commit()

        # Query channels by tenant
        tenant1_channels = (
            test_db_session.query(Channel).filter(Channel.tenant_id == tenant1.id).all()
        )
        tenant2_channels = (
            test_db_session.query(Channel).filter(Channel.tenant_id == tenant2.id).all()
        )

        assert len(tenant1_channels) == 1
        assert len(tenant2_channels) == 1
        assert tenant1_channels[0].channel_id == "UC_TENANT1"
        assert tenant2_channels[0].channel_id == "UC_TENANT2"
