"""User data export service for GDPR Article 15 compliance."""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from config.settings import Config
from src.compliance.audit_logger import AuditLogger
from src.database.connection import db_manager
from src.database.models import (
    APIKey,
    AuditLog,
    DataExportRequest,
    EmailLog,
    EmailPreference,
    User,
    UserConsent,
)

logger = logging.getLogger(__name__)


class DataExportService:
    """Service for exporting user data per GDPR Article 15."""

    def __init__(self):
        self.export_dir = Path(Config.TEMP_DIR) / "data_exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def create_export_request(
        self,
        user_id: int,
        request_type: str = "full_export",
        data_types: Optional[list] = None,
        format: str = "json",
        ip_address: Optional[str] = None,
        session: Optional[Session] = None,
    ) -> DataExportRequest:
        """
        Create a new data export request.
        
        Args:
            user_id: ID of user requesting export
            request_type: Type of export ('full_export' or 'specific_data')
            data_types: List of specific data types to export
            format: Export format ('json', 'csv', 'xml')
            ip_address: IP address of request
            session: Database session
            
        Returns:
            DataExportRequest object
        """
        should_close_session = False
        if session is None:
            session = db_manager.get_session()
            should_close_session = True

        try:
            # Create export request
            export_request = DataExportRequest(
                user_id=user_id,
                request_type=request_type,
                data_types=data_types,
                format=format,
                status="pending",
                requested_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
                ip_address=ip_address,
            )
            session.add(export_request)
            session.commit()

            # Log the request
            AuditLogger.log_action(
                action="data.export_requested",
                user_id=user_id,
                resource_type="data_export",
                resource_id=str(export_request.id),
                ip_address=ip_address,
                status="success",
                session=session,
            )

            logger.info(f"Data export request created: {export_request.id} for user {user_id}")
            return export_request
        except Exception as e:
            logger.error(f"Failed to create export request: {e}")
            session.rollback()
            raise
        finally:
            if should_close_session:
                session.close()

    def process_export_request(
        self, request_id: int, session: Optional[Session] = None
    ) -> Optional[str]:
        """
        Process a data export request and generate the export file.
        
        Args:
            request_id: ID of export request
            session: Database session
            
        Returns:
            Path to generated export file, or None if failed
        """
        should_close_session = False
        if session is None:
            session = db_manager.get_session()
            should_close_session = True

        try:
            # Get export request
            export_request = session.query(DataExportRequest).filter_by(id=request_id).first()
            if not export_request:
                logger.error(f"Export request not found: {request_id}")
                return None

            # Update status
            export_request.status = "processing"
            export_request.started_at = datetime.utcnow()
            session.commit()

            # Collect user data
            user_data = self._collect_user_data(export_request.user_id, session)

            # Generate export file
            file_path = self._generate_export_file(
                export_request.user_id, user_data, export_request.format
            )

            # Update export request
            export_request.status = "completed"
            export_request.completed_at = datetime.utcnow()
            export_request.file_path = str(file_path)
            export_request.file_size_bytes = os.path.getsize(file_path)
            session.commit()

            # Log completion
            AuditLogger.log_action(
                action="data.export_completed",
                user_id=export_request.user_id,
                resource_type="data_export",
                resource_id=str(request_id),
                status="success",
                metadata={"file_size": export_request.file_size_bytes},
                session=session,
            )

            logger.info(f"Data export completed: {request_id}")
            return str(file_path)

        except Exception as e:
            logger.error(f"Failed to process export request {request_id}: {e}")
            if export_request:
                export_request.status = "failed"
                export_request.error_message = str(e)
                session.commit()
            return None
        finally:
            if should_close_session:
                session.close()

    def _collect_user_data(self, user_id: int, session: Session) -> Dict[str, Any]:
        """Collect all user data from various tables."""
        data = {}

        # User profile
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            data["user_profile"] = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
            }

        # API Keys (excluding sensitive hashes)
        api_keys = session.query(APIKey).filter_by(user_id=user_id).all()
        data["api_keys"] = [
            {
                "id": key.id,
                "key_name": key.key_name,
                "key_prefix": key.key_prefix,
                "scopes": key.scopes,
                "is_active": key.is_active,
                "created_at": key.created_at.isoformat() if key.created_at else None,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
            }
            for key in api_keys
        ]

        # Email preferences
        email_pref = session.query(EmailPreference).filter_by(user_id=user_id).first()
        if email_pref:
            data["email_preferences"] = {
                "receive_match_found": email_pref.receive_match_found,
                "receive_processing_complete": email_pref.receive_processing_complete,
                "receive_feature_announcements": email_pref.receive_feature_announcements,
                "receive_tips_tricks": email_pref.receive_tips_tricks,
                "preferred_language": email_pref.preferred_language,
            }

        # Email logs (summary)
        email_logs = session.query(EmailLog).filter_by(user_id=user_id).all()
        data["email_history"] = [
            {
                "subject": log.subject,
                "category": log.category,
                "status": log.status,
                "sent_at": log.sent_at.isoformat() if log.sent_at else None,
            }
            for log in email_logs
        ]

        # Consent records
        consents = session.query(UserConsent).filter_by(user_id=user_id).all()
        data["consents"] = [
            {
                "consent_type": consent.consent_type,
                "consent_version": consent.consent_version,
                "given": consent.given,
                "given_at": consent.given_at.isoformat() if consent.given_at else None,
                "withdrawn_at": (
                    consent.withdrawn_at.isoformat() if consent.withdrawn_at else None
                ),
            }
            for consent in consents
        ]

        # Audit logs (last 100 entries)
        audit_logs = (
            session.query(AuditLog)
            .filter_by(user_id=user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(100)
            .all()
        )
        data["activity_logs"] = [
            {
                "action": log.action,
                "resource_type": log.resource_type,
                "status": log.status,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in audit_logs
        ]

        return data

    def _generate_export_file(
        self, user_id: int, data: Dict[str, Any], format: str
    ) -> Path:
        """Generate export file in requested format."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"user_data_export_{user_id}_{timestamp}.{format}"
        file_path = self.export_dir / filename

        if format == "json":
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}. Only 'json' is currently supported.")

        return file_path

    def record_download(
        self, request_id: int, session: Optional[Session] = None
    ) -> bool:
        """Record that a user has downloaded their export."""
        should_close_session = False
        if session is None:
            session = db_manager.get_session()
            should_close_session = True

        try:
            export_request = session.query(DataExportRequest).filter_by(id=request_id).first()
            if export_request:
                export_request.download_count = (export_request.download_count or 0) + 1
                export_request.last_downloaded_at = datetime.utcnow()
                session.commit()

                # Log download
                AuditLogger.log_action(
                    action="data.export_downloaded",
                    user_id=export_request.user_id,
                    resource_type="data_export",
                    resource_id=str(request_id),
                    status="success",
                    session=session,
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to record download: {e}")
            return False
        finally:
            if should_close_session:
                session.close()
