"""Repository for tenant management operations."""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError
from sqlalchemy.orm import Session

from .models import APIKey, Tenant
from .repositories import db_retry

logger = logging.getLogger(__name__)


class TenantRepository:
    """Repository for tenant CRUD operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    @db_retry()
    def create_tenant(
        self,
        name: str,
        slug: str,
        admin_email: str,
        admin_name: str | None = None,
        plan_tier: str | None = None,
        **kwargs: Any,
    ) -> Tenant:
        """Create a new tenant with retry on transient errors."""
        try:
            tenant = Tenant(
                name=name,
                slug=slug,
                admin_email=admin_email,
                admin_name=admin_name,
                plan_tier=plan_tier,
                **kwargs,
            )
            self.session.add(tenant)
            self.session.commit()
            logger.debug(f"Created tenant: {slug}")
            return tenant
        except (IntegrityError, OperationalError, DBAPIError) as e:
            logger.error(f"Failed to create tenant {slug}: {e}")
            raise

    @db_retry()
    def get_by_id(self, tenant_id: int) -> Tenant | None:
        """Get tenant by ID with retry on transient errors."""
        try:
            return self.session.get(Tenant, tenant_id)
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to get tenant by ID {tenant_id}: {e}")
            raise

    @db_retry()
    def get_by_slug(self, slug: str) -> Tenant | None:
        """Get tenant by slug with retry on transient errors."""
        try:
            return self.session.query(Tenant).filter(Tenant.slug == slug).first()
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to get tenant by slug {slug}: {e}")
            raise

    @db_retry()
    def get_by_domain(self, domain: str) -> Tenant | None:
        """Get tenant by custom domain with retry on transient errors."""
        try:
            return self.session.query(Tenant).filter(Tenant.custom_domain == domain).first()
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to get tenant by domain {domain}: {e}")
            raise

    @db_retry()
    def update_branding(
        self,
        tenant_id: int,
        logo_url: str | None = None,
        primary_color: str | None = None,
        custom_domain: str | None = None,
    ) -> Tenant | None:
        """Update tenant branding with retry on transient errors."""
        try:
            tenant = self.session.get(Tenant, tenant_id)
            if tenant:
                if logo_url is not None:
                    tenant.logo_url = logo_url
                if primary_color is not None:
                    tenant.primary_color = primary_color
                if custom_domain is not None:
                    tenant.custom_domain = custom_domain
                tenant.updated_at = datetime.utcnow()
                self.session.commit()
                logger.debug(f"Updated branding for tenant {tenant_id}")
            return tenant
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to update branding for tenant {tenant_id}: {e}")
            raise

    @db_retry()
    def update_settings(self, tenant_id: int, settings: dict[str, Any]) -> Tenant | None:
        """Update tenant settings with retry on transient errors."""
        try:
            tenant = self.session.get(Tenant, tenant_id)
            if tenant:
                tenant.settings = settings
                tenant.updated_at = datetime.utcnow()
                self.session.commit()
                logger.debug(f"Updated settings for tenant {tenant_id}")
            return tenant
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to update settings for tenant {tenant_id}: {e}")
            raise

    @db_retry()
    def get_api_key(self, key_hash: str) -> APIKey | None:
        """Get API key by hash with retry on transient errors."""
        try:
            return self.session.query(APIKey).filter(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True  # noqa: E712
            ).first()
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to get API key: {e}")
            raise

    @db_retry()
    def create_api_key(
        self,
        tenant_id: int,
        user_id: int,
        key_name: str,
        key_hash: str,
        key_prefix: str,
        scopes: list[str] | None = None,
        rate_limit: int = 60,
        expires_at: datetime | None = None,
    ) -> APIKey:
        """Create a new API key for a tenant with retry on transient errors."""
        try:
            api_key = APIKey(
                tenant_id=tenant_id,
                user_id=user_id,
                key_name=key_name,
                key_hash=key_hash,
                key_prefix=key_prefix,
                scopes=scopes or ["read"],
                rate_limit_per_minute=rate_limit,
                expires_at=expires_at,
            )
            self.session.add(api_key)
            self.session.commit()
            logger.debug(f"Created API key for tenant {tenant_id}")
            return api_key
        except (IntegrityError, OperationalError, DBAPIError) as e:
            logger.error(f"Failed to create API key for tenant {tenant_id}: {e}")
            raise

    @db_retry()
    def list_tenants(self, is_active: bool | None = None) -> list[Tenant]:
        """List all tenants with optional filtering by active status."""
        try:
            query = self.session.query(Tenant)
            if is_active is not None:
                query = query.filter(Tenant.is_active == is_active)
            return query.all()
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to list tenants: {e}")
            raise

    @db_retry()
    def deactivate_tenant(self, tenant_id: int) -> Tenant | None:
        """Deactivate a tenant."""
        try:
            tenant = self.session.get(Tenant, tenant_id)
            if tenant:
                tenant.is_active = False
                tenant.updated_at = datetime.utcnow()
                self.session.commit()
                logger.info(f"Deactivated tenant {tenant_id}")
            return tenant
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to deactivate tenant {tenant_id}: {e}")
            raise


def get_tenant_repository() -> TenantRepository:
    """Get a tenant repository instance.

    NOTE: Caller is responsible for session lifecycle (commit/rollback/close).
    """
    from .connection import db_manager
    session = db_manager.get_session()
    return TenantRepository(session)
