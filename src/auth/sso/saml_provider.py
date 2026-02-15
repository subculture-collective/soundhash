"""SAML 2.0 authentication provider implementation."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from sqlalchemy.orm import Session

from src.database.sso_models import SSOProvider, SSOSession, SSOAuditLog
from src.database.models import User

logger = logging.getLogger(__name__)


class SAMLProvider:
    """SAML 2.0 authentication provider."""

    def __init__(self, provider_config: SSOProvider, db: Session):
        """Initialize SAML provider with configuration.

        Args:
            provider_config: SSO provider configuration from database
            db: Database session
        """
        self.provider = provider_config
        self.db = db
        self.settings = self._build_saml_settings()

    def _build_saml_settings(self) -> Dict[str, Any]:
        """Build SAML settings from provider configuration."""
        return {
            "strict": True,
            "debug": False,
            "sp": {
                "entityId": self.provider.saml_sp_entity_id,
                "assertionConsumerService": {
                    "url": self.provider.saml_acs_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
                "singleLogoutService": {
                    "url": f"{self.provider.saml_acs_url}/slo",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "NameIDFormat": self.provider.saml_name_id_format,
            },
            "idp": {
                "entityId": self.provider.saml_entity_id,
                "singleSignOnService": {
                    "url": self.provider.saml_sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "singleLogoutService": {
                    "url": self.provider.saml_slo_url or "",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": self.provider.saml_x509_cert,
            },
            "security": {
                "nameIdEncrypted": False,
                "authnRequestsSigned": False,
                "logoutRequestSigned": False,
                "logoutResponseSigned": False,
                "signMetadata": False,
                "wantMessagesSigned": False,
                "wantAssertionsSigned": True,
                "wantAssertionsEncrypted": False,
                "wantNameId": True,
                "wantNameIdEncrypted": False,
                "wantAttributeStatement": True,
            },
        }

    def initiate_login(self, request_data: Dict[str, Any]) -> str:
        """Initiate SAML login flow.

        Args:
            request_data: FastAPI request data

        Returns:
            SAML redirect URL
        """
        auth = OneLogin_Saml2_Auth(request_data, self.settings)
        return auth.login()

    def handle_callback(
        self, request_data: Dict[str, Any], ip_address: str, user_agent: str
    ) -> Optional[User]:
        """Handle SAML callback and authenticate user.

        Args:
            request_data: SAML response data
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Authenticated User object or None if authentication failed
        """
        try:
            auth = OneLogin_Saml2_Auth(request_data, self.settings)
            auth.process_response()

            errors = auth.get_errors()
            if errors:
                error_msg = f"SAML authentication errors: {', '.join(errors)}"
                logger.error(error_msg)
                self._log_auth_event(
                    event_type="login",
                    event_status="failure",
                    event_message=error_msg,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                return None

            if not auth.is_authenticated():
                self._log_auth_event(
                    event_type="login",
                    event_status="failure",
                    event_message="User not authenticated",
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                return None

            # Extract user attributes from SAML response
            attributes = auth.get_attributes()
            name_id = auth.get_nameid()
            session_index = auth.get_session_index()

            # Map attributes to user fields
            user_data = self._map_saml_attributes(attributes, name_id)

            # Find or create user (JIT provisioning)
            user = self._find_or_create_user(user_data)

            if user:
                # Update role based on IdP groups if role mapping is enabled
                if self.provider.enable_role_mapping:
                    self._update_user_role(user, attributes)

                self._log_auth_event(
                    event_type="login",
                    event_status="success",
                    event_message="SAML authentication successful",
                    user_id=user.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    idp_response_data={"name_id": name_id, "session_index": session_index},
                )

                return user

        except Exception as e:
            logger.error(f"SAML authentication error: {str(e)}", exc_info=True)
            self._log_auth_event(
                event_type="login",
                event_status="error",
                event_message=f"SAML authentication error: {str(e)}",
                ip_address=ip_address,
                user_agent=user_agent,
                error_details=str(e),
            )

        return None

    def _map_saml_attributes(
        self, attributes: Dict[str, list], name_id: str
    ) -> Dict[str, str]:
        """Map SAML attributes to user fields.

        Args:
            attributes: SAML attributes from IdP
            name_id: SAML NameID

        Returns:
            Mapped user data
        """
        mappings = self.provider.attribute_mappings or {}

        user_data = {"email": name_id}  # Default to NameID as email

        for field, attr_name in mappings.items():
            if attr_name in attributes and attributes[attr_name]:
                user_data[field] = attributes[attr_name][0]

        return user_data

    def _find_or_create_user(self, user_data: Dict[str, str]) -> Optional[User]:
        """Find existing user or create new user (JIT provisioning).

        Args:
            user_data: User data from SAML response

        Returns:
            User object or None
        """
        email = user_data.get("email")
        if not email:
            logger.error("No email found in SAML response")
            return None

        # Try to find existing user
        user = self.db.query(User).filter(User.email == email).first()

        if user:
            # Update user info if changed
            if "full_name" in user_data and user_data["full_name"] != user.full_name:
                user.full_name = user_data["full_name"]
                user.updated_at = datetime.now(timezone.utc)
            user.last_login = datetime.now(timezone.utc)
            self.db.commit()
            return user

        # Create new user if JIT provisioning is enabled
        if self.provider.enable_jit_provisioning:
            username = email.split("@")[0]
            # Ensure username is unique
            base_username = username
            counter = 1
            while self.db.query(User).filter(User.username == username).first():
                username = f"{base_username}{counter}"
                counter += 1

            user = User(
                username=username,
                email=email,
                full_name=user_data.get("full_name", ""),
                hashed_password="",  # SSO users don't have passwords
                tenant_id=self.provider.tenant_id,
                role=self.provider.default_role or "member",
                is_active=True,
                is_verified=True,  # SSO users are pre-verified
            )

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            logger.info(f"Created new user via JIT provisioning: {email}")
            return user

        logger.warning(f"JIT provisioning disabled, user not found: {email}")
        return None

    def _update_user_role(self, user: User, attributes: Dict[str, list]) -> None:
        """Update user role based on IdP group membership.

        Args:
            user: User to update
            attributes: SAML attributes containing group information
        """
        if not self.provider.role_mappings:
            return

        # Get user groups from SAML attributes
        groups = attributes.get("groups", []) or attributes.get("memberOf", [])

        for group in groups:
            if group in self.provider.role_mappings:
                new_role = self.provider.role_mappings[group]
                if new_role != user.role:
                    logger.info(f"Updating user {user.email} role from {user.role} to {new_role}")
                    user.role = new_role
                    self.db.commit()
                    break

    def _log_auth_event(
        self,
        event_type: str,
        event_status: str,
        event_message: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        idp_response_data: Optional[Dict] = None,
        error_details: Optional[str] = None,
    ) -> None:
        """Log authentication event to audit log.

        Args:
            event_type: Type of event (login, logout, etc.)
            event_status: Status of event (success, failure, error)
            event_message: Human-readable message
            user_id: User ID if available
            ip_address: Client IP address
            user_agent: Client user agent
            idp_response_data: Sanitized IdP response data
            error_details: Error details if applicable
        """
        audit_log = SSOAuditLog(
            tenant_id=self.provider.tenant_id,
            user_id=user_id,
            provider_id=self.provider.id,
            event_type=event_type,
            event_status=event_status,
            event_message=event_message,
            ip_address=ip_address,
            user_agent=user_agent,
            idp_response_data=idp_response_data,
            error_details=error_details,
        )

        self.db.add(audit_log)
        self.db.commit()

    def initiate_logout(
        self, request_data: Dict[str, Any], name_id: str, session_index: str
    ) -> str:
        """Initiate SAML logout flow.

        Args:
            request_data: FastAPI request data
            name_id: SAML NameID
            session_index: SAML session index

        Returns:
            SAML logout redirect URL
        """
        auth = OneLogin_Saml2_Auth(request_data, self.settings)
        return auth.logout(name_id=name_id, session_index=session_index)

    def handle_logout_callback(self, request_data: Dict[str, Any]) -> bool:
        """Handle SAML logout callback.

        Args:
            request_data: SAML logout response data

        Returns:
            True if logout was successful
        """
        try:
            auth = OneLogin_Saml2_Auth(request_data, self.settings)
            auth.process_slo()

            errors = auth.get_errors()
            if errors:
                logger.error(f"SAML logout errors: {', '.join(errors)}")
                return False

            return True

        except Exception as e:
            logger.error(f"SAML logout error: {str(e)}", exc_info=True)
            return False
