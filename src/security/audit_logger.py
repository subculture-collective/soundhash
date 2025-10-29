"""Security audit logging for compliance and monitoring."""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from config.settings import Config

logger = logging.getLogger(__name__)


class SecurityEventType(Enum):
    """Security event types for audit logging."""

    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    
    # API key events
    API_KEY_CREATED = "api_key_created"
    API_KEY_ROTATED = "api_key_rotated"
    API_KEY_REVOKED = "api_key_revoked"
    API_KEY_EXPIRED = "api_key_expired"
    
    # Access control events
    ACCESS_DENIED = "access_denied"
    PERMISSION_DENIED = "permission_denied"
    IP_BLOCKED = "ip_blocked"
    IP_UNBLOCKED = "ip_unblocked"
    
    # Rate limiting events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    RATE_LIMIT_RESET = "rate_limit_reset"
    
    # Threat detection events
    THREAT_DETECTED = "threat_detected"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    PATH_TRAVERSAL_ATTEMPT = "path_traversal_attempt"
    BRUTE_FORCE_DETECTED = "brute_force_detected"
    SUSPICIOUS_USER_AGENT = "suspicious_user_agent"
    
    # Data access events
    DATA_ACCESS = "data_access"
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"
    
    # Configuration changes
    CONFIG_CHANGE = "config_change"
    SECURITY_SETTING_CHANGE = "security_setting_change"


class SecurityAuditLogger:
    """Logger for security audit events."""

    def __init__(self):
        """Initialize security audit logger."""
        self.enabled = Config.SECURITY_AUDIT_ENABLED
        
        if self.enabled:
            # Set up file handler for security logs
            self.security_logger = logging.getLogger("security_audit")
            self.security_logger.setLevel(logging.INFO)
            
            # Create file handler
            try:
                import os
                os.makedirs(os.path.dirname(Config.SECURITY_LOG_FILE), exist_ok=True)
                
                file_handler = logging.FileHandler(Config.SECURITY_LOG_FILE)
                file_handler.setLevel(logging.INFO)
                
                # JSON format for easy parsing
                formatter = logging.Formatter(
                    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                    '"logger": "%(name)s", "message": %(message)s}'
                )
                file_handler.setFormatter(formatter)
                
                self.security_logger.addHandler(file_handler)
                
                logger.info(f"Security audit logging enabled: {Config.SECURITY_LOG_FILE}")
            except Exception as e:
                logger.error(f"Failed to set up security audit logging: {e}")
                self.enabled = False

    def log_event(
        self,
        event_type: SecurityEventType,
        ip_address: Optional[str] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "INFO",
    ) -> None:
        """
        Log a security audit event.
        
        Args:
            event_type: Type of security event
            ip_address: Client IP address
            user_id: User ID if authenticated
            username: Username if authenticated
            details: Additional event details
            severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
        """
        if not self.enabled:
            return
        
        event = {
            "event_type": event_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": ip_address,
            "user_id": user_id,
            "username": username,
            "details": details or {},
            "compliance_mode": Config.COMPLIANCE_MODE,
        }
        
        # Log as JSON string
        event_json = json.dumps(event)
        
        if severity == "CRITICAL":
            self.security_logger.critical(event_json)
        elif severity == "ERROR":
            self.security_logger.error(event_json)
        elif severity == "WARNING":
            self.security_logger.warning(event_json)
        else:
            self.security_logger.info(event_json)

    def log_login_success(
        self, ip_address: str, user_id: int, username: str, method: str = "password"
    ) -> None:
        """Log successful login."""
        self.log_event(
            SecurityEventType.LOGIN_SUCCESS,
            ip_address=ip_address,
            user_id=user_id,
            username=username,
            details={"method": method},
            severity="INFO",
        )

    def log_login_failure(
        self, ip_address: str, username: str, reason: str = "invalid_credentials"
    ) -> None:
        """Log failed login attempt."""
        self.log_event(
            SecurityEventType.LOGIN_FAILURE,
            ip_address=ip_address,
            username=username,
            details={"reason": reason},
            severity="WARNING",
        )

    def log_threat(
        self, ip_address: str, threat_type: str, details: Dict[str, Any]
    ) -> None:
        """Log detected threat."""
        event_type = SecurityEventType.THREAT_DETECTED
        
        # Map to specific event types
        if "sql" in threat_type.lower():
            event_type = SecurityEventType.SQL_INJECTION_ATTEMPT
        elif "xss" in threat_type.lower():
            event_type = SecurityEventType.XSS_ATTEMPT
        elif "path" in threat_type.lower():
            event_type = SecurityEventType.PATH_TRAVERSAL_ATTEMPT
        elif "brute" in threat_type.lower():
            event_type = SecurityEventType.BRUTE_FORCE_DETECTED
        
        self.log_event(
            event_type,
            ip_address=ip_address,
            details={**details, "threat_type": threat_type},
            severity="CRITICAL",
        )

    def log_rate_limit_exceeded(
        self, ip_address: str, endpoint: str, user_id: Optional[int] = None
    ) -> None:
        """Log rate limit exceeded."""
        self.log_event(
            SecurityEventType.RATE_LIMIT_EXCEEDED,
            ip_address=ip_address,
            user_id=user_id,
            details={"endpoint": endpoint},
            severity="WARNING",
        )

    def log_ip_blocked(self, ip_address: str, reason: str) -> None:
        """Log IP address blocked."""
        self.log_event(
            SecurityEventType.IP_BLOCKED,
            ip_address=ip_address,
            details={"reason": reason},
            severity="WARNING",
        )

    def log_api_key_event(
        self,
        event_type: SecurityEventType,
        user_id: int,
        username: str,
        key_id: int,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log API key lifecycle event."""
        self.log_event(
            event_type,
            user_id=user_id,
            username=username,
            details={**(details or {}), "key_id": key_id},
            severity="INFO",
        )

    def log_data_access(
        self,
        ip_address: str,
        user_id: int,
        username: str,
        resource_type: str,
        resource_id: str,
        action: str,
    ) -> None:
        """Log data access for compliance."""
        self.log_event(
            SecurityEventType.DATA_ACCESS,
            ip_address=ip_address,
            user_id=user_id,
            username=username,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action,
            },
            severity="INFO",
        )


# Singleton instance
_audit_logger_instance: Optional[SecurityAuditLogger] = None


def get_audit_logger() -> SecurityAuditLogger:
    """Get or create security audit logger instance."""
    global _audit_logger_instance
    
    if _audit_logger_instance is None:
        _audit_logger_instance = SecurityAuditLogger()
    
    return _audit_logger_instance
