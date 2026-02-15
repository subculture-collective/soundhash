"""SSO session management for multi-device support."""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from src.database.sso_models import SSOProvider, SSOSession
from src.database.models import User

logger = logging.getLogger(__name__)


class SSOSessionManager:
    """Manage SSO sessions across multiple devices."""

    def __init__(self, db: Session):
        """Initialize session manager.

        Args:
            db: Database session
        """
        self.db = db

    def create_session(
        self,
        user: User,
        provider: SSOProvider,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        device_type: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        idp_session_id: Optional[str] = None,
        idp_session_index: Optional[str] = None,
        session_duration_hours: int = 24,
    ) -> SSOSession:
        """Create a new SSO session.

        Args:
            user: User for the session
            provider: SSO provider used
            device_id: Device identifier
            device_name: User-friendly device name
            device_type: Type of device (desktop, mobile, tablet, other)
            ip_address: Client IP address
            user_agent: Client user agent
            idp_session_id: Session ID from IdP
            idp_session_index: SAML SessionIndex
            session_duration_hours: Session duration in hours (default 24)

        Returns:
            Created SSOSession object
        """
        # Generate secure session token
        session_token = secrets.token_urlsafe(64)

        # Calculate expiration
        expires_at = datetime.now(timezone.utc) + timedelta(hours=session_duration_hours)

        # Create session
        session = SSOSession(
            user_id=user.id,
            provider_id=provider.id,
            session_token=session_token,
            device_id=device_id,
            device_name=device_name or self._parse_device_name(user_agent),
            device_type=device_type or self._parse_device_type(user_agent),
            ip_address=ip_address,
            user_agent=user_agent,
            idp_session_id=idp_session_id,
            idp_session_index=idp_session_index,
            is_active=True,
            expires_at=expires_at,
            mfa_verified=False,  # Will be set to True after MFA verification
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        logger.info(f"Created SSO session {session.id} for user {user.id}")
        return session

    def get_session(
        self,
        session_token: str,
        check_expiration: bool = True,
    ) -> Optional[SSOSession]:
        """Get session by token.

        Args:
            session_token: Session token to look up
            check_expiration: Whether to check if session is expired

        Returns:
            SSOSession object or None if not found/expired
        """
        session = (
            self.db.query(SSOSession)
            .filter(
                SSOSession.session_token == session_token,
                SSOSession.is_active == True,
            )
            .first()
        )

        if not session:
            return None

        if check_expiration and session.expires_at < datetime.now(timezone.utc):
            logger.info(f"Session {session.id} has expired")
            self.terminate_session(session.id)
            return None

        # Update last activity
        session.last_activity = datetime.now(timezone.utc)
        self.db.commit()

        return session

    def get_session_by_id(
        self,
        session_id: int,
        check_expiration: bool = True,
    ) -> Optional[SSOSession]:
        """Get session by ID.

        Args:
            session_id: Session ID to look up
            check_expiration: Whether to check if session is expired

        Returns:
            SSOSession object or None if not found/expired
        """
        session = (
            self.db.query(SSOSession)
            .filter(
                SSOSession.id == session_id,
                SSOSession.is_active == True,
            )
            .first()
        )

        if not session:
            return None

        if check_expiration and session.expires_at < datetime.now(timezone.utc):
            logger.info(f"Session {session.id} has expired")
            self.terminate_session(session.id)
            return None

        # Update last activity
        session.last_activity = datetime.now(timezone.utc)
        self.db.commit()

        return session

    def get_user_sessions(
        self,
        user: User,
        active_only: bool = True,
    ) -> List[SSOSession]:
        """Get all sessions for a user.

        Args:
            user: User to get sessions for
            active_only: Only return active sessions

        Returns:
            List of SSOSession objects
        """
        query = self.db.query(SSOSession).filter(SSOSession.user_id == user.id)

        if active_only:
            query = query.filter(
                SSOSession.is_active == True,
                SSOSession.expires_at > datetime.now(timezone.utc),
            )

        return query.order_by(SSOSession.last_activity.desc()).all()

    def mark_mfa_verified(
        self,
        session_id: int,
        mfa_method: str,
    ) -> bool:
        """Mark session as MFA verified.

        Args:
            session_id: Session ID to update
            mfa_method: MFA method used (totp, sms, email, push)

        Returns:
            True if successful
        """
        session = self.db.query(SSOSession).filter(SSOSession.id == session_id).first()

        if not session:
            logger.error(f"Session {session_id} not found")
            return False

        session.mfa_verified = True
        session.mfa_method = mfa_method
        session.mfa_verified_at = datetime.now(timezone.utc)
        self.db.commit()

        logger.info(f"Marked session {session_id} as MFA verified")
        return True

    def terminate_session(
        self,
        session_id: int,
    ) -> bool:
        """Terminate a session.

        Args:
            session_id: Session ID to terminate

        Returns:
            True if successful
        """
        session = self.db.query(SSOSession).filter(SSOSession.id == session_id).first()

        if not session:
            logger.error(f"Session {session_id} not found")
            return False

        session.is_active = False
        session.terminated_at = datetime.now(timezone.utc)
        self.db.commit()

        logger.info(f"Terminated session {session_id}")
        return True

    def terminate_user_sessions(
        self,
        user: User,
        except_session_id: Optional[int] = None,
    ) -> int:
        """Terminate all sessions for a user.

        Args:
            user: User to terminate sessions for
            except_session_id: Optional session ID to keep active

        Returns:
            Number of sessions terminated
        """
        query = self.db.query(SSOSession).filter(
            SSOSession.user_id == user.id,
            SSOSession.is_active == True,
        )

        if except_session_id:
            query = query.filter(SSOSession.id != except_session_id)

        sessions = query.all()

        for session in sessions:
            session.is_active = False
            session.terminated_at = datetime.now(timezone.utc)

        self.db.commit()

        logger.info(f"Terminated {len(sessions)} sessions for user {user.id}")
        return len(sessions)

    def extend_session(
        self,
        session_id: int,
        additional_hours: int = 24,
    ) -> bool:
        """Extend session expiration.

        Args:
            session_id: Session ID to extend
            additional_hours: Hours to add to expiration

        Returns:
            True if successful
        """
        session = self.db.query(SSOSession).filter(SSOSession.id == session_id).first()

        if not session:
            logger.error(f"Session {session_id} not found")
            return False

        session.expires_at = session.expires_at + timedelta(hours=additional_hours)
        self.db.commit()

        logger.info(f"Extended session {session_id} by {additional_hours} hours")
        return True

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        expired_sessions = (
            self.db.query(SSOSession)
            .filter(
                SSOSession.is_active == True,
                SSOSession.expires_at < datetime.now(timezone.utc),
            )
            .all()
        )

        for session in expired_sessions:
            session.is_active = False
            session.terminated_at = datetime.now(timezone.utc)

        self.db.commit()

        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        return len(expired_sessions)

    def _parse_device_name(self, user_agent: Optional[str]) -> str:
        """Parse device name from user agent.

        Args:
            user_agent: User agent string

        Returns:
            User-friendly device name
        """
        if not user_agent:
            return "Unknown Device"

        ua_lower = user_agent.lower()

        # Check for mobile devices
        if "iphone" in ua_lower:
            return "iPhone"
        elif "ipad" in ua_lower:
            return "iPad"
        elif "android" in ua_lower and "mobile" in ua_lower:
            return "Android Phone"
        elif "android" in ua_lower:
            return "Android Tablet"

        # Check for desktop browsers
        if "chrome" in ua_lower:
            return "Chrome Browser"
        elif "firefox" in ua_lower:
            return "Firefox Browser"
        elif "safari" in ua_lower:
            return "Safari Browser"
        elif "edge" in ua_lower:
            return "Edge Browser"

        return "Unknown Device"

    def _parse_device_type(self, user_agent: Optional[str]) -> str:
        """Parse device type from user agent.

        Args:
            user_agent: User agent string

        Returns:
            Device type (desktop, mobile, tablet, other)
        """
        if not user_agent:
            return "other"

        ua_lower = user_agent.lower()

        if "mobile" in ua_lower or "iphone" in ua_lower:
            return "mobile"
        elif "tablet" in ua_lower or "ipad" in ua_lower:
            return "tablet"
        elif any(x in ua_lower for x in ["windows", "mac", "linux", "chrome", "firefox", "safari"]):
            return "desktop"

        return "other"
