"""Middleware package initialization."""

from .tenant_middleware import TenantMiddleware

__all__ = ["TenantMiddleware"]
