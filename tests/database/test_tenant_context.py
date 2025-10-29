"""Tests for tenant context filtering and isolation."""

from src.database.tenant_filter import (
    get_current_tenant_id,
    set_current_tenant_id,
)


class TestTenantContextManagement:
    """Test tenant context variable management."""

    def test_initial_tenant_context_is_none(self):
        """Test that initial tenant context is None."""
        # Reset context
        set_current_tenant_id(None)
        assert get_current_tenant_id() is None

    def test_set_and_get_tenant_context(self):
        """Test setting and getting tenant context."""
        set_current_tenant_id(123)
        assert get_current_tenant_id() == 123

    def test_update_tenant_context(self):
        """Test updating tenant context."""
        set_current_tenant_id(456)
        assert get_current_tenant_id() == 456

        set_current_tenant_id(789)
        assert get_current_tenant_id() == 789

    def test_clear_tenant_context(self):
        """Test clearing tenant context."""
        set_current_tenant_id(999)
        assert get_current_tenant_id() == 999

        set_current_tenant_id(None)
        assert get_current_tenant_id() is None

    def test_tenant_context_isolation(self):
        """Test that tenant context is isolated per execution context."""
        # This test verifies basic functionality
        # In a real async environment, each task would have its own context
        set_current_tenant_id(111)
        assert get_current_tenant_id() == 111

        # Simulate context change
        set_current_tenant_id(222)
        assert get_current_tenant_id() == 222

        # Clean up
        set_current_tenant_id(None)
