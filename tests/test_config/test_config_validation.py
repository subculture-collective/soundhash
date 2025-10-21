"""Tests for configuration validation and error handling."""

import os
import pytest
from unittest.mock import patch

from config.settings import Config


class TestConfigValidation:
    """Test suite for Config validation."""

    def test_config_is_singleton(self):
        """Test that Config is a singleton instance."""
        from config.settings import Config as Config1
        from config.settings import Config as Config2
        assert Config1 is Config2

    def test_missing_database_credentials_raises_clear_error(self):
        """Test that missing database credentials raises a clear error."""
        with patch.object(Config, "DATABASE_URL", None):
            with patch.object(Config, "DATABASE_USER", None):
                with patch.object(Config, "DATABASE_PASSWORD", None):
                    with pytest.raises(ValueError) as exc_info:
                        Config.get_database_url()
                    
                    error_message = str(exc_info.value)
                    assert "Database configuration incomplete" in error_message
                    assert "DATABASE_URL" in error_message
                    assert "DATABASE_USER" in error_message
                    assert "DATABASE_PASSWORD" in error_message

    def test_database_url_provided_bypasses_credential_check(self):
        """Test that providing DATABASE_URL bypasses credential validation."""
        with patch.object(Config, "DATABASE_URL", "postgresql://test:test@localhost/testdb"):
            with patch.object(Config, "DATABASE_USER", None):
                with patch.object(Config, "DATABASE_PASSWORD", None):
                    url = Config.get_database_url()
                    assert url == "postgresql://test:test@localhost/testdb"

    def test_partial_database_credentials_raises_error(self):
        """Test that partial credentials (only user, no password) raises error."""
        with patch.object(Config, "DATABASE_URL", None):
            with patch.object(Config, "DATABASE_USER", "testuser"):
                with patch.object(Config, "DATABASE_PASSWORD", None):
                    with pytest.raises(ValueError) as exc_info:
                        Config.get_database_url()
                    assert "Database configuration incomplete" in str(exc_info.value)

    def test_empty_proxy_list_returns_empty_list(self):
        """Test that empty PROXY_LIST returns empty list."""
        with patch.object(Config, "PROXY_LIST_STR", ""):
            assert Config.PROXY_LIST == []

    def test_single_proxy_in_list(self):
        """Test that single proxy is correctly parsed."""
        with patch.object(Config, "PROXY_LIST_STR", "http://proxy.example.com:8080"):
            assert len(Config.PROXY_LIST) == 1
            assert Config.PROXY_LIST[0] == "http://proxy.example.com:8080"

    def test_multiple_proxies_in_list(self):
        """Test that multiple proxies are correctly parsed."""
        with patch.object(Config, "PROXY_LIST_STR", "http://p1.com:8080,http://p2.com:8080"):
            assert len(Config.PROXY_LIST) == 2
            assert "http://p1.com:8080" in Config.PROXY_LIST
            assert "http://p2.com:8080" in Config.PROXY_LIST

    def test_proxy_list_strips_whitespace(self):
        """Test that proxy list strips whitespace around entries."""
        with patch.object(Config, "PROXY_LIST_STR", "http://p1.com:8080 , http://p2.com:8080"):
            assert len(Config.PROXY_LIST) == 2
            # All entries should be stripped
            for proxy in Config.PROXY_LIST:
                assert proxy == proxy.strip()

    def test_empty_target_channels_returns_empty_list(self):
        """Test that empty TARGET_CHANNELS returns empty list."""
        with patch.object(Config, "TARGET_CHANNELS_STR", ""):
            assert Config.TARGET_CHANNELS == []

    def test_target_channels_parsing(self):
        """Test that target channels are correctly parsed."""
        with patch.object(Config, "TARGET_CHANNELS_STR", "UC123,UC456,UC789"):
            assert len(Config.TARGET_CHANNELS) == 3
            assert "UC123" in Config.TARGET_CHANNELS
            assert "UC456" in Config.TARGET_CHANNELS
            assert "UC789" in Config.TARGET_CHANNELS

    def test_bot_keywords_default_value(self):
        """Test that BOT_KEYWORDS has default value when empty."""
        with patch.object(Config, "BOT_KEYWORDS_STR", ""):
            keywords = Config.BOT_KEYWORDS
            assert isinstance(keywords, list)
            assert len(keywords) > 0
            assert "find clip" in keywords

    def test_bot_keywords_custom_parsing(self):
        """Test that custom BOT_KEYWORDS are correctly parsed."""
        with patch.object(Config, "BOT_KEYWORDS_STR", "keyword1,keyword2,keyword3"):
            assert len(Config.BOT_KEYWORDS) == 3
            assert "keyword1" in Config.BOT_KEYWORDS
            assert "keyword2" in Config.BOT_KEYWORDS
            assert "keyword3" in Config.BOT_KEYWORDS

    def test_config_has_all_expected_attributes(self):
        """Test that Config has all expected configuration attributes."""
        expected_attrs = [
            "DATABASE_URL", "DATABASE_HOST", "DATABASE_PORT", "DATABASE_NAME",
            "DATABASE_USER", "DATABASE_PASSWORD",
            "YOUTUBE_API_KEY",
            "TEMP_DIR", "SEGMENT_LENGTH_SECONDS", "FINGERPRINT_SAMPLE_RATE",
            "MAX_CONCURRENT_DOWNLOADS", "MAX_CONCURRENT_CHANNELS",
            "USE_PROXY", "PROXY_URL", "PROXY_LIST",
            "YT_COOKIES_FILE", "YT_COOKIES_FROM_BROWSER", "YT_BROWSER_PROFILE",
            "YT_PLAYER_CLIENT",
            "TARGET_CHANNELS", "BOT_NAME", "BOT_KEYWORDS",
            "KEEP_ORIGINAL_AUDIO", "CLEANUP_SEGMENTS_AFTER_PROCESSING",
            "CHANNEL_RETRY_DELAY", "CHANNEL_MAX_RETRIES",
        ]
        
        for attr in expected_attrs:
            assert hasattr(Config, attr), f"Config missing attribute: {attr}"

    def test_config_defaults_are_sensible(self):
        """Test that Config default values are sensible."""
        assert Config.DATABASE_HOST == "localhost"
        assert Config.DATABASE_PORT == 5432
        assert Config.DATABASE_NAME == "soundhash"
        assert Config.TEMP_DIR == "./temp"
        assert Config.SEGMENT_LENGTH_SECONDS == 90
        assert Config.FINGERPRINT_SAMPLE_RATE == 22050
        assert Config.MAX_CONCURRENT_DOWNLOADS == 3
        assert Config.MAX_CONCURRENT_CHANNELS == 2
        assert Config.USE_PROXY is False
        assert Config.KEEP_ORIGINAL_AUDIO is True
        assert Config.CLEANUP_SEGMENTS_AFTER_PROCESSING is True

    def test_boolean_config_values(self):
        """Test that boolean configuration values work correctly."""
        assert isinstance(Config.USE_PROXY, bool)
        assert isinstance(Config.KEEP_ORIGINAL_AUDIO, bool)
        assert isinstance(Config.CLEANUP_SEGMENTS_AFTER_PROCESSING, bool)

    def test_integer_config_values(self):
        """Test that integer configuration values work correctly."""
        assert isinstance(Config.DATABASE_PORT, int)
        assert isinstance(Config.AUTH_SERVER_PORT, int)
        assert isinstance(Config.MAX_CONCURRENT_DOWNLOADS, int)
        assert isinstance(Config.MAX_CONCURRENT_CHANNELS, int)
        assert isinstance(Config.SEGMENT_LENGTH_SECONDS, int)
        assert isinstance(Config.FINGERPRINT_SAMPLE_RATE, int)
        assert isinstance(Config.CHANNEL_RETRY_DELAY, int)
        assert isinstance(Config.CHANNEL_MAX_RETRIES, int)

    def test_list_config_values(self):
        """Test that list configuration values work correctly."""
        assert isinstance(Config.PROXY_LIST, list)
        assert isinstance(Config.TARGET_CHANNELS, list)
        assert isinstance(Config.BOT_KEYWORDS, list)
