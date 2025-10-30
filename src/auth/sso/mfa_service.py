"""Multi-Factor Authentication (MFA) service implementation."""

import hashlib
import logging
import secrets
from datetime import datetime
from typing import List, Optional, Tuple

import pyotp
from sqlalchemy.orm import Session

from src.database.sso_models import MFADevice, SSOAuditLog
from src.database.models import User

logger = logging.getLogger(__name__)


class MFAService:
    """Multi-Factor Authentication service for TOTP, SMS, Email, WebAuthn."""

    def __init__(self, db: Session):
        """Initialize MFA service.

        Args:
            db: Database session
        """
        self.db = db

    def setup_totp(
        self,
        user: User,
        device_name: str = "Authenticator App",
    ) -> Tuple[str, str]:
        """Set up TOTP (Time-based One-Time Password) for a user.

        Args:
            user: User to set up TOTP for
            device_name: User-friendly name for the device

        Returns:
            Tuple of (secret, provisioning_uri) for QR code generation
        """
        # Generate a new TOTP secret
        secret = pyotp.random_base32()

        # Create provisioning URI for QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="SoundHash",
        )

        # Save MFA device (unverified until user confirms with a code)
        mfa_device = MFADevice(
            user_id=user.id,
            device_type="totp",
            device_name=device_name,
            totp_secret=secret,
            totp_algorithm="SHA1",
            totp_digits=6,
            totp_period=30,
            is_verified=False,
            is_active=False,  # Will be activated after verification
        )

        self.db.add(mfa_device)
        self.db.commit()

        return secret, provisioning_uri

    def verify_totp_setup(
        self,
        user: User,
        code: str,
    ) -> bool:
        """Verify TOTP setup by checking the code.

        Args:
            user: User verifying TOTP
            code: TOTP code to verify

        Returns:
            True if verification successful
        """
        # Find the unverified TOTP device
        mfa_device = (
            self.db.query(MFADevice)
            .filter(
                MFADevice.user_id == user.id,
                MFADevice.device_type == "totp",
                MFADevice.is_verified == False,
            )
            .first()
        )

        if not mfa_device:
            logger.error(f"No unverified TOTP device found for user {user.id}")
            return False

        # Verify the code
        totp = pyotp.TOTP(mfa_device.totp_secret)
        if totp.verify(code, valid_window=1):  # Allow 1 window tolerance (30s before/after)
            mfa_device.is_verified = True
            mfa_device.is_active = True
            mfa_device.verified_at = datetime.utcnow()

            # Make this the primary device if no other primary exists
            primary_device = (
                self.db.query(MFADevice)
                .filter(
                    MFADevice.user_id == user.id,
                    MFADevice.is_primary == True,
                )
                .first()
            )
            if not primary_device:
                mfa_device.is_primary = True

            self.db.commit()
            logger.info(f"TOTP verified successfully for user {user.id}")
            return True

        logger.warning(f"TOTP verification failed for user {user.id}")
        return False

    def verify_totp_code(
        self,
        user: User,
        code: str,
        device_id: Optional[int] = None,
    ) -> bool:
        """Verify a TOTP code during authentication.

        Args:
            user: User attempting authentication
            code: TOTP code to verify
            device_id: Optional specific device ID to check

        Returns:
            True if code is valid
        """
        query = self.db.query(MFADevice).filter(
            MFADevice.user_id == user.id,
            MFADevice.device_type == "totp",
            MFADevice.is_verified == True,
            MFADevice.is_active == True,
        )

        if device_id:
            query = query.filter(MFADevice.id == device_id)

        mfa_devices = query.all()

        for device in mfa_devices:
            totp = pyotp.TOTP(device.totp_secret)
            if totp.verify(code, valid_window=1):
                # Update usage tracking
                device.last_used_at = datetime.utcnow()
                device.use_count += 1
                self.db.commit()

                logger.info(f"TOTP verification successful for user {user.id}")
                return True

        logger.warning(f"TOTP verification failed for user {user.id}")
        return False

    def generate_backup_codes(
        self,
        user: User,
        count: int = 10,
    ) -> List[str]:
        """Generate backup codes for emergency MFA access.

        Args:
            user: User to generate backup codes for
            count: Number of backup codes to generate

        Returns:
            List of backup codes
        """
        codes = []
        hashed_codes = []

        for _ in range(count):
            # Generate a random 8-character alphanumeric code
            code = secrets.token_urlsafe(6).upper()[:8]
            codes.append(code)

            # Hash the code for storage
            hashed = hashlib.sha256(code.encode()).hexdigest()
            hashed_codes.append(hashed)

        # Save backup codes device
        mfa_device = MFADevice(
            user_id=user.id,
            device_type="backup_codes",
            device_name="Backup Codes",
            backup_codes=hashed_codes,
            is_verified=True,
            is_active=True,
        )

        self.db.add(mfa_device)
        self.db.commit()

        logger.info(f"Generated {count} backup codes for user {user.id}")
        return codes

    def verify_backup_code(
        self,
        user: User,
        code: str,
    ) -> bool:
        """Verify a backup code (one-time use).

        Args:
            user: User attempting authentication
            code: Backup code to verify

        Returns:
            True if code is valid
        """
        # Find backup codes device
        device = (
            self.db.query(MFADevice)
            .filter(
                MFADevice.user_id == user.id,
                MFADevice.device_type == "backup_codes",
                MFADevice.is_active == True,
            )
            .first()
        )

        if not device or not device.backup_codes:
            logger.warning(f"No backup codes found for user {user.id}")
            return False

        # Hash the provided code
        hashed = hashlib.sha256(code.encode()).hexdigest()

        # Check if code exists in list
        if hashed in device.backup_codes:
            # Remove the used code
            device.backup_codes.remove(hashed)
            
            # Mark the JSON field as modified so SQLAlchemy tracks the change
            from sqlalchemy.orm import attributes
            attributes.flag_modified(device, "backup_codes")

            # Update usage tracking
            device.last_used_at = datetime.utcnow()
            device.use_count += 1

            # Deactivate if no codes left
            if not device.backup_codes:
                device.is_active = False
                logger.info(f"All backup codes used for user {user.id}")

            self.db.commit()

            logger.info(f"Backup code verification successful for user {user.id}")
            return True

        logger.warning(f"Invalid backup code for user {user.id}")
        return False

    def get_user_mfa_devices(
        self,
        user: User,
        active_only: bool = True,
    ) -> List[MFADevice]:
        """Get all MFA devices for a user.

        Args:
            user: User to get devices for
            active_only: Only return active devices

        Returns:
            List of MFA devices
        """
        query = self.db.query(MFADevice).filter(MFADevice.user_id == user.id)

        if active_only:
            query = query.filter(MFADevice.is_active == True)

        return query.order_by(MFADevice.is_primary.desc(), MFADevice.created_at).all()

    def remove_mfa_device(
        self,
        user: User,
        device_id: int,
    ) -> bool:
        """Remove/deactivate an MFA device.

        Args:
            user: User who owns the device
            device_id: ID of device to remove

        Returns:
            True if device was removed successfully
        """
        device = (
            self.db.query(MFADevice)
            .filter(
                MFADevice.id == device_id,
                MFADevice.user_id == user.id,
            )
            .first()
        )

        if not device:
            logger.error(f"MFA device {device_id} not found for user {user.id}")
            return False

        # If this was the primary device, make another device primary
        if device.is_primary:
            other_device = (
                self.db.query(MFADevice)
                .filter(
                    MFADevice.user_id == user.id,
                    MFADevice.id != device_id,
                    MFADevice.is_active == True,
                )
                .first()
            )
            if other_device:
                other_device.is_primary = True

        device.is_active = False
        self.db.commit()

        logger.info(f"Removed MFA device {device_id} for user {user.id}")
        return True

    def set_primary_device(
        self,
        user: User,
        device_id: int,
    ) -> bool:
        """Set an MFA device as the primary device.

        Args:
            user: User who owns the device
            device_id: ID of device to set as primary

        Returns:
            True if successful
        """
        # Remove primary flag from all devices
        self.db.query(MFADevice).filter(
            MFADevice.user_id == user.id,
            MFADevice.is_primary == True,
        ).update({"is_primary": False})

        # Set new primary device
        device = (
            self.db.query(MFADevice)
            .filter(
                MFADevice.id == device_id,
                MFADevice.user_id == user.id,
                MFADevice.is_active == True,
            )
            .first()
        )

        if not device:
            logger.error(f"MFA device {device_id} not found for user {user.id}")
            return False

        device.is_primary = True
        self.db.commit()

        logger.info(f"Set MFA device {device_id} as primary for user {user.id}")
        return True

    def is_mfa_enabled(self, user: User) -> bool:
        """Check if user has MFA enabled.

        Args:
            user: User to check

        Returns:
            True if user has at least one active MFA device
        """
        count = (
            self.db.query(MFADevice)
            .filter(
                MFADevice.user_id == user.id,
                MFADevice.is_active == True,
                MFADevice.is_verified == True,
            )
            .count()
        )

        return count > 0
