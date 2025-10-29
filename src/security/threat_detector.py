"""Automated threat detection and blocking."""

import logging
import re
import time
from collections import defaultdict
from typing import Dict, List, Optional, Set

from config.settings import Config

logger = logging.getLogger(__name__)


class ThreatDetector:
    """
    Automated threat detection and blocking system.
    
    Detects:
    - SQL injection attempts
    - XSS attempts
    - Path traversal attempts
    - Suspicious user agents
    - Brute force attacks
    - Abnormal request patterns
    """

    def __init__(self, redis_client=None, ip_manager=None):
        """Initialize threat detector."""
        self.redis_client = redis_client
        self.ip_manager = ip_manager
        self.use_redis = redis_client is not None and Config.REDIS_ENABLED
        
        # In-memory tracking
        self.failed_attempts: Dict[str, List[float]] = defaultdict(list)
        self.suspicious_patterns: Dict[str, int] = defaultdict(int)
        
        # Threat patterns
        self._init_threat_patterns()
        
        logger.info(
            f"Threat detector initialized with {'Redis' if self.use_redis else 'in-memory'} backend"
        )

    def _init_threat_patterns(self):
        """Initialize threat detection patterns."""
        # SQL injection patterns
        self.sql_injection_patterns = [
            r"(\bunion\b.*\bselect\b)",
            r"(\bor\b.*=.*)",
            r"(--|\#|\/\*)",
            r"(\bexec\b|\bexecute\b)",
            r"(\bdrop\b.*\btable\b)",
            r"(\binsert\b.*\binto\b)",
            r"(\bupdate\b.*\bset\b)",
            r"(\bdelete\b.*\bfrom\b)",
            r"(\bselect\b.*\bfrom\b)",
            r"(\bscript\b.*\balert\b)",
            r"(\bor\b.*\b1\s*=\s*1)",
            r"(\'\s*or\s*\'.*=)",
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"onerror\s*=",
            r"onload\s*=",
            r"onclick\s*=",
            r"<iframe[^>]*>",
            r"<embed[^>]*>",
            r"<object[^>]*>",
        ]
        
        # Path traversal patterns
        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"/etc/passwd",
            r"/etc/shadow",
            r"c:\\windows",
            r"c:/windows",
        ]
        
        # Suspicious user agents
        self.suspicious_user_agents = [
            "sqlmap",
            "nikto",
            "nmap",
            "masscan",
            "nessus",
            "burp",
            "acunetix",
            "w3af",
            "metasploit",
            "havij",
        ]
        
        # Compile regex patterns for performance
        self.sql_regex = [re.compile(p, re.IGNORECASE) for p in self.sql_injection_patterns]
        self.xss_regex = [re.compile(p, re.IGNORECASE) for p in self.xss_patterns]
        self.path_regex = [re.compile(p, re.IGNORECASE) for p in self.path_traversal_patterns]

    def _check_patterns(self, text: str, patterns: List[re.Pattern]) -> Optional[str]:
        """Check if text matches any threat pattern."""
        for pattern in patterns:
            if pattern.search(text):
                return pattern.pattern
        return None

    def detect_sql_injection(self, text: str) -> Optional[str]:
        """Detect SQL injection attempt."""
        return self._check_patterns(text, self.sql_regex)

    def detect_xss(self, text: str) -> Optional[str]:
        """Detect XSS attempt."""
        return self._check_patterns(text, self.xss_regex)

    def detect_path_traversal(self, text: str) -> Optional[str]:
        """Detect path traversal attempt."""
        return self._check_patterns(text, self.path_regex)

    def detect_suspicious_user_agent(self, user_agent: str) -> bool:
        """Detect suspicious user agent."""
        if not user_agent:
            return True  # No user agent is suspicious
        
        user_agent_lower = user_agent.lower()
        return any(sus in user_agent_lower for sus in self.suspicious_user_agents)

    def check_request(
        self,
        ip: str,
        method: str,
        path: str,
        query_params: Dict[str, str],
        headers: Dict[str, str],
        body: Optional[str] = None,
    ) -> tuple[bool, List[str]]:
        """
        Check request for threats.
        
        Args:
            ip: Client IP address
            method: HTTP method
            path: Request path
            query_params: Query parameters
            headers: Request headers
            body: Request body
        
        Returns:
            Tuple of (is_safe, threat_reasons)
        """
        threats = []
        
        # Check path
        if self.detect_path_traversal(path):
            threats.append("Path traversal attempt detected in path")
        
        # Check query parameters
        for key, value in query_params.items():
            if sql_pattern := self.detect_sql_injection(f"{key}={value}"):
                threats.append(f"SQL injection attempt detected in query: {sql_pattern}")
            if xss_pattern := self.detect_xss(f"{key}={value}"):
                threats.append(f"XSS attempt detected in query: {xss_pattern}")
            if self.detect_path_traversal(value):
                threats.append("Path traversal attempt detected in query parameters")
        
        # Check user agent
        user_agent = headers.get("User-Agent", "")
        if self.detect_suspicious_user_agent(user_agent):
            threats.append(f"Suspicious user agent detected: {user_agent[:50]}")
        
        # Check body
        if body:
            if sql_pattern := self.detect_sql_injection(body):
                threats.append(f"SQL injection attempt detected in body: {sql_pattern}")
            if xss_pattern := self.detect_xss(body):
                threats.append(f"XSS attempt detected in body: {xss_pattern}")
        
        # Check for excessive header size (potential DoS)
        total_header_size = sum(len(k) + len(v) for k, v in headers.items())
        if total_header_size > Config.MAX_HEADER_SIZE:
            threats.append(f"Excessive header size: {total_header_size} bytes")
        
        # Log threats
        if threats:
            logger.warning(
                f"Threats detected from {ip} on {method} {path}: {', '.join(threats)}"
            )
            self._record_threat(ip, threats)
        
        return len(threats) == 0, threats

    def _record_threat(self, ip: str, threats: List[str]):
        """Record threat for future analysis and auto-blocking."""
        now = time.time()
        
        if self.use_redis:
            # Increment threat counter
            threat_key = f"threat:{ip}"
            count = self.redis_client.incr(threat_key)
            self.redis_client.expire(threat_key, 3600)  # 1 hour window
            
            # Store threat details
            self.redis_client.lpush(f"threat:details:{ip}", f"{now}|{','.join(threats)}")
            self.redis_client.ltrim(f"threat:details:{ip}", 0, 99)  # Keep last 100
            self.redis_client.expire(f"threat:details:{ip}", 86400)  # 24 hours
        else:
            count = self.suspicious_patterns[ip] + 1
            self.suspicious_patterns[ip] = count
        
        # Auto-block after threshold
        if count >= Config.THREAT_AUTO_BLOCK_THRESHOLD:
            logger.warning(
                f"Auto-blocking IP {ip} after {count} threats detected"
            )
            if self.ip_manager:
                self.ip_manager.add_to_blocklist(
                    ip,
                    reason=f"Auto-blocked after {count} threats: {', '.join(threats)}"
                )

    def track_failed_login(self, ip: str, username: str) -> bool:
        """
        Track failed login attempts.
        
        Returns:
            True if should block (brute force detected)
        """
        now = time.time()
        key = f"{ip}:{username}"
        
        if self.use_redis:
            redis_key = f"failed_login:{key}"
            count = self.redis_client.incr(redis_key)
            if count == 1:
                self.redis_client.expire(redis_key, Config.FAILED_LOGIN_WINDOW)
            
            if count >= Config.FAILED_LOGIN_THRESHOLD:
                logger.warning(
                    f"Brute force attack detected from {ip} for user {username} "
                    f"({count} failed attempts)"
                )
                if self.ip_manager:
                    self.ip_manager.add_to_blocklist(
                        ip,
                        reason=f"Brute force attack: {count} failed login attempts for {username}"
                    )
                return True
        else:
            # Clean old attempts
            self.failed_attempts[key] = [
                ts for ts in self.failed_attempts[key]
                if now - ts < Config.FAILED_LOGIN_WINDOW
            ]
            
            self.failed_attempts[key].append(now)
            
            if len(self.failed_attempts[key]) >= Config.FAILED_LOGIN_THRESHOLD:
                logger.warning(
                    f"Brute force attack detected from {ip} for user {username}"
                )
                if self.ip_manager:
                    self.ip_manager.add_to_blocklist(
                        ip,
                        reason=f"Brute force attack: failed login attempts for {username}"
                    )
                return True
        
        return False

    def get_threat_stats(self, ip: str) -> Dict:
        """Get threat statistics for an IP."""
        if self.use_redis:
            threat_key = f"threat:{ip}"
            count = int(self.redis_client.get(threat_key) or 0)
            
            details_key = f"threat:details:{ip}"
            details = self.redis_client.lrange(details_key, 0, 9)  # Last 10
            
            return {
                "threat_count": count,
                "recent_threats": [d.split("|", 1)[1] for d in details] if details else [],
            }
        else:
            return {
                "threat_count": self.suspicious_patterns.get(ip, 0),
                "recent_threats": [],
            }


# Singleton instance
_threat_detector_instance: Optional[ThreatDetector] = None


def get_threat_detector(ip_manager=None) -> ThreatDetector:
    """Get or create threat detector instance."""
    global _threat_detector_instance
    
    if _threat_detector_instance is None:
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
                logger.info("Connected to Redis for threat detection")
            except Exception as e:
                logger.warning(
                    f"Failed to connect to Redis, using in-memory threat detection: {e}"
                )
                redis_client = None
        
        _threat_detector_instance = ThreatDetector(redis_client, ip_manager)
    
    return _threat_detector_instance
