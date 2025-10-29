"""Tests for tenant repository operations."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, Tenant, User
from src.database.tenant_repository import TenantRepository


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
def tenant_repo(test_db_session):
    """Create a tenant repository instance."""
    return TenantRepository(test_db_session)


class TestTenantRepository:
    """Test tenant repository CRUD operations."""

    def test_create_tenant(self, tenant_repo):
        """Test creating a tenant."""
        tenant = tenant_repo.create_tenant(
            name="Test Company",
            slug="test-company",
            admin_email="admin@test.com",
            admin_name="Test Admin",
            plan_tier="enterprise",
        )

        assert tenant.id is not None
        assert tenant.name == "Test Company"
        assert tenant.slug == "test-company"
        assert tenant.admin_email == "admin@test.com"
        assert tenant.is_active is True

    def test_create_tenant_with_settings(self, tenant_repo):
        """Test creating a tenant with custom settings."""
        tenant = tenant_repo.create_tenant(
            name="Settings Company",
            slug="settings-co",
            admin_email="admin@settings.com",
            settings={"max_concurrent_jobs": 10},
        )

        assert tenant.settings == {"max_concurrent_jobs": 10}

    def test_get_by_id(self, tenant_repo):
        """Test retrieving tenant by ID."""
        tenant = tenant_repo.create_tenant(
            name="Find Me",
            slug="find-me",
            admin_email="admin@findme.com",
        )

        retrieved = tenant_repo.get_by_id(tenant.id)
        assert retrieved is not None
        assert retrieved.slug == "find-me"

    def test_get_by_id_not_found(self, tenant_repo):
        """Test retrieving non-existent tenant by ID."""
        retrieved = tenant_repo.get_by_id(99999)
        assert retrieved is None

    def test_get_by_slug(self, tenant_repo):
        """Test retrieving tenant by slug."""
        tenant_repo.create_tenant(
            name="Slug Test",
            slug="slug-test",
            admin_email="admin@slug.com",
        )

        retrieved = tenant_repo.get_by_slug("slug-test")
        assert retrieved is not None
        assert retrieved.name == "Slug Test"

    def test_get_by_slug_not_found(self, tenant_repo):
        """Test retrieving non-existent tenant by slug."""
        retrieved = tenant_repo.get_by_slug("non-existent")
        assert retrieved is None

    def test_get_by_domain(self, tenant_repo):
        """Test retrieving tenant by custom domain."""
        tenant_repo.create_tenant(
            name="Domain Test",
            slug="domain-test",
            admin_email="admin@domain.com",
            custom_domain="custom.example.com",
        )

        retrieved = tenant_repo.get_by_domain("custom.example.com")
        assert retrieved is not None
        assert retrieved.slug == "domain-test"

    def test_get_by_domain_not_found(self, tenant_repo):
        """Test retrieving non-existent tenant by domain."""
        retrieved = tenant_repo.get_by_domain("nonexistent.example.com")
        assert retrieved is None

    def test_update_branding(self, tenant_repo):
        """Test updating tenant branding."""
        tenant = tenant_repo.create_tenant(
            name="Branding Test",
            slug="branding-test",
            admin_email="admin@branding.com",
        )

        updated = tenant_repo.update_branding(
            tenant.id,
            logo_url="https://example.com/logo.png",
            primary_color="#FF5733",
            custom_domain="branded.example.com",
        )

        assert updated is not None
        assert updated.logo_url == "https://example.com/logo.png"
        assert updated.primary_color == "#FF5733"
        assert updated.custom_domain == "branded.example.com"

    def test_update_branding_partial(self, tenant_repo):
        """Test partially updating tenant branding."""
        tenant = tenant_repo.create_tenant(
            name="Partial Update",
            slug="partial-update",
            admin_email="admin@partial.com",
            logo_url="https://example.com/old-logo.png",
        )

        # Update only primary color
        updated = tenant_repo.update_branding(
            tenant.id,
            primary_color="#00FF00",
        )

        assert updated is not None
        assert updated.logo_url == "https://example.com/old-logo.png"  # Unchanged
        assert updated.primary_color == "#00FF00"  # Changed

    def test_update_settings(self, tenant_repo):
        """Test updating tenant settings."""
        tenant = tenant_repo.create_tenant(
            name="Settings Update",
            slug="settings-update",
            admin_email="admin@settings.com",
            settings={"old_setting": "old_value"},
        )

        new_settings = {
            "new_setting": "new_value",
            "max_concurrent_jobs": 15,
        }
        updated = tenant_repo.update_settings(tenant.id, new_settings)

        assert updated is not None
        assert updated.settings == new_settings
        assert "old_setting" not in updated.settings

    def test_create_api_key(self, tenant_repo, test_db_session):
        """Test creating an API key for a tenant."""
        tenant = tenant_repo.create_tenant(
            name="API Key Test",
            slug="api-key-test",
            admin_email="admin@apikey.com",
        )

        # Create a user for the API key
        user = User(
            username="apiuser",
            email="user@apikey.com",
            hashed_password="hashed",
            tenant_id=tenant.id,
        )
        test_db_session.add(user)
        test_db_session.commit()

        api_key = tenant_repo.create_api_key(
            tenant_id=tenant.id,
            user_id=user.id,
            key_name="Test API Key",
            key_hash="test_hash_123",
            key_prefix="test_",
            scopes=["read", "write"],
            rate_limit=100,
        )

        assert api_key.id is not None
        assert api_key.tenant_id == tenant.id
        assert api_key.key_name == "Test API Key"
        assert api_key.scopes == ["read", "write"]
        assert api_key.rate_limit_per_minute == 100

    def test_list_tenants(self, tenant_repo):
        """Test listing all tenants."""
        tenant_repo.create_tenant(
            name="Tenant 1",
            slug="tenant-1",
            admin_email="admin1@example.com",
        )
        tenant_repo.create_tenant(
            name="Tenant 2",
            slug="tenant-2",
            admin_email="admin2@example.com",
        )

        tenants = tenant_repo.list_tenants()
        assert len(tenants) == 2
        assert {t.slug for t in tenants} == {"tenant-1", "tenant-2"}

    def test_list_tenants_filtered_by_active(self, tenant_repo):
        """Test listing tenants filtered by active status."""
        active_tenant = tenant_repo.create_tenant(
            name="Active Tenant",
            slug="active-tenant",
            admin_email="active@example.com",
            is_active=True,
        )
        inactive_tenant = tenant_repo.create_tenant(
            name="Inactive Tenant",
            slug="inactive-tenant",
            admin_email="inactive@example.com",
            is_active=False,
        )

        active_tenants = tenant_repo.list_tenants(is_active=True)
        inactive_tenants = tenant_repo.list_tenants(is_active=False)

        assert len(active_tenants) == 1
        assert active_tenants[0].slug == "active-tenant"
        assert len(inactive_tenants) == 1
        assert inactive_tenants[0].slug == "inactive-tenant"

    def test_deactivate_tenant(self, tenant_repo):
        """Test deactivating a tenant."""
        tenant = tenant_repo.create_tenant(
            name="Deactivate Test",
            slug="deactivate-test",
            admin_email="admin@deactivate.com",
            is_active=True,
        )

        assert tenant.is_active is True

        deactivated = tenant_repo.deactivate_tenant(tenant.id)

        assert deactivated is not None
        assert deactivated.is_active is False

    def test_deactivate_nonexistent_tenant(self, tenant_repo):
        """Test deactivating a non-existent tenant."""
        result = tenant_repo.deactivate_tenant(99999)
        assert result is None


class TestTenantRepositoryEdgeCases:
    """Test edge cases and error handling in tenant repository."""

    def test_duplicate_slug(self, tenant_repo):
        """Test creating tenant with duplicate slug."""
        tenant_repo.create_tenant(
            name="First Tenant",
            slug="duplicate-slug",
            admin_email="first@example.com",
        )

        with pytest.raises(Exception):  # Should raise IntegrityError
            tenant_repo.create_tenant(
                name="Second Tenant",
                slug="duplicate-slug",
                admin_email="second@example.com",
            )

    def test_duplicate_custom_domain(self, tenant_repo):
        """Test creating tenant with duplicate custom domain."""
        tenant_repo.create_tenant(
            name="First Tenant",
            slug="first-tenant",
            admin_email="first@example.com",
            custom_domain="shared.example.com",
        )

        with pytest.raises(Exception):  # Should raise IntegrityError
            tenant_repo.create_tenant(
                name="Second Tenant",
                slug="second-tenant",
                admin_email="second@example.com",
                custom_domain="shared.example.com",
            )
