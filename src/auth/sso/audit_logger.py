"""SSO audit logging service."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.database.sso_models import SSOAuditLog, SSOProvider
from src.database.models import User, Tenant

logger = logging.getLogger(__name__)


class SSOAuditLogger:
    """Audit logging for SSO authentication events."""

    def __init__(self, db: Session):
        """Initialize audit logger.

        Args:
            db: Database session
        """
        self.db = db

    def log_event(
        self,
        tenant_id: int,
        event_type: str,
        event_status: str,
        event_message: str,
        user_id: Optional[int] = None,
        provider_id: Optional[int] = None,
        username_attempted: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_id: Optional[str] = None,
        idp_response_data: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        error_details: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SSOAuditLog:
        """Log an SSO event.

        Args:
            tenant_id: Tenant ID
            event_type: Type of event (login, logout, refresh, mfa_challenge, etc.)
            event_status: Status (success, failure, error)
            event_message: Human-readable message
            user_id: User ID if available
            provider_id: SSO provider ID
            username_attempted: Username/email attempted
            ip_address: Client IP address
            user_agent: Client user agent
            device_id: Device identifier
            idp_response_data: Sanitized IdP response data
            error_code: Error code if applicable
            error_details: Error details if applicable
            metadata: Additional metadata

        Returns:
            Created SSOAuditLog object
        """
        audit_log = SSOAuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            provider_id=provider_id,
            event_type=event_type,
            event_status=event_status,
            event_message=event_message,
            username_attempted=username_attempted,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            idp_response_data=idp_response_data,
            error_code=error_code,
            error_details=error_details,
            metadata=metadata,
        )

        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)

        logger.info(
            f"Logged SSO event: {event_type} - {event_status} for tenant {tenant_id}"
        )
        return audit_log

    def log_login_success(
        self,
        tenant_id: int,
        user: User,
        provider: SSOProvider,
        ip_address: str,
        user_agent: str,
        device_id: Optional[str] = None,
        mfa_used: bool = False,
    ) -> SSOAuditLog:
        """Log successful login event.

        Args:
            tenant_id: Tenant ID
            user: Authenticated user
            provider: SSO provider used
            ip_address: Client IP address
            user_agent: Client user agent
            device_id: Device identifier
            mfa_used: Whether MFA was used

        Returns:
            Created audit log
        """
        metadata = {"mfa_used": mfa_used, "provider_type": provider.provider_type}

        return self.log_event(
            tenant_id=tenant_id,
            event_type="login",
            event_status="success",
            event_message=f"User {user.email} successfully logged in via {provider.provider_name}",
            user_id=user.id,
            provider_id=provider.id,
            username_attempted=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            metadata=metadata,
        )

    def log_login_failure(
        self,
        tenant_id: int,
        username_attempted: str,
        provider: SSOProvider,
        ip_address: str,
        user_agent: str,
        reason: str,
        error_code: Optional[str] = None,
    ) -> SSOAuditLog:
        """Log failed login attempt.

        Args:
            tenant_id: Tenant ID
            username_attempted: Username that was attempted
            provider: SSO provider used
            ip_address: Client IP address
            user_agent: Client user agent
            reason: Failure reason
            error_code: Optional error code

        Returns:
            Created audit log
        """
        return self.log_event(
            tenant_id=tenant_id,
            event_type="login",
            event_status="failure",
            event_message=f"Login failed for {username_attempted}: {reason}",
            provider_id=provider.id,
            username_attempted=username_attempted,
            ip_address=ip_address,
            user_agent=user_agent,
            error_code=error_code,
            error_details=reason,
        )

    def log_logout(
        self,
        tenant_id: int,
        user: User,
        provider: SSOProvider,
        ip_address: str,
        user_agent: str,
    ) -> SSOAuditLog:
        """Log logout event.

        Args:
            tenant_id: Tenant ID
            user: User logging out
            provider: SSO provider used
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created audit log
        """
        return self.log_event(
            tenant_id=tenant_id,
            event_type="logout",
            event_status="success",
            event_message=f"User {user.email} logged out",
            user_id=user.id,
            provider_id=provider.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def log_mfa_challenge(
        self,
        tenant_id: int,
        user: User,
        mfa_method: str,
        ip_address: str,
        user_agent: str,
    ) -> SSOAuditLog:
        """Log MFA challenge event.

        Args:
            tenant_id: Tenant ID
            user: User being challenged
            mfa_method: MFA method (totp, sms, email, etc.)
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created audit log
        """
        return self.log_event(
            tenant_id=tenant_id,
            event_type="mfa_challenge",
            event_status="success",
            event_message=f"MFA challenge sent to {user.email} via {mfa_method}",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"mfa_method": mfa_method},
        )

    def log_mfa_success(
        self,
        tenant_id: int,
        user: User,
        mfa_method: str,
        ip_address: str,
        user_agent: str,
    ) -> SSOAuditLog:
        """Log successful MFA verification.

        Args:
            tenant_id: Tenant ID
            user: User who passed MFA
            mfa_method: MFA method used
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created audit log
        """
        return self.log_event(
            tenant_id=tenant_id,
            event_type="mfa_success",
            event_status="success",
            event_message=f"MFA verification successful for {user.email}",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"mfa_method": mfa_method},
        )

    def log_mfa_failure(
        self,
        tenant_id: int,
        user: User,
        mfa_method: str,
        ip_address: str,
        user_agent: str,
        reason: str,
    ) -> SSOAuditLog:
        """Log failed MFA verification.

        Args:
            tenant_id: Tenant ID
            user: User who failed MFA
            mfa_method: MFA method attempted
            ip_address: Client IP address
            user_agent: Client user agent
            reason: Failure reason

        Returns:
            Created audit log
        """
        return self.log_event(
            tenant_id=tenant_id,
            event_type="mfa_failure",
            event_status="failure",
            event_message=f"MFA verification failed for {user.email}: {reason}",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            error_details=reason,
            metadata={"mfa_method": mfa_method},
        )

    def log_session_terminated(
        self,
        tenant_id: int,
        user: User,
        session_id: int,
        reason: str,
    ) -> SSOAuditLog:
        """Log session termination.

        Args:
            tenant_id: Tenant ID
            user: User whose session was terminated
            session_id: Session ID
            reason: Termination reason

        Returns:
            Created audit log
        """
        return self.log_event(
            tenant_id=tenant_id,
            event_type="session_terminated",
            event_status="success",
            event_message=f"Session {session_id} terminated for {user.email}: {reason}",
            user_id=user.id,
            metadata={"session_id": session_id, "reason": reason},
        )

    def get_user_audit_logs(
        self,
        user: User,
        limit: int = 100,
        event_type: Optional[str] = None,
    ) -> List[SSOAuditLog]:
        """Get audit logs for a user.

        Args:
            user: User to get logs for
            limit: Maximum number of logs to return
            event_type: Optional filter by event type

        Returns:
            List of audit logs
        """
        query = self.db.query(SSOAuditLog).filter(SSOAuditLog.user_id == user.id)

        if event_type:
            query = query.filter(SSOAuditLog.event_type == event_type)

        return query.order_by(SSOAuditLog.created_at.desc()).limit(limit).all()

    def get_tenant_audit_logs(
        self,
        tenant_id: int,
        limit: int = 100,
        event_type: Optional[str] = None,
        event_status: Optional[str] = None,
    ) -> List[SSOAuditLog]:
        """Get audit logs for a tenant.

        Args:
            tenant_id: Tenant ID
            limit: Maximum number of logs to return
            event_type: Optional filter by event type
            event_status: Optional filter by event status

        Returns:
            List of audit logs
        """
        query = self.db.query(SSOAuditLog).filter(SSOAuditLog.tenant_id == tenant_id)

        if event_type:
            query = query.filter(SSOAuditLog.event_type == event_type)

        if event_status:
            query = query.filter(SSOAuditLog.event_status == event_status)

        return query.order_by(SSOAuditLog.created_at.desc()).limit(limit).all()
