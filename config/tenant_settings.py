"""Tenant-specific settings that override global defaults."""

from config.settings import Config
from src.database.models import Tenant


class TenantSettings:
    """Tenant-specific settings management."""

    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self._settings = tenant.settings or {}

    def get(self, key: str, default=None):
        """Get tenant setting or fall back to default."""
        return self._settings.get(key, default)

    def set(self, key: str, value):
        """Set tenant setting."""
        self._settings[key] = value
        self.tenant.settings = self._settings
        # Note: Caller should commit the session

    @property
    def max_concurrent_jobs(self) -> int:
        """Get max concurrent jobs setting."""
        return self.get("max_concurrent_jobs", Config.MAX_CONCURRENT_DOWNLOADS)

    @property
    def fingerprint_sample_rate(self) -> int:
        """Get fingerprint sample rate setting."""
        return self.get("fingerprint_sample_rate", Config.FINGERPRINT_SAMPLE_RATE)

    @property
    def enable_webhooks(self) -> bool:
        """Check if webhooks are enabled."""
        return self.get("enable_webhooks", False)

    @property
    def webhook_url(self) -> str | None:
        """Get webhook URL if configured."""
        return self.get("webhook_url")

    @property
    def max_upload_size_mb(self) -> int:
        """Get max upload size in MB."""
        return self.get("max_upload_size_mb", 100)
