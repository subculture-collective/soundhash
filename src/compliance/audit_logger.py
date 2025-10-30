"""Audit logging service for SOC 2 compliance."""

import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from src.database.connection import db_manager
from src.database.models import AuditLog

logger = logging.getLogger(__name__)


class AuditLogger:
    """Service for logging audit trails of all data access and modifications."""

    @staticmethod
    def log_action(
        action: str,
        user_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None,
        session: Optional[Session] = None,
    ) -> Optional[AuditLog]:
        """
        Log an action to the audit trail.
        
        Args:
            action: Action performed (e.g., 'user.login', 'data.export')
            user_id: ID of user performing the action
            tenant_id: ID of tenant (for multi-tenant)
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            ip_address: IP address of request
            user_agent: User agent string
            request_method: HTTP method
            request_path: Request path
            old_values: Previous state of data
            new_values: New state of data
            status: Status of action ('success', 'failure', 'partial')
            error_message: Error message if failed
            metadata: Additional metadata
            session: Database session (will create new if None)
            
        Returns:
            AuditLog entry if successful, None if error
        """
        should_close_session = False
        if session is None:
            session = db_manager.get_session()
            should_close_session = True

        try:
            audit_entry = AuditLog(
                user_id=user_id,
                tenant_id=tenant_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_method=request_method,
                request_path=request_path,
                old_values=old_values,
                new_values=new_values,
                status=status,
                error_message=error_message,
                extra_metadata=metadata,
                created_at=datetime.utcnow(),
            )
            session.add(audit_entry)
            session.commit()
            session.refresh(audit_entry)
            logger.debug(f"Audit log created: {action} by user {user_id}")
            return audit_entry
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            session.rollback()
            return None
        finally:
            if should_close_session:
                session.close()

    @staticmethod
    def log_data_access(
        user_id: int,
        resource_type: str,
        resource_id: str,
        ip_address: Optional[str] = None,
        metadata: Optional[dict] = None,
        session: Optional[Session] = None,
    ) -> Optional[AuditLog]:
        """Log data access event."""
        return AuditLogger.log_action(
            action=f"{resource_type}.read",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            metadata=metadata,
            session=session,
        )

    @staticmethod
    def log_data_modification(
        user_id: int,
        resource_type: str,
        resource_id: str,
        old_values: dict,
        new_values: dict,
        ip_address: Optional[str] = None,
        metadata: Optional[dict] = None,
        session: Optional[Session] = None,
    ) -> Optional[AuditLog]:
        """Log data modification event."""
        return AuditLogger.log_action(
            action=f"{resource_type}.update",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            metadata=metadata,
            session=session,
        )

    @staticmethod
    def log_data_deletion(
        user_id: int,
        resource_type: str,
        resource_id: str,
        old_values: dict,
        ip_address: Optional[str] = None,
        metadata: Optional[dict] = None,
        session: Optional[Session] = None,
    ) -> Optional[AuditLog]:
        """Log data deletion event."""
        return AuditLogger.log_action(
            action=f"{resource_type}.delete",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            ip_address=ip_address,
            metadata=metadata,
            session=session,
        )
