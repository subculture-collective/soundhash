"""Tests for configuration settings."""

import os
from unittest.mock import patch

from config.settings import Config


class TestConfig:
    """Test suite for Config class."""

    def test_config_has_expected_attributes(self):
        """Test that Config has expected attributes."""
        assert hasattr(Config, "DATABASE_URL")
        assert hasattr(Config, "DATABASE_HOST")
        assert hasattr(Config, "DATABASE_PORT")
        assert hasattr(Config, "DATABASE_NAME")
        assert hasattr(Config, "TEMP_DIR")
        assert hasattr(Config, "SEGMENT_LENGTH_SECONDS")
        assert hasattr(Config, "FINGERPRINT_SAMPLE_RATE")

    def test_config_default_values(self):
        """Test that Config has reasonable default values."""
        assert Config.DATABASE_HOST == "localhost"
        assert Config.DATABASE_PORT == 5432
        assert Config.DATABASE_NAME == "soundhash"
        assert Config.TEMP_DIR == "./temp"
        assert Config.SEGMENT_LENGTH_SECONDS == 90
        assert Config.FINGERPRINT_SAMPLE_RATE == 22050

    def test_get_database_url_with_url(self):
        """Test get_database_url when DATABASE_URL is set."""
        with patch.object(Config, "DATABASE_URL", "postgresql://test:test@localhost/testdb"):
            url = Config.get_database_url()
            assert url == "postgresql://test:test@localhost/testdb"

    def test_get_database_url_without_url(self):
        """Test get_database_url when DATABASE_URL is not set."""
        with patch.object(Config, "DATABASE_URL", None):
            with patch.object(Config, "DATABASE_USER", "testuser"):
                with patch.object(Config, "DATABASE_PASSWORD", "testpass"):
                    with patch.object(Config, "DATABASE_HOST", "testhost"):
                        with patch.object(Config, "DATABASE_PORT", 5433):
                            with patch.object(Config, "DATABASE_NAME", "testdb"):
                                url = Config.get_database_url()
                                assert url == "postgresql://testuser:testpass@testhost:5433/testdb"

    def test_config_boolean_flags(self):
        """Test boolean configuration flags."""
        # These should be boolean values
        assert isinstance(Config.KEEP_ORIGINAL_AUDIO, bool)
        assert isinstance(Config.CLEANUP_SEGMENTS_AFTER_PROCESSING, bool)
        assert isinstance(Config.USE_PROXY, bool)

    def test_config_proxy_list(self):
        """Test that PROXY_LIST is a list."""
        assert isinstance(Config.PROXY_LIST, list)

    def test_config_target_channels(self):
        """Test that TARGET_CHANNELS is a list."""
        assert isinstance(Config.TARGET_CHANNELS, list)

    def test_proxy_list_comma_separated_parsing(self):
        """Test that PROXY_LIST correctly parses comma-separated values from env var."""
        # Test with comma-separated proxy list
        test_proxy_list = "http://proxy1.example.com:8080,http://proxy2.example.com:8080,http://proxy3.example.com:8080"
        with patch.dict(os.environ, {"PROXY_LIST": test_proxy_list}, clear=False):
            # Need to reload the module to pick up the new env var
            import importlib
            import config.settings
            importlib.reload(config.settings)
            from config.settings import Config as ReloadedConfig
            
            assert isinstance(ReloadedConfig.PROXY_LIST, list)
            assert len(ReloadedConfig.PROXY_LIST) == 3
            assert ReloadedConfig.PROXY_LIST[0] == "http://proxy1.example.com:8080"
            assert ReloadedConfig.PROXY_LIST[1] == "http://proxy2.example.com:8080"
            assert ReloadedConfig.PROXY_LIST[2] == "http://proxy3.example.com:8080"

    def test_proxy_list_single_proxy(self):
        """Test that PROXY_LIST correctly handles single proxy (no commas)."""
        test_proxy = "http://single-proxy.example.com:8080"
        with patch.dict(os.environ, {"PROXY_LIST": test_proxy}, clear=False):
            import importlib
            import config.settings
            importlib.reload(config.settings)
            from config.settings import Config as ReloadedConfig
            
            assert isinstance(ReloadedConfig.PROXY_LIST, list)
            assert len(ReloadedConfig.PROXY_LIST) == 1
            assert ReloadedConfig.PROXY_LIST[0] == "http://single-proxy.example.com:8080"

    def test_proxy_list_empty_string(self):
        """Test that PROXY_LIST returns empty list when env var is empty."""
        with patch.dict(os.environ, {"PROXY_LIST": ""}, clear=False):
            import importlib
            import config.settings
            importlib.reload(config.settings)
            from config.settings import Config as ReloadedConfig
            
            assert isinstance(ReloadedConfig.PROXY_LIST, list)
            assert len(ReloadedConfig.PROXY_LIST) == 0

    def test_proxy_list_not_set(self):
        """Test that PROXY_LIST returns empty list when env var is not set."""
        # Remove PROXY_LIST from env if it exists
        env_copy = os.environ.copy()
        if "PROXY_LIST" in env_copy:
            del env_copy["PROXY_LIST"]
        
        with patch.dict(os.environ, env_copy, clear=True):
            import importlib
            import config.settings
            importlib.reload(config.settings)
            from config.settings import Config as ReloadedConfig
            
            assert isinstance(ReloadedConfig.PROXY_LIST, list)
            assert len(ReloadedConfig.PROXY_LIST) == 0
