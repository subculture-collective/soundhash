"""Consent management service for GDPR compliance."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.compliance.audit_logger import AuditLogger
from src.database.connection import db_manager
from src.database.models import UserConsent

logger = logging.getLogger(__name__)


class ConsentManager:
    """Service for managing user consent records."""

    @staticmethod
    def record_consent(
        user_id: int,
        consent_type: str,
        consent_version: str,
        given: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        method: str = "web_form",
        metadata: Optional[dict] = None,
        session: Optional[Session] = None,
    ) -> UserConsent:
        """
        Record user consent.
        
        Args:
            user_id: ID of user giving consent
            consent_type: Type of consent (e.g., 'terms_of_service', 'privacy_policy')
            consent_version: Version of the document
            given: True if consenting, False if withdrawing
            ip_address: IP address of request
            user_agent: User agent string
            method: Method of consent collection
            metadata: Additional metadata
            session: Database session
            
        Returns:
            UserConsent object
        """
        should_close_session = False
        if session is None:
            session = db_manager.get_session()
            should_close_session = True

        try:
            consent = UserConsent(
                user_id=user_id,
                consent_type=consent_type,
                consent_version=consent_version,
                given=given,
                given_at=datetime.utcnow(),
                withdrawn_at=None if given else datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                method=method,
                metadata=metadata,
            )
            session.add(consent)
            session.commit()

            # Log consent action
            AuditLogger.log_action(
                action=f"consent.{consent_type}.{'given' if given else 'withdrawn'}",
                user_id=user_id,
                resource_type="consent",
                resource_id=str(consent.id),
                ip_address=ip_address,
                user_agent=user_agent,
                status="success",
                metadata={
                    "consent_type": consent_type,
                    "consent_version": consent_version,
                    "given": given,
                },
                session=session,
            )

            logger.info(
                f"Consent {'given' if given else 'withdrawn'}: {consent_type} "
                f"v{consent_version} by user {user_id}"
            )
            return consent
        except Exception as e:
            logger.error(f"Failed to record consent: {e}")
            session.rollback()
            raise
        finally:
            if should_close_session:
                session.close()

    @staticmethod
    def withdraw_consent(
        user_id: int,
        consent_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session: Optional[Session] = None,
    ) -> bool:
        """
        Withdraw previously given consent.
        
        Args:
            user_id: ID of user withdrawing consent
            consent_type: Type of consent to withdraw
            ip_address: IP address of request
            user_agent: User agent string
            session: Database session
            
        Returns:
            True if successful, False otherwise
        """
        should_close_session = False
        if session is None:
            session = db_manager.get_session()
            should_close_session = True

        try:
            # Find the most recent consent of this type
            consent = (
                session.query(UserConsent)
                .filter_by(user_id=user_id, consent_type=consent_type, given=True)
                .order_by(UserConsent.given_at.desc())
                .first()
            )

            if not consent:
                logger.warning(f"No active consent found for user {user_id}, type {consent_type}")
                return False

            # Record withdrawal as a new entry
            withdrawal = UserConsent(
                user_id=user_id,
                consent_type=consent_type,
                consent_version=consent.consent_version,
                given=False,
                given_at=datetime.utcnow(),
                withdrawn_at=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                method="web_form",
            )
            session.add(withdrawal)
            session.commit()

            # Log withdrawal
            AuditLogger.log_action(
                action=f"consent.{consent_type}.withdrawn",
                user_id=user_id,
                resource_type="consent",
                resource_id=str(withdrawal.id),
                ip_address=ip_address,
                user_agent=user_agent,
                status="success",
                session=session,
            )

            logger.info(f"Consent withdrawn: {consent_type} by user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to withdraw consent: {e}")
            session.rollback()
            return False
        finally:
            if should_close_session:
                session.close()

    @staticmethod
    def check_consent(
        user_id: int, consent_type: str, session: Optional[Session] = None
    ) -> bool:
        """
        Check if user has given consent for a specific type.
        
        Args:
            user_id: ID of user
            consent_type: Type of consent to check
            session: Database session
            
        Returns:
            True if user has active consent, False otherwise
        """
        should_close_session = False
        if session is None:
            session = db_manager.get_session()
            should_close_session = True

        try:
            # Get most recent consent record
            consent = (
                session.query(UserConsent)
                .filter_by(user_id=user_id, consent_type=consent_type)
                .order_by(UserConsent.created_at.desc())
                .first()
            )

            return consent is not None and consent.given
        finally:
            if should_close_session:
                session.close()

    @staticmethod
    def get_consent_history(
        user_id: int, consent_type: Optional[str] = None, session: Optional[Session] = None
    ) -> list:
        """
        Get consent history for a user.
        
        Args:
            user_id: ID of user
            consent_type: Optional specific consent type to filter
            session: Database session
            
        Returns:
            List of consent records
        """
        should_close_session = False
        if session is None:
            session = db_manager.get_session()
            should_close_session = True

        try:
            query = session.query(UserConsent).filter_by(user_id=user_id)
            if consent_type:
                query = query.filter_by(consent_type=consent_type)

            return query.order_by(UserConsent.created_at.desc()).all()
        finally:
            if should_close_session:
                session.close()
