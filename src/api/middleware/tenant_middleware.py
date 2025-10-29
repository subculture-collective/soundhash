"""Tenant middleware for multi-tenant request routing."""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import Config
from src.database.tenant_filter import set_current_tenant_id
from src.database.tenant_repository import get_tenant_repository

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and set tenant context for each request."""

    async def dispatch(self, request: Request, call_next):
        """
        Process request and set tenant context.

        Tenant extraction priority:
        1. Custom domain
        2. Subdomain (e.g., acme.soundhash.io)
        3. X-API-Key header
        4. Authenticated user
        """
        tenant = await self.get_tenant_from_request(request)

        if tenant:
            # Set tenant context for this request
            set_current_tenant_id(tenant.id)
            request.state.tenant = tenant
            logger.debug(f"Request processed for tenant: {tenant.slug}")
        else:
            logger.debug("Request processed without tenant context")

        response = await call_next(request)

        # Clean up context
        set_current_tenant_id(None)

        return response

    async def get_tenant_from_request(self, request: Request):
        """
        Extract tenant from various sources.

        Note: This method performs sequential database queries for tenant detection.
        For high-traffic scenarios, consider implementing caching for frequently
        accessed tenants, especially those identified by API keys or custom domains.

        Args:
            request: FastAPI request object

        Returns:
            Tenant object or None
        """
        tenant_repo = get_tenant_repository()

        try:
            # 1. From custom domain
            host = request.headers.get("host", "").split(":")[0]
            tenant = tenant_repo.get_by_domain(host)
            if tenant and tenant.is_active:
                return tenant

            # 2. From subdomain (e.g., acme.soundhash.io)
            if Config.BASE_DOMAIN and host.endswith(f".{Config.BASE_DOMAIN}"):
                subdomain = host.replace(f".{Config.BASE_DOMAIN}", "")
                if subdomain and subdomain != Config.BASE_DOMAIN:
                    tenant = tenant_repo.get_by_slug(subdomain)
                    if tenant and tenant.is_active:
                        return tenant

            # 3. From API key header
            api_key = request.headers.get("X-API-Key")
            if api_key:
                # Import here to avoid circular dependency
                from src.api.auth import hash_api_key
                key_hash = hash_api_key(api_key)
                key_record = tenant_repo.get_api_key(key_hash)
                if key_record and key_record.tenant:
                    return key_record.tenant

            # 4. From authenticated user
            if hasattr(request.state, "user") and request.state.user:
                user_tenant = request.state.user.tenant
                if user_tenant and user_tenant.is_active:
                    return user_tenant

            return None
        except Exception as e:
            logger.error(f"Error extracting tenant from request: {e}")
            return None
        finally:
            # Close the session
            tenant_repo.session.close()
