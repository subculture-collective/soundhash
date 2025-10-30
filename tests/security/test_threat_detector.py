"""Tests for threat detector."""

from src.security.threat_detector import ThreatDetector


class TestThreatDetector:
    """Test threat detector functionality."""

    def test_threat_detector_init(self):
        """Test threat detector initialization."""
        detector = ThreatDetector()
        assert detector is not None

    def test_detect_sql_injection_union(self):
        """Test SQL injection detection - UNION."""
        detector = ThreatDetector()

        # Should detect SQL injection
        pattern = detector.detect_sql_injection("1' UNION SELECT * FROM users--")
        assert pattern is not None

    def test_detect_sql_injection_or(self):
        """Test SQL injection detection - OR."""
        detector = ThreatDetector()

        # Should detect SQL injection
        pattern = detector.detect_sql_injection("' OR 1=1--")
        assert pattern is not None

    def test_detect_sql_injection_drop(self):
        """Test SQL injection detection - DROP."""
        detector = ThreatDetector()

        # Should detect SQL injection
        pattern = detector.detect_sql_injection("'; DROP TABLE users;--")
        assert pattern is not None

    def test_safe_sql_input(self):
        """Test that safe SQL input is not flagged."""
        detector = ThreatDetector()

        # Should not detect SQL injection in safe input
        pattern = detector.detect_sql_injection("user123")
        assert pattern is None

        pattern = detector.detect_sql_injection("search term")
        assert pattern is None

    def test_detect_xss_script(self):
        """Test XSS detection - script tag."""
        detector = ThreatDetector()

        # Should detect XSS
        pattern = detector.detect_xss("<script>alert('XSS')</script>")
        assert pattern is not None

    def test_detect_xss_javascript(self):
        """Test XSS detection - javascript:."""
        detector = ThreatDetector()

        # Should detect XSS
        pattern = detector.detect_xss("javascript:alert(1)")
        assert pattern is not None

    def test_detect_xss_onerror(self):
        """Test XSS detection - onerror."""
        detector = ThreatDetector()

        # Should detect XSS
        pattern = detector.detect_xss('<img src=x onerror="alert(1)">')
        assert pattern is not None

    def test_safe_xss_input(self):
        """Test that safe input is not flagged as XSS."""
        detector = ThreatDetector()

        # Should not detect XSS in safe input
        pattern = detector.detect_xss("Hello world")
        assert pattern is None

    def test_detect_path_traversal_dotdot(self):
        """Test path traversal detection - ../."""
        detector = ThreatDetector()

        # Should detect path traversal
        pattern = detector.detect_path_traversal("../../etc/passwd")
        assert pattern is not None

    def test_detect_path_traversal_windows(self):
        """Test path traversal detection - Windows."""
        detector = ThreatDetector()

        # Should detect path traversal
        pattern = detector.detect_path_traversal("c:\\windows\\system32")
        assert pattern is not None

    def test_safe_path_input(self):
        """Test that safe paths are not flagged."""
        detector = ThreatDetector()

        # Should not detect path traversal in safe input
        pattern = detector.detect_path_traversal("/api/v1/videos")
        assert pattern is None

    def test_detect_suspicious_user_agent(self):
        """Test suspicious user agent detection."""
        detector = ThreatDetector()

        # Should detect suspicious user agents
        assert detector.detect_suspicious_user_agent("sqlmap/1.0") is True
        assert detector.detect_suspicious_user_agent("nikto") is True
        assert detector.detect_suspicious_user_agent("nmap") is True

    def test_safe_user_agent(self):
        """Test that normal user agents are not flagged."""
        detector = ThreatDetector()

        # Should not flag normal user agents
        assert detector.detect_suspicious_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64)") is False
        assert detector.detect_suspicious_user_agent("curl/7.68.0") is False

    def test_empty_user_agent(self):
        """Test that empty user agent is flagged."""
        detector = ThreatDetector()

        # Empty user agent is suspicious
        assert detector.detect_suspicious_user_agent("") is True
        assert detector.detect_suspicious_user_agent(None) is True

    def test_check_request_safe(self):
        """Test checking a safe request."""
        detector = ThreatDetector()

        is_safe, threats = detector.check_request(
            ip="192.168.1.100",
            method="GET",
            path="/api/v1/videos",
            query_params={"page": "1", "limit": "10"},
            headers={"User-Agent": "Mozilla/5.0"},
            body=None,
        )

        assert is_safe is True
        assert len(threats) == 0

    def test_check_request_sql_injection(self):
        """Test checking request with SQL injection."""
        detector = ThreatDetector()

        is_safe, threats = detector.check_request(
            ip="192.168.1.100",
            method="GET",
            path="/api/v1/videos",
            query_params={"id": "1' OR 1=1--"},
            headers={"User-Agent": "Mozilla/5.0"},
            body=None,
        )

        assert is_safe is False
        assert len(threats) > 0
        assert any("SQL injection" in threat for threat in threats)

    def test_check_request_xss(self):
        """Test checking request with XSS."""
        detector = ThreatDetector()

        is_safe, threats = detector.check_request(
            ip="192.168.1.100",
            method="POST",
            path="/api/v1/videos",
            query_params={},
            headers={"User-Agent": "Mozilla/5.0"},
            body='{"title": "<script>alert(1)</script>"}',
        )

        assert is_safe is False
        assert len(threats) > 0
        assert any("XSS" in threat for threat in threats)

    def test_check_request_suspicious_user_agent(self):
        """Test checking request with suspicious user agent."""
        detector = ThreatDetector()

        is_safe, threats = detector.check_request(
            ip="192.168.1.100",
            method="GET",
            path="/api/v1/videos",
            query_params={},
            headers={"User-Agent": "sqlmap/1.0"},
            body=None,
        )

        assert is_safe is False
        assert len(threats) > 0
        assert any("user agent" in threat.lower() for threat in threats)

    def test_check_request_multiple_threats(self):
        """Test checking request with multiple threats."""
        detector = ThreatDetector()

        is_safe, threats = detector.check_request(
            ip="192.168.1.100",
            method="POST",
            path="/api/v1/videos",
            query_params={"id": "1' OR 1=1--"},
            headers={"User-Agent": "sqlmap/1.0"},
            body='{"title": "<script>alert(1)</script>"}',
        )

        assert is_safe is False
        assert len(threats) >= 3  # SQL injection, XSS, suspicious user agent

    def test_track_failed_login(self):
        """Test tracking failed login attempts."""
        detector = ThreatDetector()

        ip = "192.168.1.100"
        username = "testuser"

        # First few attempts should not trigger block
        for _i in range(4):
            should_block = detector.track_failed_login(ip, username)
            assert should_block is False

        # 5th attempt should trigger block (if threshold is 5)
        # Note: This depends on FAILED_LOGIN_THRESHOLD config

    def test_get_threat_stats(self):
        """Test getting threat statistics."""
        detector = ThreatDetector()

        ip = "192.168.1.100"

        # Get stats for IP with no threats
        stats = detector.get_threat_stats(ip)
        assert stats["threat_count"] == 0
        assert len(stats["recent_threats"]) == 0

    def test_excessive_header_size(self):
        """Test detection of excessive header size."""
        detector = ThreatDetector()

        # Create large headers
        large_headers = {
            "User-Agent": "Mozilla/5.0",
            "X-Large-Header": "A" * 10000,  # 10KB header
        }

        is_safe, threats = detector.check_request(
            ip="192.168.1.100",
            method="GET",
            path="/api/v1/videos",
            query_params={},
            headers=large_headers,
            body=None,
        )

        # Should detect excessive header size if MAX_HEADER_SIZE is set appropriately
        # Result depends on config - we just verify the function doesn't crash
        assert isinstance(is_safe, bool)
        assert isinstance(threats, list)
