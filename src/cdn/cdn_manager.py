"""CDN management and cache invalidation."""

import hashlib
import logging
import time
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError
from config.settings import Config

logger = logging.getLogger(__name__)


class CDNManager:
    """Manages CDN operations including cache invalidation."""

    def __init__(self):
        self.enabled = Config.CDN_ENABLED
        self.provider = Config.CDN_PROVIDER
        self.distribution_id = Config.CLOUDFRONT_DISTRIBUTION_ID

        if self.provider == "cloudfront" and self.distribution_id:
            self.cloudfront_client = boto3.client("cloudfront")
        else:
            self.cloudfront_client = None

    def invalidate_cache(self, paths: List[str], caller_reference: Optional[str] = None) -> Optional[str]:
        """
        Invalidate CDN cache for specified paths.

        Args:
            paths: List of paths to invalidate (e.g., ['/static/images/*', '/api/config'])
            caller_reference: Optional unique identifier for this invalidation

        Returns:
            Invalidation ID or None if CDN not configured
        """
        if not self.enabled or not self.cloudfront_client:
            return None

        if not paths:
            return None

        # Generate caller reference if not provided
        if caller_reference is None:
            timestamp = str(int(time.time()))
            paths_hash = hashlib.md5(",".join(paths).encode()).hexdigest()[:8]
            caller_reference = f"soundhash-{timestamp}-{paths_hash}"

        try:
            response = self.cloudfront_client.create_invalidation(
                DistributionId=self.distribution_id,
                InvalidationBatch={
                    "Paths": {"Quantity": len(paths), "Items": paths},
                    "CallerReference": caller_reference,
                },
            )
            invalidation_id = response["Invalidation"]["Id"]
            logger.info(f"CloudFront invalidation created: {invalidation_id}")
            return invalidation_id

        except ClientError as e:
            logger.error(f"Failed to create CloudFront invalidation: {e}")
            return None

    def get_invalidation_status(self, invalidation_id: str) -> Optional[str]:
        """
        Get status of a cache invalidation.

        Args:
            invalidation_id: Invalidation ID from invalidate_cache()

        Returns:
            Status string ('InProgress' or 'Completed') or None
        """
        if not self.enabled or not self.cloudfront_client:
            return None

        try:
            response = self.cloudfront_client.get_invalidation(
                DistributionId=self.distribution_id, Id=invalidation_id
            )
            return response["Invalidation"]["Status"]
        except ClientError as e:
            logger.error(f"Failed to get invalidation status: {e}")
            return None

    def purge_all(self) -> Optional[str]:
        """
        Purge entire CDN cache (use with caution).

        Returns:
            Invalidation ID or None
        """
        return self.invalidate_cache(["/*"])

    def purge_static_assets(self) -> Optional[str]:
        """
        Purge all static assets from CDN cache.

        Returns:
            Invalidation ID or None
        """
        return self.invalidate_cache(["/static/*", "/images/*", "/css/*", "/js/*"])

    def purge_api_cache(self, endpoint: Optional[str] = None) -> Optional[str]:
        """
        Purge API endpoint cache.

        Args:
            endpoint: Specific endpoint to purge (e.g., '/api/videos/*')
                     If None, purges all API cache

        Returns:
            Invalidation ID or None
        """
        if endpoint:
            paths = [endpoint]
        else:
            paths = ["/api/*"]

        return self.invalidate_cache(paths)

    def get_distribution_config(self) -> Optional[dict]:
        """
        Get CloudFront distribution configuration.

        Returns:
            Distribution config dict or None
        """
        if not self.enabled or not self.cloudfront_client:
            return None

        try:
            response = self.cloudfront_client.get_distribution_config(DistributionId=self.distribution_id)
            return response["DistributionConfig"]
        except ClientError as e:
            logger.error(f"Failed to get distribution config: {e}")
            return None

    def enable_distribution(self) -> bool:
        """
        Enable CloudFront distribution.

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.cloudfront_client:
            return False

        try:
            # Get current config
            response = self.cloudfront_client.get_distribution_config(DistributionId=self.distribution_id)
            config = response["DistributionConfig"]
            etag = response["ETag"]

            # Update enabled status
            config["Enabled"] = True

            # Update distribution
            self.cloudfront_client.update_distribution(
                DistributionConfig=config, Id=self.distribution_id, IfMatch=etag
            )
            logger.error(f"CloudFront distribution {self.distribution_id} enabled")
            return True

        except ClientError as e:
            logger.error(f"Failed to enable distribution: {e}")
            return False

    def disable_distribution(self) -> bool:
        """
        Disable CloudFront distribution.

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.cloudfront_client:
            return False

        try:
            # Get current config
            response = self.cloudfront_client.get_distribution_config(DistributionId=self.distribution_id)
            config = response["DistributionConfig"]
            etag = response["ETag"]

            # Update enabled status
            config["Enabled"] = False

            # Update distribution
            self.cloudfront_client.update_distribution(
                DistributionConfig=config, Id=self.distribution_id, IfMatch=etag
            )
            logger.error(f"CloudFront distribution {self.distribution_id} disabled")
            return True

        except ClientError as e:
            logger.error(f"Failed to disable distribution: {e}")
            return False

    def get_cache_statistics(self) -> Optional[dict]:
        """
        Get CDN cache statistics.

        Returns:
            Dict with cache stats or None
        """
        if not self.enabled or not self.cloudfront_client:
            return None

        try:
            # Get CloudWatch metrics for the distribution
            cloudwatch = boto3.client("cloudwatch")

            # Query for recent metrics
            end_time = time.time()
            start_time = end_time - 3600  # Last hour

            # Cache hit rate
            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/CloudFront",
                MetricName="CacheHitRate",
                Dimensions=[{"Name": "DistributionId", "Value": self.distribution_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=["Average"],
            )

            cache_hit_rate = None
            if response["Datapoints"]:
                cache_hit_rate = response["Datapoints"][0]["Average"]

            return {"cache_hit_rate": cache_hit_rate, "distribution_id": self.distribution_id}

        except ClientError as e:
            logger.error(f"Failed to get cache statistics: {e}")
            return None
