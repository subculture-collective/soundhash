"""Tests for CDN management functionality."""

import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError
from src.cdn.cdn_manager import CDNManager


class TestCDNManager:
    """Test cases for CDNManager class."""

    def test_init(self):
        """Test CDNManager initialization."""
        manager = CDNManager()
        assert manager is not None

    def test_init_disabled(self, monkeypatch):
        """Test initialization when CDN is disabled."""
        monkeypatch.setattr("config.settings.Config.CDN_ENABLED", False)
        
        manager = CDNManager()
        assert manager.enabled is False
        assert manager.cloudfront_client is None

    @patch("boto3.client")
    def test_invalidate_cache(self, mock_boto_client, monkeypatch):
        """Test cache invalidation."""
        monkeypatch.setattr("config.settings.Config.CDN_ENABLED", True)
        monkeypatch.setattr("config.settings.Config.CDN_PROVIDER", "cloudfront")
        monkeypatch.setattr("config.settings.Config.CLOUDFRONT_DISTRIBUTION_ID", "E123456")
        
        # Mock CloudFront client
        mock_client = Mock()
        mock_client.create_invalidation.return_value = {
            "Invalidation": {"Id": "INV123"}
        }
        mock_boto_client.return_value = mock_client
        
        manager = CDNManager()
        manager.cloudfront_client = mock_client
        
        result = manager.invalidate_cache(["/static/*", "/api/*"])
        
        assert result == "INV123"
        mock_client.create_invalidation.assert_called_once()

    @patch("boto3.client")
    def test_invalidate_cache_error(self, mock_boto_client, monkeypatch):
        """Test cache invalidation with error."""
        monkeypatch.setattr("config.settings.Config.CDN_ENABLED", True)
        monkeypatch.setattr("config.settings.Config.CDN_PROVIDER", "cloudfront")
        monkeypatch.setattr("config.settings.Config.CLOUDFRONT_DISTRIBUTION_ID", "E123456")
        
        # Mock CloudFront client with error
        mock_client = Mock()
        mock_client.create_invalidation.side_effect = ClientError(
            {"Error": {"Code": "InvalidArgument", "Message": "Invalid path"}},
            "create_invalidation"
        )
        mock_boto_client.return_value = mock_client
        
        manager = CDNManager()
        manager.cloudfront_client = mock_client
        
        result = manager.invalidate_cache(["/invalid/*"])
        
        assert result is None

    @patch("boto3.client")
    def test_get_invalidation_status(self, mock_boto_client, monkeypatch):
        """Test getting invalidation status."""
        monkeypatch.setattr("config.settings.Config.CDN_ENABLED", True)
        monkeypatch.setattr("config.settings.Config.CDN_PROVIDER", "cloudfront")
        monkeypatch.setattr("config.settings.Config.CLOUDFRONT_DISTRIBUTION_ID", "E123456")
        
        # Mock CloudFront client
        mock_client = Mock()
        mock_client.get_invalidation.return_value = {
            "Invalidation": {"Status": "Completed"}
        }
        mock_boto_client.return_value = mock_client
        
        manager = CDNManager()
        manager.cloudfront_client = mock_client
        
        status = manager.get_invalidation_status("INV123")
        
        assert status == "Completed"
        mock_client.get_invalidation.assert_called_once_with(
            DistributionId="E123456",
            Id="INV123"
        )

    @patch("boto3.client")
    def test_purge_all(self, mock_boto_client, monkeypatch):
        """Test purging all cache."""
        monkeypatch.setattr("config.settings.Config.CDN_ENABLED", True)
        monkeypatch.setattr("config.settings.Config.CDN_PROVIDER", "cloudfront")
        monkeypatch.setattr("config.settings.Config.CLOUDFRONT_DISTRIBUTION_ID", "E123456")
        
        # Mock CloudFront client
        mock_client = Mock()
        mock_client.create_invalidation.return_value = {
            "Invalidation": {"Id": "INV123"}
        }
        mock_boto_client.return_value = mock_client
        
        manager = CDNManager()
        manager.cloudfront_client = mock_client
        
        result = manager.purge_all()
        
        assert result == "INV123"
        # Verify it invalidates everything
        call_args = mock_client.create_invalidation.call_args
        paths = call_args[1]["InvalidationBatch"]["Paths"]["Items"]
        assert "/*" in paths

    @patch("boto3.client")
    def test_purge_static_assets(self, mock_boto_client, monkeypatch):
        """Test purging static assets."""
        monkeypatch.setattr("config.settings.Config.CDN_ENABLED", True)
        monkeypatch.setattr("config.settings.Config.CDN_PROVIDER", "cloudfront")
        monkeypatch.setattr("config.settings.Config.CLOUDFRONT_DISTRIBUTION_ID", "E123456")
        
        # Mock CloudFront client
        mock_client = Mock()
        mock_client.create_invalidation.return_value = {
            "Invalidation": {"Id": "INV123"}
        }
        mock_boto_client.return_value = mock_client
        
        manager = CDNManager()
        manager.cloudfront_client = mock_client
        
        result = manager.purge_static_assets()
        
        assert result == "INV123"

    @patch("boto3.client")
    def test_purge_api_cache(self, mock_boto_client, monkeypatch):
        """Test purging API cache."""
        monkeypatch.setattr("config.settings.Config.CDN_ENABLED", True)
        monkeypatch.setattr("config.settings.Config.CDN_PROVIDER", "cloudfront")
        monkeypatch.setattr("config.settings.Config.CLOUDFRONT_DISTRIBUTION_ID", "E123456")
        
        # Mock CloudFront client
        mock_client = Mock()
        mock_client.create_invalidation.return_value = {
            "Invalidation": {"Id": "INV123"}
        }
        mock_boto_client.return_value = mock_client
        
        manager = CDNManager()
        manager.cloudfront_client = mock_client
        
        # Test with specific endpoint
        result = manager.purge_api_cache("/api/videos/*")
        assert result == "INV123"
        
        # Test without endpoint (purge all API)
        result = manager.purge_api_cache()
        assert result == "INV123"

    @patch("boto3.client")
    def test_get_distribution_config(self, mock_boto_client, monkeypatch):
        """Test getting distribution configuration."""
        monkeypatch.setattr("config.settings.Config.CDN_ENABLED", True)
        monkeypatch.setattr("config.settings.Config.CDN_PROVIDER", "cloudfront")
        monkeypatch.setattr("config.settings.Config.CLOUDFRONT_DISTRIBUTION_ID", "E123456")
        
        # Mock CloudFront client
        mock_client = Mock()
        mock_config = {"Enabled": True, "Comment": "Test Distribution"}
        mock_client.get_distribution_config.return_value = {
            "DistributionConfig": mock_config
        }
        mock_boto_client.return_value = mock_client
        
        manager = CDNManager()
        manager.cloudfront_client = mock_client
        
        config = manager.get_distribution_config()
        
        assert config is not None
        assert config["Enabled"] is True

    @patch("boto3.client")
    def test_enable_distribution(self, mock_boto_client, monkeypatch):
        """Test enabling distribution."""
        monkeypatch.setattr("config.settings.Config.CDN_ENABLED", True)
        monkeypatch.setattr("config.settings.Config.CDN_PROVIDER", "cloudfront")
        monkeypatch.setattr("config.settings.Config.CLOUDFRONT_DISTRIBUTION_ID", "E123456")
        
        # Mock CloudFront client
        mock_client = Mock()
        mock_config = {"Enabled": False}
        mock_client.get_distribution_config.return_value = {
            "DistributionConfig": mock_config,
            "ETag": "ETAG123"
        }
        mock_client.update_distribution.return_value = {}
        mock_boto_client.return_value = mock_client
        
        manager = CDNManager()
        manager.cloudfront_client = mock_client
        
        result = manager.enable_distribution()
        
        assert result is True
        mock_client.update_distribution.assert_called_once()

    @patch("boto3.client")
    def test_disable_distribution(self, mock_boto_client, monkeypatch):
        """Test disabling distribution."""
        monkeypatch.setattr("config.settings.Config.CDN_ENABLED", True)
        monkeypatch.setattr("config.settings.Config.CDN_PROVIDER", "cloudfront")
        monkeypatch.setattr("config.settings.Config.CLOUDFRONT_DISTRIBUTION_ID", "E123456")
        
        # Mock CloudFront client
        mock_client = Mock()
        mock_config = {"Enabled": True}
        mock_client.get_distribution_config.return_value = {
            "DistributionConfig": mock_config,
            "ETag": "ETAG123"
        }
        mock_client.update_distribution.return_value = {}
        mock_boto_client.return_value = mock_client
        
        manager = CDNManager()
        manager.cloudfront_client = mock_client
        
        result = manager.disable_distribution()
        
        assert result is True
        mock_client.update_distribution.assert_called_once()

    @patch("boto3.client")
    def test_get_cache_statistics(self, mock_boto_client, monkeypatch):
        """Test getting cache statistics."""
        monkeypatch.setattr("config.settings.Config.CDN_ENABLED", True)
        monkeypatch.setattr("config.settings.Config.CDN_PROVIDER", "cloudfront")
        monkeypatch.setattr("config.settings.Config.CLOUDFRONT_DISTRIBUTION_ID", "E123456")
        
        # Mock CloudFront and CloudWatch clients
        mock_cf_client = Mock()
        mock_cw_client = Mock()
        mock_cw_client.get_metric_statistics.return_value = {
            "Datapoints": [{"Average": 95.5}]
        }
        
        with patch("boto3.client") as mock_boto:
            def client_factory(service):
                if service == "cloudfront":
                    return mock_cf_client
                elif service == "cloudwatch":
                    return mock_cw_client
                return Mock()
            
            mock_boto.side_effect = client_factory
            
            manager = CDNManager()
            manager.cloudfront_client = mock_cf_client
            
            stats = manager.get_cache_statistics()
            
            assert stats is not None
            assert "cache_hit_rate" in stats
            assert stats["cache_hit_rate"] == 95.5

    def test_disabled_operations(self, monkeypatch):
        """Test operations when CDN is disabled."""
        monkeypatch.setattr("config.settings.Config.CDN_ENABLED", False)
        
        manager = CDNManager()
        
        # All operations should return None or False when disabled
        assert manager.invalidate_cache(["/test/*"]) is None
        assert manager.get_invalidation_status("INV123") is None
        assert manager.purge_all() is None
        assert manager.get_distribution_config() is None
        assert manager.enable_distribution() is False
        assert manager.disable_distribution() is False
        assert manager.get_cache_statistics() is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
