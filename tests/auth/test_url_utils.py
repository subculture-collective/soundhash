"""
Tests for URL sanitization and validation utilities.
"""

import pytest

from src.auth.url_utils import build_callback_url, sanitize_callback_url


class TestSanitizeCallbackUrl:
    """Tests for the sanitize_callback_url function"""

    def test_valid_http_url(self):
        """Test sanitization of valid HTTP URL"""
        url = "http://example.com"
        result = sanitize_callback_url(url)
        assert result == "http://example.com"

    def test_valid_https_url(self):
        """Test sanitization of valid HTTPS URL"""
        url = "https://example.com"
        result = sanitize_callback_url(url)
        assert result == "https://example.com"

    def test_url_with_port(self):
        """Test sanitization of URL with port number"""
        url = "http://p1.com:8080"
        result = sanitize_callback_url(url)
        assert result == "http://p1.com:8080"

    def test_url_with_path(self):
        """Test sanitization of URL with path"""
        url = "https://example.com/api"
        result = sanitize_callback_url(url)
        assert result == "https://example.com/api"

    def test_url_with_trailing_slash(self):
        """Test that trailing slash is removed"""
        url = "https://example.com/"
        result = sanitize_callback_url(url)
        assert result == "https://example.com"

    def test_url_with_path_and_trailing_slash(self):
        """Test that trailing slash is removed from path"""
        url = "https://example.com/api/"
        result = sanitize_callback_url(url)
        assert result == "https://example.com/api"

    def test_url_with_query_parameters_raises_error(self):
        """Test that URL with query parameters raises ValueError"""
        url = "https://example.com?param=value"
        with pytest.raises(ValueError, match="should not contain query parameters"):
            sanitize_callback_url(url)

    def test_url_with_fragment_raises_error(self):
        """Test that URL with fragment raises ValueError"""
        url = "https://example.com#section"
        with pytest.raises(ValueError, match="should not contain.*fragments"):
            sanitize_callback_url(url)

    def test_invalid_scheme_raises_error(self):
        """Test that invalid scheme raises ValueError"""
        url = "ftp://example.com"
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            sanitize_callback_url(url)

    def test_missing_scheme_raises_error(self):
        """Test that URL without scheme raises ValueError"""
        url = "example.com"
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            sanitize_callback_url(url)

    def test_empty_url_raises_error(self):
        """Test that empty URL raises ValueError"""
        url = ""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            sanitize_callback_url(url)

    def test_none_url_raises_error(self):
        """Test that None URL raises ValueError"""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            sanitize_callback_url(None)

    def test_url_with_whitespace(self):
        """Test that URL with leading/trailing whitespace is stripped"""
        url = "  https://example.com  "
        result = sanitize_callback_url(url)
        assert result == "https://example.com"

    def test_missing_netloc_raises_error(self):
        """Test that URL without netloc raises ValueError"""
        url = "https://"
        with pytest.raises(ValueError, match="must contain a valid hostname"):
            sanitize_callback_url(url)

    def test_localhost_url(self):
        """Test sanitization of localhost URL"""
        url = "http://localhost:8000"
        result = sanitize_callback_url(url)
        assert result == "http://localhost:8000"

    def test_ip_address_url(self):
        """Test sanitization of IP address URL"""
        url = "http://192.168.1.1:8080"
        result = sanitize_callback_url(url)
        assert result == "http://192.168.1.1:8080"

    def test_complex_path(self):
        """Test sanitization of URL with complex path"""
        url = "https://api.example.com/v1/auth"
        result = sanitize_callback_url(url)
        assert result == "https://api.example.com/v1/auth"


class TestBuildCallbackUrl:
    """Tests for the build_callback_url function"""

    def test_build_simple_callback(self):
        """Test building a simple callback URL"""
        base = "https://example.com"
        path = "/auth/callback"
        result = build_callback_url(base, path)
        assert result == "https://example.com/auth/callback"

    def test_build_callback_with_port(self):
        """Test building callback URL with port"""
        base = "http://localhost:8000"
        path = "/auth/callback"
        result = build_callback_url(base, path)
        assert result == "http://localhost:8000/auth/callback"

    def test_build_callback_removes_trailing_slash(self):
        """Test that trailing slash is removed from base URL"""
        base = "https://example.com/"
        path = "/auth/callback"
        result = build_callback_url(base, path)
        assert result == "https://example.com/auth/callback"

    def test_build_callback_with_base_path(self):
        """Test building callback URL when base has path"""
        base = "https://example.com/api"
        path = "/auth/callback"
        result = build_callback_url(base, path)
        assert result == "https://example.com/api/auth/callback"

    def test_path_without_leading_slash_raises_error(self):
        """Test that path without leading slash raises ValueError"""
        base = "https://example.com"
        path = "auth/callback"
        with pytest.raises(ValueError, match="Path must start with /"):
            build_callback_url(base, path)

    def test_invalid_base_url_raises_error(self):
        """Test that invalid base URL raises ValueError"""
        base = "not-a-url"
        path = "/auth/callback"
        with pytest.raises(ValueError):
            build_callback_url(base, path)

    def test_build_callback_validates_base(self):
        """Test that build_callback_url validates base URL"""
        base = "ftp://example.com"
        path = "/auth/callback"
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            build_callback_url(base, path)

    def test_build_twitter_callback(self):
        """Test building Twitter OAuth callback URL"""
        base = "https://myapp.com"
        path = "/auth/twitter/callback"
        result = build_callback_url(base, path)
        assert result == "https://myapp.com/auth/twitter/callback"

    def test_build_reddit_callback(self):
        """Test building Reddit OAuth callback URL"""
        base = "https://myapp.com"
        path = "/auth/reddit/callback"
        result = build_callback_url(base, path)
        assert result == "https://myapp.com/auth/reddit/callback"

    def test_prevent_url_injection(self):
        """Test that URL injection attempts are prevented"""
        # This tests the security issue from the GitHub alert
        # Even if base_url contains http://p1.com:8080, it should be properly sanitized
        base = "http://p1.com:8080"
        path = "/auth/callback"
        result = build_callback_url(base, path)
        assert result == "http://p1.com:8080/auth/callback"
        # Verify the result starts with the sanitized base
        assert result.startswith("http://p1.com:8080")

    def test_prevent_query_injection_in_base(self):
        """Test that query parameters in base URL are rejected"""
        base = "https://example.com?malicious=true"
        path = "/auth/callback"
        with pytest.raises(ValueError, match="should not contain query parameters"):
            build_callback_url(base, path)
