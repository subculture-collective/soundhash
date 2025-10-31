"""Regional routing and database endpoint selection."""

import random
import time
from typing import Optional, Dict
from config.settings import Config


class RegionalRouter:
    """Handles regional routing and database endpoint selection."""

    def __init__(self):
        self.multi_region_enabled = Config.MULTI_REGION_ENABLED
        self.primary_region = Config.PRIMARY_REGION
        self.regions = Config.REGIONS
        self.geo_routing_enabled = Config.GEO_ROUTING_ENABLED
        self.latency_routing_enabled = Config.LATENCY_ROUTING_ENABLED
        
        # Regional database endpoints
        self.db_endpoints = {
            "us-east-1": Config.get_database_url(),
            "eu-west-1": Config.DATABASE_REPLICA_EU_ENDPOINT or Config.get_database_url(),
            "ap-southeast-1": Config.DATABASE_REPLICA_APAC_ENDPOINT or Config.get_database_url(),
        }
        
        # Reader endpoints for load balancing
        self.db_reader_endpoints = Config.DATABASE_READER_ENDPOINTS
        
        # Latency tracking
        self._latency_cache: Dict[str, Dict[str, float]] = {}
        self._cache_ttl = 60  # seconds

    def get_database_endpoint(
        self, operation: str = "read", region: Optional[str] = None, client_ip: Optional[str] = None
    ) -> str:
        """
        Get the appropriate database endpoint based on region and operation type.

        Args:
            operation: 'read' or 'write'
            region: Target region (e.g., 'us-east-1', 'eu-west-1', 'ap-southeast-1')
            client_ip: Client IP address for geo-routing

        Returns:
            Database connection string
        """
        if not self.multi_region_enabled:
            return Config.get_database_url()

        # Writes always go to primary
        if operation == "write":
            return self.db_endpoints.get(self.primary_region, Config.get_database_url())

        # Determine target region
        target_region = region
        if not target_region and client_ip:
            target_region = self._get_region_from_ip(client_ip)
        if not target_region:
            target_region = self.primary_region

        # Get regional endpoint
        endpoint = self.db_endpoints.get(target_region)
        
        # Fall back to primary if regional endpoint not configured
        if not endpoint or endpoint == "":
            endpoint = self.db_endpoints.get(self.primary_region, Config.get_database_url())

        return endpoint

    def get_reader_endpoint(self, region: Optional[str] = None) -> str:
        """
        Get a read replica endpoint with load balancing.

        Args:
            region: Target region

        Returns:
            Database reader endpoint
        """
        if not self.multi_region_enabled or not self.db_reader_endpoints:
            return self.get_database_endpoint("read", region)

        # Simple round-robin selection (could be enhanced with health checks)
        return random.choice(self.db_reader_endpoints)

    def _get_region_from_ip(self, client_ip: str) -> str:
        """
        Determine region from client IP address.

        Args:
            client_ip: Client IP address

        Returns:
            Region identifier
        """
        # In production, use a GeoIP library or service
        # For now, return primary region as fallback
        # Example implementation with maxminddb:
        # import maxminddb
        # reader = maxminddb.open_database('GeoLite2-City.mmdb')
        # response = reader.get(client_ip)
        # if response and 'country' in response:
        #     country_code = response['country']['iso_code']
        #     return self._map_country_to_region(country_code)
        
        return self.primary_region

    def _map_country_to_region(self, country_code: str) -> str:
        """
        Map country code to AWS region.

        Args:
            country_code: ISO country code

        Returns:
            AWS region
        """
        # European countries
        eu_countries = {
            "GB", "FR", "DE", "ES", "IT", "NL", "BE", "SE", "NO", "DK", "FI",
            "PL", "RO", "PT", "GR", "CZ", "HU", "AT", "CH", "IE"
        }
        
        # APAC countries
        apac_countries = {
            "JP", "CN", "KR", "SG", "HK", "TW", "IN", "AU", "NZ", "TH", "MY",
            "ID", "PH", "VN", "PK", "BD"
        }
        
        if country_code in eu_countries:
            return "eu-west-1"
        elif country_code in apac_countries:
            return "ap-southeast-1"
        else:
            return "us-east-1"

    def measure_latency(self, region: str) -> float:
        """
        Measure latency to a specific region.

        Args:
            region: Target region

        Returns:
            Latency in milliseconds
        """
        # Check cache
        cache_key = f"latency_{region}"
        now = time.time()
        
        if cache_key in self._latency_cache:
            cached_data = self._latency_cache[cache_key]
            if now - cached_data["timestamp"] < self._cache_ttl:
                return cached_data["latency"]

        # In production, implement actual latency measurement
        # For now, return estimated latency based on region
        estimated_latencies = {
            "us-east-1": 50.0,
            "eu-west-1": 100.0,
            "ap-southeast-1": 200.0,
        }
        
        latency = estimated_latencies.get(region, 100.0)
        
        # Cache result
        self._latency_cache[cache_key] = {"latency": latency, "timestamp": now}
        
        return latency

    def select_optimal_region(self, client_ip: Optional[str] = None) -> str:
        """
        Select optimal region based on latency or geography.

        Args:
            client_ip: Client IP address

        Returns:
            Optimal region identifier
        """
        if not self.multi_region_enabled:
            return self.primary_region

        if self.geo_routing_enabled and client_ip:
            return self._get_region_from_ip(client_ip)

        if self.latency_routing_enabled:
            # Measure latency to all regions
            latencies = {region: self.measure_latency(region) for region in self.regions}
            # Return region with lowest latency
            return min(latencies, key=latencies.get)

        return self.primary_region

    def check_regional_health(self, region: str) -> bool:
        """
        Check health of a specific region.

        Args:
            region: Region to check

        Returns:
            True if healthy, False otherwise
        """
        # In production, implement actual health checks
        # For now, assume all regions are healthy
        return region in self.regions

    def get_failover_region(self, failed_region: str) -> str:
        """
        Get failover region when primary region fails.

        Args:
            failed_region: Region that failed

        Returns:
            Failover region identifier
        """
        if not Config.AUTO_FAILOVER_ENABLED:
            return self.primary_region

        # Get list of healthy regions excluding failed region
        healthy_regions = [r for r in self.regions if r != failed_region and self.check_regional_health(r)]
        
        if not healthy_regions:
            # All regions failed, return primary as last resort
            return self.primary_region

        # If primary failed, use first secondary
        if failed_region == self.primary_region:
            return healthy_regions[0]

        # Otherwise return primary
        return self.primary_region

    def enforce_data_residency(self, region: str, country_code: Optional[str] = None) -> bool:
        """
        Check if data residency requirements are met for a region.

        Args:
            region: Target region
            country_code: Country code for compliance check

        Returns:
            True if compliant, False otherwise
        """
        if not Config.DATA_RESIDENCY_ENFORCEMENT:
            return True

        # EU data residency
        if Config.EU_DATA_RESIDENCY and country_code in ["GB", "FR", "DE", "ES", "IT"]:
            return region == "eu-west-1"

        # APAC data residency
        if Config.APAC_DATA_RESIDENCY and country_code in ["JP", "CN", "SG", "AU"]:
            return region == "ap-southeast-1"

        return True
