"""API key rotation and management."""

import logging
import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from src.api.auth import get_password_hash, verify_password
from src.database.models import APIKey, User

logger = logging.getLogger(__name__)


class APIKeyManager:
    """Manage API keys with rotation and expiration."""

    def __init__(self, db: Session):
        """Initialize API key manager."""
        self.db = db

    def generate_key(self) -> str:
        """Generate a new API key."""
        return f"sk_{secrets.token_urlsafe(32)}"

    def create_key(
        self,
        user: User,
        name: str,
        expires_days: int | None = None,
    ) -> tuple[APIKey, str]:
        """
        Create a new API key for a user.

        Args:
            user: User to create key for
            name: Descriptive name for the key
            expires_days: Days until key expires (None = never expires)

        Returns:
            Tuple of (APIKey record, plain_text_key)
        """
        # Generate new key
        plain_key = self.generate_key()
        key_hash = get_password_hash(plain_key)

        # Calculate expiration
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)

        # Create key record
        api_key = APIKey(
            user_id=user.id,
            name=name,
            key_hash=key_hash,
            key_prefix=plain_key[:8],
            expires_at=expires_at,
            is_active=True,
        )

        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)

        logger.info(
            f"Created API key '{name}' for user {user.username} (expires: {expires_at})"
        )

        return api_key, plain_key

    def rotate_key(self, key_id: int) -> tuple[APIKey | None, str | None]:
        """
        Rotate an API key by creating a new one and deactivating the old one.

        Args:
            key_id: ID of the key to rotate

        Returns:
            Tuple of (new_APIKey, new_plain_text_key) or (None, None) if failed
        """
        # Get existing key
        old_key = self.db.query(APIKey).filter(APIKey.id == key_id).first()

        if not old_key:
            logger.error(f"API key {key_id} not found")
            return None, None

        # Get user
        user = self.db.query(User).filter(User.id == old_key.user_id).first()
        if not user:
            logger.error(f"User {old_key.user_id} not found")
            return None, None

        # Create new key with same expiration policy
        expires_days = None
        if old_key.expires_at:
            delta = old_key.expires_at - datetime.utcnow()
            expires_days = max(1, delta.days)

        new_key, plain_key = self.create_key(
            user=user,
            name=f"{old_key.name} (rotated)",
            expires_days=expires_days,
        )

        # Deactivate old key
        old_key.is_active = False
        self.db.commit()

        logger.info(
            f"Rotated API key {key_id} for user {user.username}. New key ID: {new_key.id}"
        )

        return new_key, plain_key

    def revoke_key(self, key_id: int, reason: str | None = None) -> bool:
        """
        Revoke (deactivate) an API key.

        Args:
            key_id: ID of the key to revoke
            reason: Optional reason for revocation

        Returns:
            True if successful
        """
        api_key = self.db.query(APIKey).filter(APIKey.id == key_id).first()

        if not api_key:
            logger.error(f"API key {key_id} not found")
            return False

        api_key.is_active = False
        self.db.commit()

        logger.info(
            f"Revoked API key {key_id} (prefix: {api_key.key_prefix}). Reason: {reason}"
        )

        return True

    def list_user_keys(self, user_id: int, include_inactive: bool = False) -> list[APIKey]:
        """
        List all API keys for a user.

        Args:
            user_id: User ID
            include_inactive: Include inactive/revoked keys

        Returns:
            List of APIKey records
        """
        query = self.db.query(APIKey).filter(APIKey.user_id == user_id)

        if not include_inactive:
            query = query.filter(APIKey.is_active)

        return query.order_by(APIKey.created_at.desc()).all()

    def cleanup_expired_keys(self) -> int:
        """
        Deactivate expired API keys.

        Returns:
            Number of keys deactivated
        """
        now = datetime.utcnow()

        expired_keys = (
            self.db.query(APIKey)
            .filter(
                APIKey.is_active,
                APIKey.expires_at.isnot(None),
                APIKey.expires_at < now,
            )
            .all()
        )

        count = len(expired_keys)

        for key in expired_keys:
            key.is_active = False

        if count > 0:
            self.db.commit()
            logger.info(f"Deactivated {count} expired API keys")

        return count

    def get_key_by_id(self, key_id: int) -> APIKey | None:
        """Get API key by ID."""
        return self.db.query(APIKey).filter(APIKey.id == key_id).first()

    def verify_key(self, plain_key: str) -> APIKey | None:
        """
        Verify a plain text API key and return the key record.

        Args:
            plain_key: Plain text API key

        Returns:
            APIKey record if valid, None otherwise
        """
        # Get prefix
        prefix = plain_key[:8] if len(plain_key) > 8 else plain_key

        # Find keys with matching prefix
        candidate_keys = (
            self.db.query(APIKey)
            .filter(
                APIKey.key_prefix == prefix,
                APIKey.is_active,
            )
            .all()
        )

        # Verify hash
        for key in candidate_keys:
            if verify_password(plain_key, key.key_hash):
                # Check expiration
                if key.expires_at and key.expires_at < datetime.utcnow():
                    logger.warning(f"API key {key.id} is expired")
                    key.is_active = False
                    self.db.commit()
                    return None

                # Update last used
                key.last_used_at = datetime.utcnow()
                self.db.commit()

                return key

        return None

    def get_key_stats(self, key_id: int) -> dict | None:
        """Get statistics for an API key."""
        key = self.get_key_by_id(key_id)

        if not key:
            return None

        return {
            "id": key.id,
            "name": key.name,
            "prefix": key.key_prefix,
            "created_at": key.created_at.isoformat(),
            "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
            "expires_at": key.expires_at.isoformat() if key.expires_at else None,
            "is_active": key.is_active,
            "days_until_expiry": (key.expires_at - datetime.utcnow()).days
            if key.expires_at
            else None,
        }
