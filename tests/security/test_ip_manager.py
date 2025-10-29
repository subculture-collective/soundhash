"""Tests for IP manager."""

from src.security.ip_manager import IPManager


class TestIPManager:
    """Test IP manager functionality."""

    def test_ip_manager_init(self):
        """Test IP manager initialization."""
        manager = IPManager()
        assert manager is not None

    def test_add_to_allowlist(self):
        """Test adding IP to allowlist."""
        manager = IPManager()

        # Add single IP
        success = manager.add_to_allowlist("192.168.1.100")
        assert success is True
        assert "192.168.1.100" in manager.allowlist

    def test_add_network_to_allowlist(self):
        """Test adding network to allowlist."""
        manager = IPManager()

        # Add network in CIDR notation
        success = manager.add_to_allowlist("192.168.1.0/24")
        assert success is True

    def test_add_to_blocklist(self):
        """Test adding IP to blocklist."""
        manager = IPManager()

        # Add single IP with reason
        success = manager.add_to_blocklist("203.0.113.50", reason="Suspicious activity")
        assert success is True
        assert "203.0.113.50" in manager.blocklist

    def test_add_network_to_blocklist(self):
        """Test adding network to blocklist."""
        manager = IPManager()

        # Add network in CIDR notation
        success = manager.add_to_blocklist("203.0.113.0/24", reason="Spam source")
        assert success is True

    def test_is_blocked_single_ip(self):
        """Test checking if IP is blocked."""
        manager = IPManager()

        # Add IP to blocklist
        manager.add_to_blocklist("203.0.113.50", reason="Test block")

        # Check if blocked
        is_blocked, reason = manager.is_blocked("203.0.113.50")
        assert is_blocked is True

    def test_is_blocked_network(self):
        """Test checking if IP in blocked network."""
        manager = IPManager()

        # Add network to blocklist
        manager.add_to_blocklist("203.0.113.0/24", reason="Spam network")

        # Check if IP in network is blocked
        is_blocked, reason = manager.is_blocked("203.0.113.100")
        assert is_blocked is True

    def test_is_allowed_empty_allowlist(self):
        """Test that empty allowlist allows all IPs."""
        manager = IPManager()

        # Empty allowlist should allow all
        is_allowed = manager.is_allowed("192.168.1.100")
        assert is_allowed is True

    def test_is_allowed_with_allowlist(self):
        """Test checking if IP is in allowlist."""
        manager = IPManager()

        # Add IP to allowlist
        manager.add_to_allowlist("192.168.1.100")

        # IP in allowlist should be allowed
        is_allowed = manager.is_allowed("192.168.1.100")
        assert is_allowed is True

        # IP not in allowlist should be denied
        is_allowed = manager.is_allowed("192.168.1.200")
        assert is_allowed is False

    def test_is_allowed_network(self):
        """Test checking if IP in allowed network."""
        manager = IPManager()

        # Add network to allowlist
        manager.add_to_allowlist("192.168.1.0/24")

        # IP in network should be allowed
        is_allowed = manager.is_allowed("192.168.1.100")
        assert is_allowed is True

        # IP outside network should be denied
        is_allowed = manager.is_allowed("192.168.2.100")
        assert is_allowed is False

    def test_check_ip_combined(self):
        """Test combined IP check (allowlist and blocklist)."""
        manager = IPManager()

        # Add to allowlist
        manager.add_to_allowlist("192.168.1.0/24")

        # Add specific IP to blocklist
        manager.add_to_blocklist("192.168.1.50", reason="Compromised")

        # IP in allowlist but also blocked should be denied
        allowed, reason = manager.check_ip("192.168.1.50")
        assert allowed is False

        # IP in allowlist and not blocked should be allowed
        allowed, reason = manager.check_ip("192.168.1.100")
        assert allowed is True

        # IP outside allowlist should be denied
        allowed, reason = manager.check_ip("192.168.2.100")
        assert allowed is False

    def test_remove_from_allowlist(self):
        """Test removing IP from allowlist."""
        manager = IPManager()

        # Add and then remove
        manager.add_to_allowlist("192.168.1.100")
        assert "192.168.1.100" in manager.allowlist

        manager.remove_from_allowlist("192.168.1.100")
        assert "192.168.1.100" not in manager.allowlist

    def test_remove_from_blocklist(self):
        """Test removing IP from blocklist."""
        manager = IPManager()

        # Add and then remove
        manager.add_to_blocklist("203.0.113.50")
        assert "203.0.113.50" in manager.blocklist

        manager.remove_from_blocklist("203.0.113.50")
        assert "203.0.113.50" not in manager.blocklist

    def test_get_lists(self):
        """Test getting allowlist and blocklist."""
        manager = IPManager()

        # Add some IPs
        manager.add_to_allowlist("192.168.1.100")
        manager.add_to_allowlist("192.168.1.0/24")
        manager.add_to_blocklist("203.0.113.50")

        allowlist = manager.get_allowlist()
        blocklist = manager.get_blocklist()

        assert len(allowlist) >= 2
        assert len(blocklist) >= 1

    def test_ipv6_support(self):
        """Test IPv6 address support."""
        manager = IPManager()

        # Add IPv6 address
        success = manager.add_to_allowlist("2001:db8::1")
        assert success is True

        # Check if allowed
        is_allowed = manager.is_allowed("2001:db8::1")
        assert is_allowed is True

    def test_invalid_ip_handling(self):
        """Test handling of invalid IP addresses."""
        manager = IPManager()

        # Invalid IP should return as-is but not cause error
        success = manager.add_to_allowlist("invalid.ip.address")
        # Should handle gracefully
        assert isinstance(success, bool)
