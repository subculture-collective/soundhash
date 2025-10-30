"""Data retention policy enforcement service."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.compliance.audit_logger import AuditLogger
from src.database.connection import db_manager
from src.database.models import (
    AuditLog,
    DataRetentionPolicy,
    EmailLog,
    ProcessingJob,
)

logger = logging.getLogger(__name__)


class DataRetentionService:
    """Service for enforcing data retention policies."""

    @staticmethod
    def create_policy(
        policy_name: str,
        data_type: str,
        retention_days: int,
        action: str = "delete",
        description: Optional[str] = None,
        legal_basis: Optional[str] = None,
        tenant_id: Optional[int] = None,
        session: Optional[Session] = None,
    ) -> DataRetentionPolicy:
        """
        Create a new data retention policy.
        
        Args:
            policy_name: Name of the policy
            data_type: Type of data this policy applies to
            retention_days: Number of days to retain data
            action: Action after retention period ('delete', 'archive', 'anonymize')
            description: Policy description
            legal_basis: Legal justification for retention period
            tenant_id: Tenant ID (for multi-tenant)
            session: Database session
            
        Returns:
            DataRetentionPolicy object
        """
        should_close_session = False
        if session is None:
            session = db_manager.get_session()
            should_close_session = True

        try:
            policy = DataRetentionPolicy(
                tenant_id=tenant_id,
                policy_name=policy_name,
                data_type=data_type,
                retention_days=retention_days,
                action=action,
                description=description,
                legal_basis=legal_basis,
                is_active=True,
            )
            session.add(policy)
            session.commit()

            logger.info(f"Data retention policy created: {policy_name} for {data_type}")
            return policy
        except Exception as e:
            logger.error(f"Failed to create retention policy: {e}")
            session.rollback()
            raise
        finally:
            if should_close_session:
                session.close()

    @staticmethod
    def apply_policies(
        tenant_id: Optional[int] = None, session: Optional[Session] = None
    ) -> Dict[str, int]:
        """
        Apply all active retention policies.
        
        Args:
            tenant_id: Optional tenant ID to filter policies
            session: Database session
            
        Returns:
            Dictionary with counts of items processed per data type
        """
        should_close_session = False
        if session is None:
            session = db_manager.get_session()
            should_close_session = True

        try:
            # Get active policies
            query = session.query(DataRetentionPolicy).filter_by(is_active=True)
            if tenant_id:
                query = query.filter_by(tenant_id=tenant_id)
            policies = query.all()

            results = {}
            for policy in policies:
                try:
                    count = DataRetentionService._apply_single_policy(policy, session)
                    results[policy.data_type] = count

                    # Update last applied timestamp
                    policy.last_applied_at = datetime.utcnow()
                    session.commit()
                except Exception as e:
                    logger.error(f"Failed to apply policy {policy.policy_name}: {e}")
                    session.rollback()

            return results
        finally:
            if should_close_session:
                session.close()

    @staticmethod
    def _apply_single_policy(policy: DataRetentionPolicy, session: Session) -> int:
        """Apply a single retention policy."""
        cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_days)
        count = 0

        if policy.data_type == "audit_logs":
            # Delete old audit logs
            if policy.action == "delete":
                count = (
                    session.query(AuditLog)
                    .filter(AuditLog.created_at < cutoff_date)
                    .delete(synchronize_session=False)
                )
        elif policy.data_type == "email_logs":
            # Delete old email logs
            if policy.action == "delete":
                count = (
                    session.query(EmailLog)
                    .filter(EmailLog.created_at < cutoff_date)
                    .delete(synchronize_session=False)
                )
        elif policy.data_type == "processing_jobs":
            # Delete completed/failed jobs
            if policy.action == "delete":
                count = (
                    session.query(ProcessingJob)
                    .filter(
                        and_(
                            ProcessingJob.completed_at < cutoff_date,
                            ProcessingJob.status.in_(["completed", "failed"]),
                        )
                    )
                    .delete(synchronize_session=False)
                )

        session.commit()

        # Log the retention policy execution
        if count > 0:
            AuditLogger.log_action(
                action="retention.policy_applied",
                resource_type="retention_policy",
                resource_id=str(policy.id),
                status="success",
                extra_metadata={
                    "policy_name": policy.policy_name,
                    "data_type": policy.data_type,
                    "items_processed": count,
                    "retention_days": policy.retention_days,
                    "action": policy.action,
                },
                session=session,
            )
            logger.info(
                f"Retention policy applied: {policy.policy_name}, "
                f"{count} items {policy.action}d"
            )

        return count

    @staticmethod
    def get_policy(
        policy_id: int, session: Optional[Session] = None
    ) -> Optional[DataRetentionPolicy]:
        """Get a specific retention policy."""
        should_close_session = False
        if session is None:
            session = db_manager.get_session()
            should_close_session = True

        try:
            return session.query(DataRetentionPolicy).filter_by(id=policy_id).first()
        finally:
            if should_close_session:
                session.close()

    @staticmethod
    def list_policies(
        tenant_id: Optional[int] = None, session: Optional[Session] = None
    ) -> list:
        """List all retention policies."""
        should_close_session = False
        if session is None:
            session = db_manager.get_session()
            should_close_session = True

        try:
            query = session.query(DataRetentionPolicy)
            if tenant_id:
                query = query.filter_by(tenant_id=tenant_id)
            return query.all()
        finally:
            if should_close_session:
                session.close()

    @staticmethod
    def deactivate_policy(policy_id: int, session: Optional[Session] = None) -> bool:
        """Deactivate a retention policy."""
        should_close_session = False
        if session is None:
            session = db_manager.get_session()
            should_close_session = True

        try:
            policy = session.query(DataRetentionPolicy).filter_by(id=policy_id).first()
            if policy:
                policy.is_active = False
                session.commit()
                logger.info(f"Retention policy deactivated: {policy.policy_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to deactivate retention policy: {e}")
            session.rollback()
            return False
        finally:
            if should_close_session:
                session.close()
