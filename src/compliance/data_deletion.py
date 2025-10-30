"""User data deletion service for GDPR Article 17 compliance (Right to be Forgotten)."""

import logging
import secrets
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.orm import Session

from src.compliance.audit_logger import AuditLogger
from src.database.connection import db_manager
from src.database.models import (
    APIKey,
    AuditLog,
    DataDeletionRequest,
    DataExportRequest,
    EmailLog,
    EmailPreference,
    User,
    UserConsent,
)

logger = logging.getLogger(__name__)


class DataDeletionService:
    """Service for deleting or anonymizing user data per GDPR Article 17."""

    def create_deletion_request(
        self,
        user_id: int,
        deletion_type: str = "full",
        data_types: Optional[list] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        session: Optional[Session] = None,
    ) -> DataDeletionRequest:
        """
        Create a new data deletion request.
        
        Args:
            user_id: ID of user requesting deletion
            deletion_type: Type of deletion ('full', 'partial', 'anonymize')
            data_types: Specific data types to delete (for partial deletion)
            reason: Optional reason for deletion
            ip_address: IP address of request
            session: Database session
            
        Returns:
            DataDeletionRequest object
        """
        should_close_session = False
        if session is None:
            session = db_manager.get_session()
            should_close_session = True

        try:
            # Generate verification token
            verification_token = secrets.token_urlsafe(32)

            # Create deletion request
            deletion_request = DataDeletionRequest(
                user_id=user_id,
                deletion_type=deletion_type,
                data_types=data_types,
                reason=reason,
                status="pending",
                requested_at=datetime.utcnow(),
                verification_token=verification_token,
                ip_address=ip_address,
            )
            session.add(deletion_request)
            session.commit()

            # Log the request
            AuditLogger.log_action(
                action="data.deletion_requested",
                user_id=user_id,
                resource_type="data_deletion",
                resource_id=str(deletion_request.id),
                ip_address=ip_address,
                status="success",
                metadata={"deletion_type": deletion_type},
                session=session,
            )

            logger.info(f"Data deletion request created: {deletion_request.id} for user {user_id}")
            return deletion_request
        except Exception as e:
            logger.error(f"Failed to create deletion request: {e}")
            session.rollback()
            raise
        finally:
            if should_close_session:
                session.close()

    def verify_deletion_request(
        self, request_id: int, verification_token: str, session: Optional[Session] = None
    ) -> bool:
        """
        Verify a deletion request using the verification token.
        
        Args:
            request_id: ID of deletion request
            verification_token: Token sent to user for verification
            session: Database session
            
        Returns:
            True if verified, False otherwise
        """
        should_close_session = False
        if session is None:
            session = db_manager.get_session()
            should_close_session = True

        try:
            deletion_request = session.query(DataDeletionRequest).filter_by(id=request_id).first()
            if (
                deletion_request
                and deletion_request.verification_token == verification_token
                and deletion_request.status == "pending"
            ):
                deletion_request.verified_at = datetime.utcnow()
                deletion_request.status = "processing"
                session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to verify deletion request: {e}")
            return False
        finally:
            if should_close_session:
                session.close()

    def process_deletion_request(
        self, request_id: int, session: Optional[Session] = None
    ) -> bool:
        """
        Process a verified data deletion request.
        
        Args:
            request_id: ID of deletion request
            session: Database session
            
        Returns:
            True if successful, False otherwise
        """
        should_close_session = False
        if session is None:
            session = db_manager.get_session()
            should_close_session = True

        try:
            # Get deletion request
            deletion_request = session.query(DataDeletionRequest).filter_by(id=request_id).first()
            if not deletion_request:
                logger.error(f"Deletion request not found: {request_id}")
                return False

            if deletion_request.status != "processing":
                logger.error(f"Deletion request {request_id} not in processing state")
                return False

            # Update status
            deletion_request.started_at = datetime.utcnow()
            session.commit()

            user_id = deletion_request.user_id
            deletion_summary = {}

            if deletion_request.deletion_type == "full":
                deletion_summary = self._perform_full_deletion(user_id, session)
            elif deletion_request.deletion_type == "anonymize":
                deletion_summary = self._perform_anonymization(user_id, session)
            elif deletion_request.deletion_type == "partial":
                deletion_summary = self._perform_partial_deletion(
                    user_id, deletion_request.data_types or [], session
                )

            # Update deletion request
            deletion_request.status = "completed"
            deletion_request.completed_at = datetime.utcnow()
            deletion_request.items_deleted = deletion_summary.get("deleted", {})
            deletion_request.items_anonymized = deletion_summary.get("anonymized", {})
            session.commit()

            # Log completion
            AuditLogger.log_action(
                action="data.deletion_completed",
                user_id=user_id,
                resource_type="data_deletion",
                resource_id=str(request_id),
                status="success",
                metadata=deletion_summary,
                session=session,
            )

            logger.info(f"Data deletion completed: {request_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to process deletion request {request_id}: {e}")
            if deletion_request:
                deletion_request.status = "failed"
                deletion_request.error_message = str(e)
                session.commit()
            return False
        finally:
            if should_close_session:
                session.close()

    def _perform_full_deletion(self, user_id: int, session: Session) -> Dict:
        """Perform full deletion of user data."""
        deleted = {}

        # Delete API keys
        deleted["api_keys"] = (
            session.query(APIKey).filter_by(user_id=user_id).delete(synchronize_session=False)
        )

        # Delete email preferences
        deleted["email_preferences"] = (
            session.query(EmailPreference)
            .filter_by(user_id=user_id)
            .delete(synchronize_session=False)
        )

        # Delete email logs
        deleted["email_logs"] = (
            session.query(EmailLog).filter_by(user_id=user_id).delete(synchronize_session=False)
        )

        # Delete consent records
        deleted["consents"] = (
            session.query(UserConsent).filter_by(user_id=user_id).delete(synchronize_session=False)
        )

        # Delete data export requests
        deleted["export_requests"] = (
            session.query(DataExportRequest)
            .filter_by(user_id=user_id)
            .delete(synchronize_session=False)
        )

        # Anonymize audit logs instead of deleting (for compliance)
        audit_count = (
            session.query(AuditLog)
            .filter_by(user_id=user_id)
            .update({"user_id": None}, synchronize_session=False)
        )
        deleted["audit_logs_anonymized"] = audit_count

        # Finally, delete the user account
        deleted["user"] = (
            session.query(User).filter_by(id=user_id).delete(synchronize_session=False)
        )

        session.commit()
        return {"deleted": deleted}

    def _perform_anonymization(self, user_id: int, session: Session) -> Dict:
        """Anonymize user data while preserving aggregate statistics."""
        anonymized = {}

        user = session.query(User).filter_by(id=user_id).first()
        if user:
            # Anonymize user data
            user.username = f"deleted_user_{user_id}"
            user.email = f"deleted_{user_id}@anonymized.local"
            user.full_name = "Deleted User"
            user.hashed_password = "DELETED"
            user.is_active = False
            anonymized["user"] = 1

        # Deactivate API keys
        anonymized["api_keys"] = (
            session.query(APIKey)
            .filter_by(user_id=user_id)
            .update({"is_active": False}, synchronize_session=False)
        )

        # Anonymize audit logs
        anonymized["audit_logs"] = (
            session.query(AuditLog)
            .filter_by(user_id=user_id)
            .update({"user_id": None}, synchronize_session=False)
        )

        session.commit()
        return {"anonymized": anonymized}

    def _perform_partial_deletion(
        self, user_id: int, data_types: list, session: Session
    ) -> Dict:
        """Perform partial deletion of specific data types."""
        deleted = {}

        for data_type in data_types:
            if data_type == "api_keys":
                deleted["api_keys"] = (
                    session.query(APIKey)
                    .filter_by(user_id=user_id)
                    .delete(synchronize_session=False)
                )
            elif data_type == "email_logs":
                deleted["email_logs"] = (
                    session.query(EmailLog)
                    .filter_by(user_id=user_id)
                    .delete(synchronize_session=False)
                )
            elif data_type == "consents":
                deleted["consents"] = (
                    session.query(UserConsent)
                    .filter_by(user_id=user_id)
                    .delete(synchronize_session=False)
                )

        session.commit()
        return {"deleted": deleted}
