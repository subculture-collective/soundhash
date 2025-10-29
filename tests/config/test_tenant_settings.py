"""Tests for tenant-specific settings."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.tenant_settings import TenantSettings
from src.database.models import Base, Tenant


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
    """Create a sample tenant with settings."""
    tenant = Tenant(
        name="Test Company",
        slug="test-company",
        admin_email="admin@test.com",
        settings={
            "max_concurrent_jobs": 10,
            "fingerprint_sample_rate": 44100,
            "enable_webhooks": True,
            "webhook_url": "https://example.com/webhook",
            "max_upload_size_mb": 500,
        },
    )
    test_db_session.add(tenant)
    test_db_session.commit()
    return tenant


class TestTenantSettings:
    """Test tenant-specific settings management."""

    def test_get_existing_setting(self, sample_tenant):
        """Test retrieving an existing tenant setting."""
        settings = TenantSettings(sample_tenant)
        assert settings.get("max_concurrent_jobs") == 10

    def test_get_non_existing_setting(self, sample_tenant):
        """Test retrieving a non-existing setting returns None."""
        settings = TenantSettings(sample_tenant)
        assert settings.get("non_existent_key") is None

    def test_get_with_default(self, sample_tenant):
        """Test retrieving a setting with a default value."""
        settings = TenantSettings(sample_tenant)
        assert settings.get("non_existent_key", "default_value") == "default_value"

    def test_set_new_setting(self, sample_tenant):
        """Test setting a new tenant setting."""
        settings = TenantSettings(sample_tenant)
        settings.set("new_key", "new_value")

        assert settings.get("new_key") == "new_value"
        assert sample_tenant.settings["new_key"] == "new_value"

    def test_update_existing_setting(self, sample_tenant):
        """Test updating an existing setting."""
        settings = TenantSettings(sample_tenant)
        original_value = settings.get("max_concurrent_jobs")
        assert original_value == 10

        settings.set("max_concurrent_jobs", 20)
        assert settings.get("max_concurrent_jobs") == 20

    def test_property_max_concurrent_jobs(self, sample_tenant):
        """Test max_concurrent_jobs property."""
        settings = TenantSettings(sample_tenant)
        assert settings.max_concurrent_jobs == 10

    def test_property_max_concurrent_jobs_default(self, test_db_session):
        """Test max_concurrent_jobs property with default value."""
        tenant = Tenant(
            name="Default Settings",
            slug="default-settings",
            admin_email="admin@default.com",
            settings={},
        )
        test_db_session.add(tenant)
        test_db_session.commit()

        settings = TenantSettings(tenant)
        # Should fall back to Config.MAX_CONCURRENT_DOWNLOADS
        assert settings.max_concurrent_jobs is not None

    def test_property_fingerprint_sample_rate(self, sample_tenant):
        """Test fingerprint_sample_rate property."""
        settings = TenantSettings(sample_tenant)
        assert settings.fingerprint_sample_rate == 44100

    def test_property_enable_webhooks(self, sample_tenant):
        """Test enable_webhooks property."""
        settings = TenantSettings(sample_tenant)
        assert settings.enable_webhooks is True

    def test_property_webhook_url(self, sample_tenant):
        """Test webhook_url property."""
        settings = TenantSettings(sample_tenant)
        assert settings.webhook_url == "https://example.com/webhook"

    def test_property_webhook_url_none(self, test_db_session):
        """Test webhook_url property when not configured."""
        tenant = Tenant(
            name="No Webhook",
            slug="no-webhook",
            admin_email="admin@nowebhook.com",
            settings={},
        )
        test_db_session.add(tenant)
        test_db_session.commit()

        settings = TenantSettings(tenant)
        assert settings.webhook_url is None

    def test_property_max_upload_size_mb(self, sample_tenant):
        """Test max_upload_size_mb property."""
        settings = TenantSettings(sample_tenant)
        assert settings.max_upload_size_mb == 500

    def test_property_max_upload_size_mb_default(self, test_db_session):
        """Test max_upload_size_mb property with default value."""
        tenant = Tenant(
            name="Default Upload",
            slug="default-upload",
            admin_email="admin@upload.com",
            settings={},
        )
        test_db_session.add(tenant)
        test_db_session.commit()

        settings = TenantSettings(tenant)
        assert settings.max_upload_size_mb == 100  # Default value

    def test_tenant_without_settings(self, test_db_session):
        """Test TenantSettings with tenant that has no settings."""
        tenant = Tenant(
            name="No Settings",
            slug="no-settings",
            admin_email="admin@nosettings.com",
        )
        test_db_session.add(tenant)
        test_db_session.commit()

        settings = TenantSettings(tenant)
        assert settings._settings == {}
        assert settings.get("any_key") is None
