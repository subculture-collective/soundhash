"""Tests for regional routing functionality."""

import pytest
from src.cdn.regional_router import RegionalRouter


class TestRegionalRouter:
    """Test cases for RegionalRouter class."""

    def test_init(self):
        """Test RegionalRouter initialization."""
        router = RegionalRouter()
        assert router is not None
        assert router.primary_region == "us-east-1"
        assert "us-east-1" in router.regions

    def test_get_database_endpoint_write(self, monkeypatch):
        """Test write operations always go to primary."""
        monkeypatch.setattr("config.settings.Config.MULTI_REGION_ENABLED", True)
        monkeypatch.setattr("config.settings.Config.PRIMARY_REGION", "us-east-1")
        
        router = RegionalRouter()
        endpoint = router.get_database_endpoint(operation="write")
        
        # Should return primary endpoint
        assert endpoint is not None
        assert "us-east-1" in router.db_endpoints

    def test_get_database_endpoint_read(self, monkeypatch):
        """Test read operations can use regional endpoints."""
        monkeypatch.setattr("config.settings.Config.MULTI_REGION_ENABLED", True)
        monkeypatch.setattr("config.settings.Config.PRIMARY_REGION", "us-east-1")
        
        router = RegionalRouter()
        endpoint = router.get_database_endpoint(operation="read", region="eu-west-1")
        
        assert endpoint is not None

    def test_get_database_endpoint_disabled(self, monkeypatch):
        """Test behavior when multi-region is disabled."""
        monkeypatch.setattr("config.settings.Config.MULTI_REGION_ENABLED", False)
        
        router = RegionalRouter()
        endpoint = router.get_database_endpoint(operation="read", region="eu-west-1")
        
        # Should return primary endpoint regardless of region
        assert endpoint is not None

    def test_map_country_to_region(self):
        """Test country code to region mapping."""
        router = RegionalRouter()
        
        # European countries
        assert router._map_country_to_region("GB") == "eu-west-1"
        assert router._map_country_to_region("DE") == "eu-west-1"
        assert router._map_country_to_region("FR") == "eu-west-1"
        
        # APAC countries
        assert router._map_country_to_region("JP") == "ap-southeast-1"
        assert router._map_country_to_region("SG") == "ap-southeast-1"
        assert router._map_country_to_region("AU") == "ap-southeast-1"
        
        # Default to US
        assert router._map_country_to_region("US") == "us-east-1"
        assert router._map_country_to_region("CA") == "us-east-1"

    def test_measure_latency(self):
        """Test latency measurement."""
        router = RegionalRouter()
        
        # Should return some latency value
        latency_us = router.measure_latency("us-east-1")
        assert latency_us > 0
        
        latency_eu = router.measure_latency("eu-west-1")
        assert latency_eu > 0
        
        latency_apac = router.measure_latency("ap-southeast-1")
        assert latency_apac > 0

    def test_measure_latency_caching(self):
        """Test latency measurement caching."""
        router = RegionalRouter()
        
        # First measurement
        latency1 = router.measure_latency("us-east-1")
        
        # Second measurement should use cache
        latency2 = router.measure_latency("us-east-1")
        
        assert latency1 == latency2

    def test_select_optimal_region_disabled(self, monkeypatch):
        """Test region selection when multi-region is disabled."""
        monkeypatch.setattr("config.settings.Config.MULTI_REGION_ENABLED", False)
        
        router = RegionalRouter()
        region = router.select_optimal_region()
        
        assert region == router.primary_region

    def test_select_optimal_region_geo(self, monkeypatch):
        """Test geolocation-based region selection."""
        monkeypatch.setattr("config.settings.Config.MULTI_REGION_ENABLED", True)
        monkeypatch.setattr("config.settings.Config.GEO_ROUTING_ENABLED", True)
        
        router = RegionalRouter()
        # Would need actual IP geolocation for full test
        region = router.select_optimal_region()
        
        assert region in router.regions

    def test_select_optimal_region_latency(self, monkeypatch):
        """Test latency-based region selection."""
        monkeypatch.setattr("config.settings.Config.MULTI_REGION_ENABLED", True)
        monkeypatch.setattr("config.settings.Config.LATENCY_ROUTING_ENABLED", True)
        
        router = RegionalRouter()
        region = router.select_optimal_region()
        
        assert region in router.regions

    def test_check_regional_health(self):
        """Test regional health check."""
        router = RegionalRouter()
        
        # All regions should be healthy by default
        assert router.check_regional_health("us-east-1") is True
        assert router.check_regional_health("eu-west-1") is True
        assert router.check_regional_health("ap-southeast-1") is True
        
        # Non-existent region
        assert router.check_regional_health("non-existent") is False

    def test_get_failover_region(self, monkeypatch):
        """Test failover region selection."""
        monkeypatch.setattr("config.settings.Config.AUTO_FAILOVER_ENABLED", True)
        
        router = RegionalRouter()
        
        # If primary fails, should return secondary
        failover = router.get_failover_region("us-east-1")
        assert failover != "us-east-1"
        assert failover in router.regions
        
        # If secondary fails, should return primary
        failover = router.get_failover_region("eu-west-1")
        assert failover == "us-east-1"

    def test_get_failover_region_disabled(self, monkeypatch):
        """Test failover when auto-failover is disabled."""
        monkeypatch.setattr("config.settings.Config.AUTO_FAILOVER_ENABLED", False)
        
        router = RegionalRouter()
        failover = router.get_failover_region("eu-west-1")
        
        # Should return primary
        assert failover == router.primary_region

    def test_enforce_data_residency_disabled(self, monkeypatch):
        """Test data residency when enforcement is disabled."""
        monkeypatch.setattr("config.settings.Config.DATA_RESIDENCY_ENFORCEMENT", False)
        
        router = RegionalRouter()
        result = router.enforce_data_residency("us-east-1", "DE")
        
        # Should always return True when disabled
        assert result is True

    def test_enforce_data_residency_eu(self, monkeypatch):
        """Test EU data residency enforcement."""
        monkeypatch.setattr("config.settings.Config.DATA_RESIDENCY_ENFORCEMENT", True)
        monkeypatch.setattr("config.settings.Config.EU_DATA_RESIDENCY", True)
        
        router = RegionalRouter()
        
        # EU country should require EU region
        assert router.enforce_data_residency("eu-west-1", "DE") is True
        assert router.enforce_data_residency("us-east-1", "DE") is False

    def test_enforce_data_residency_apac(self, monkeypatch):
        """Test APAC data residency enforcement."""
        monkeypatch.setattr("config.settings.Config.DATA_RESIDENCY_ENFORCEMENT", True)
        monkeypatch.setattr("config.settings.Config.APAC_DATA_RESIDENCY", True)
        
        router = RegionalRouter()
        
        # APAC country should require APAC region
        assert router.enforce_data_residency("ap-southeast-1", "JP") is True
        assert router.enforce_data_residency("us-east-1", "JP") is False

    def test_get_reader_endpoint(self, monkeypatch):
        """Test reader endpoint selection."""
        monkeypatch.setattr("config.settings.Config.MULTI_REGION_ENABLED", True)
        
        router = RegionalRouter()
        endpoint = router.get_reader_endpoint("eu-west-1")
        
        assert endpoint is not None

    def test_get_reader_endpoint_with_replicas(self, monkeypatch):
        """Test reader endpoint with configured replicas."""
        monkeypatch.setattr("config.settings.Config.MULTI_REGION_ENABLED", True)
        monkeypatch.setattr(
            "config.settings.Config.DATABASE_READER_ENDPOINTS",
            ["replica1.example.com", "replica2.example.com"]
        )
        
        router = RegionalRouter()
        endpoint = router.get_reader_endpoint()
        
        # Should return one of the reader endpoints
        assert endpoint in ["replica1.example.com", "replica2.example.com"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
