"""IP allowlist/blocklist management for security."""

import ipaddress
import logging
from typing import Optional, Set

from config.settings import Config

logger = logging.getLogger(__name__)


class IPManager:
    """Manage IP allowlists and blocklists for security."""

    def __init__(self, redis_client=None):
        """Initialize IP manager."""
        self.redis_client = redis_client
        self.use_redis = redis_client is not None and Config.REDIS_ENABLED
        
        # In-memory storage
        self.allowlist: Set[str] = set()
        self.blocklist: Set[str] = set()
        self.network_allowlist: Set[ipaddress.IPv4Network | ipaddress.IPv6Network] = set()
        self.network_blocklist: Set[ipaddress.IPv4Network | ipaddress.IPv6Network] = set()
        
        # Load initial lists from config
        self._load_from_config()
        
        logger.info(
            f"IP manager initialized with {'Redis' if self.use_redis else 'in-memory'} backend"
        )

    def _load_from_config(self):
        """Load IP lists from configuration."""
        # Load allowlist
        if Config.IP_ALLOWLIST:
            for ip in Config.IP_ALLOWLIST:
                self.add_to_allowlist(ip)
        
        # Load blocklist
        if Config.IP_BLOCKLIST:
            for ip in Config.IP_BLOCKLIST:
                self.add_to_blocklist(ip)

    def _normalize_ip(self, ip: str) -> str:
        """Normalize IP address."""
        try:
            # Try to parse as IPv4/IPv6 address
            addr = ipaddress.ip_address(ip)
            return str(addr)
        except ValueError:
            # Return as-is if not a valid IP
            return ip

    def add_to_allowlist(self, ip: str) -> bool:
        """Add IP or network to allowlist."""
        try:
            # Check if it's a network (CIDR notation)
            if "/" in ip:
                network = ipaddress.ip_network(ip, strict=False)
                self.network_allowlist.add(network)
                
                if self.use_redis:
                    self.redis_client.sadd("ip:allowlist:networks", str(network))
                
                logger.info(f"Added network {network} to allowlist")
            else:
                normalized_ip = self._normalize_ip(ip)
                self.allowlist.add(normalized_ip)
                
                if self.use_redis:
                    self.redis_client.sadd("ip:allowlist", normalized_ip)
                
                logger.info(f"Added IP {normalized_ip} to allowlist")
            
            return True
        except Exception as e:
            logger.error(f"Failed to add {ip} to allowlist: {e}")
            return False

    def add_to_blocklist(self, ip: str, reason: Optional[str] = None) -> bool:
        """Add IP or network to blocklist."""
        try:
            # Check if it's a network (CIDR notation)
            if "/" in ip:
                network = ipaddress.ip_network(ip, strict=False)
                self.network_blocklist.add(network)
                
                if self.use_redis:
                    self.redis_client.sadd("ip:blocklist:networks", str(network))
                    if reason:
                        self.redis_client.hset(f"ip:blocklist:reason:{network}", "reason", reason)
                
                logger.warning(f"Added network {network} to blocklist. Reason: {reason}")
            else:
                normalized_ip = self._normalize_ip(ip)
                self.blocklist.add(normalized_ip)
                
                if self.use_redis:
                    self.redis_client.sadd("ip:blocklist", normalized_ip)
                    if reason:
                        self.redis_client.hset(f"ip:blocklist:reason:{normalized_ip}", "reason", reason)
                
                logger.warning(f"Added IP {normalized_ip} to blocklist. Reason: {reason}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to add {ip} to blocklist: {e}")
            return False

    def remove_from_allowlist(self, ip: str) -> bool:
        """Remove IP or network from allowlist."""
        try:
            if "/" in ip:
                network = ipaddress.ip_network(ip, strict=False)
                self.network_allowlist.discard(network)
                
                if self.use_redis:
                    self.redis_client.srem("ip:allowlist:networks", str(network))
            else:
                normalized_ip = self._normalize_ip(ip)
                self.allowlist.discard(normalized_ip)
                
                if self.use_redis:
                    self.redis_client.srem("ip:allowlist", normalized_ip)
            
            logger.info(f"Removed {ip} from allowlist")
            return True
        except Exception as e:
            logger.error(f"Failed to remove {ip} from allowlist: {e}")
            return False

    def remove_from_blocklist(self, ip: str) -> bool:
        """Remove IP or network from blocklist."""
        try:
            if "/" in ip:
                network = ipaddress.ip_network(ip, strict=False)
                self.network_blocklist.discard(network)
                
                if self.use_redis:
                    self.redis_client.srem("ip:blocklist:networks", str(network))
                    self.redis_client.delete(f"ip:blocklist:reason:{network}")
            else:
                normalized_ip = self._normalize_ip(ip)
                self.blocklist.discard(normalized_ip)
                
                if self.use_redis:
                    self.redis_client.srem("ip:blocklist", normalized_ip)
                    self.redis_client.delete(f"ip:blocklist:reason:{normalized_ip}")
            
            logger.info(f"Removed {ip} from blocklist")
            return True
        except Exception as e:
            logger.error(f"Failed to remove {ip} from blocklist: {e}")
            return False

    def is_blocked(self, ip: str) -> tuple[bool, Optional[str]]:
        """
        Check if IP is blocked.
        
        Returns:
            Tuple of (is_blocked, reason)
        """
        try:
            normalized_ip = self._normalize_ip(ip)
            addr = ipaddress.ip_address(normalized_ip)
            
            # Check direct IP blocklist
            if normalized_ip in self.blocklist:
                reason = None
                if self.use_redis:
                    reason = self.redis_client.hget(f"ip:blocklist:reason:{normalized_ip}", "reason")
                return True, reason
            
            # Check network blocklist
            for network in self.network_blocklist:
                if addr in network:
                    reason = None
                    if self.use_redis:
                        reason = self.redis_client.hget(f"ip:blocklist:reason:{network}", "reason")
                    return True, reason
            
            return False, None
        except Exception as e:
            logger.error(f"Failed to check if {ip} is blocked: {e}")
            # Fail open - don't block on error
            return False, None

    def is_allowed(self, ip: str) -> bool:
        """
        Check if IP is in allowlist.
        
        If allowlist is empty, all IPs are implicitly allowed (unless blocked).
        If allowlist has entries, only those IPs/networks are allowed.
        """
        try:
            # Empty allowlist means all IPs are allowed (unless blocked)
            if not self.allowlist and not self.network_allowlist:
                return True
            
            normalized_ip = self._normalize_ip(ip)
            addr = ipaddress.ip_address(normalized_ip)
            
            # Check direct IP allowlist
            if normalized_ip in self.allowlist:
                return True
            
            # Check network allowlist
            for network in self.network_allowlist:
                if addr in network:
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to check if {ip} is allowed: {e}")
            # Fail open - allow on error
            return True

    def check_ip(self, ip: str) -> tuple[bool, Optional[str]]:
        """
        Check if IP should be allowed through.
        
        Returns:
            Tuple of (allowed, reason_if_blocked)
        """
        # First check if blocked
        is_blocked, block_reason = self.is_blocked(ip)
        if is_blocked:
            return False, block_reason or "IP is blocked"
        
        # Then check if allowed (if allowlist is configured)
        if not self.is_allowed(ip):
            return False, "IP not in allowlist"
        
        return True, None

    def get_allowlist(self) -> Set[str]:
        """Get all IPs and networks in allowlist."""
        result = set(self.allowlist)
        result.update(str(net) for net in self.network_allowlist)
        return result

    def get_blocklist(self) -> Set[str]:
        """Get all IPs and networks in blocklist."""
        result = set(self.blocklist)
        result.update(str(net) for net in self.network_blocklist)
        return result


# Singleton instance
_ip_manager_instance: Optional[IPManager] = None


def get_ip_manager() -> IPManager:
    """Get or create IP manager instance."""
    global _ip_manager_instance
    
    if _ip_manager_instance is None:
        redis_client = None
        
        if Config.REDIS_ENABLED:
            try:
                import redis
                redis_client = redis.Redis(
                    host=Config.REDIS_HOST,
                    port=Config.REDIS_PORT,
                    db=Config.REDIS_DB,
                    password=Config.REDIS_PASSWORD,
                    decode_responses=True,
                )
                # Test connection
                redis_client.ping()
                logger.info("Connected to Redis for IP management")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis, using in-memory IP management: {e}")
                redis_client = None
        
        _ip_manager_instance = IPManager(redis_client)
    
    return _ip_manager_instance
