"""Tenant filtering for row-level security in multi-tenant architecture."""

from contextvars import ContextVar

# Context variable to store current tenant ID
current_tenant_id: ContextVar[int | None] = ContextVar("current_tenant_id", default=None)


def get_current_tenant_id() -> int | None:
    """
    Get the current tenant ID from context.

    Returns:
        Current tenant ID or None if not set
    """
    return current_tenant_id.get()


def set_current_tenant_id(tenant_id: int | None) -> None:
    """
    Set the current tenant ID in context.

    Args:
        tenant_id: Tenant ID to set in context
    """
    current_tenant_id.set(tenant_id)
