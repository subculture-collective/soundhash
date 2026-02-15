"""OAuth 2.0 authentication provider implementation."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from authlib.integrations.requests_client import OAuth2Session
from sqlalchemy.orm import Session

from src.database.sso_models import SSOProvider, SSOAuditLog
from src.database.models import User

logger = logging.getLogger(__name__)


class OAuth2Provider:
    """OAuth 2.0 authentication provider for Google, Microsoft, GitHub, etc."""

    # Pre-configured OAuth providers
    PROVIDER_CONFIGS = {
        "oauth2_google": {
            "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
            "scopes": ["openid", "email", "profile"],
            "user_email_field": "email",
            "user_name_field": "name",
        },
        "oauth2_microsoft": {
            "authorization_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "userinfo_url": "https://graph.microsoft.com/v1.0/me",
            "scopes": ["openid", "email", "profile", "User.Read"],
            "user_email_field": "mail",
            "user_name_field": "displayName",
        },
        "oauth2_github": {
            "authorization_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "userinfo_url": "https://api.github.com/user",
            "scopes": ["read:user", "user:email"],
            "user_email_field": "email",
            "user_name_field": "name",
        },
        "oauth2_azure_ad": {
            "authorization_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "userinfo_url": "https://graph.microsoft.com/v1.0/me",
            "scopes": ["openid", "email", "profile", "User.Read"],
            "user_email_field": "mail",
            "user_name_field": "displayName",
        },
    }

    def __init__(self, provider_config: SSOProvider, db: Session):
        """Initialize OAuth 2.0 provider with configuration.

        Args:
            provider_config: SSO provider configuration from database
            db: Database session
        """
        self.provider = provider_config
        self.db = db

        # Use pre-configured settings if provider type is known
        if provider_config.provider_type in self.PROVIDER_CONFIGS:
            preset = self.PROVIDER_CONFIGS[provider_config.provider_type]
            self.authorization_url = provider_config.oauth_authorization_url or preset["authorization_url"]
            self.token_url = provider_config.oauth_token_url or preset["token_url"]
            self.userinfo_url = provider_config.oauth_userinfo_url or preset["userinfo_url"]
            self.scopes = provider_config.oauth_scopes or preset["scopes"]
            self.user_email_field = preset["user_email_field"]
            self.user_name_field = preset["user_name_field"]
        else:
            # Use custom configuration
            self.authorization_url = provider_config.oauth_authorization_url
            self.token_url = provider_config.oauth_token_url
            self.userinfo_url = provider_config.oauth_userinfo_url
            self.scopes = provider_config.oauth_scopes or []
            self.user_email_field = "email"
            self.user_name_field = "name"

    def initiate_login(self, state: str) -> str:
        """Initiate OAuth 2.0 login flow.

        Args:
            state: Random state parameter for CSRF protection

        Returns:
            OAuth authorization URL
        """
        session = OAuth2Session(
            client_id=self.provider.oauth_client_id,
            redirect_uri=self.provider.oauth_redirect_uri,
            scope=self.scopes,
        )

        authorization_url, _ = session.create_authorization_url(
            self.authorization_url,
            state=state,
        )

        return authorization_url

    def handle_callback(
        self,
        code: str,
        state: str,
        ip_address: str,
        user_agent: str,
    ) -> Optional[User]:
        """Handle OAuth callback and authenticate user.

        Args:
            code: Authorization code from OAuth provider
            state: State parameter for CSRF validation
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Authenticated User object or None if authentication failed
        """
        try:
            # Exchange authorization code for access token
            session = OAuth2Session(
                client_id=self.provider.oauth_client_id,
                client_secret=self.provider.oauth_client_secret,
                redirect_uri=self.provider.oauth_redirect_uri,
            )

            token = session.fetch_token(
                self.token_url,
                code=code,
            )

            if not token:
                self._log_auth_event(
                    event_type="login",
                    event_status="failure",
                    event_message="Failed to obtain access token",
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                return None

            # Fetch user info from OAuth provider
            user_info = self._fetch_user_info(token["access_token"])

            if not user_info:
                self._log_auth_event(
                    event_type="login",
                    event_status="failure",
                    event_message="Failed to fetch user info",
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                return None

            # Map OAuth user info to our user fields
            user_data = self._map_oauth_attributes(user_info)

            # Find or create user (JIT provisioning)
            user = self._find_or_create_user(user_data)

            if user:
                # Update role based on OAuth groups if available and role mapping is enabled
                if self.provider.enable_role_mapping and "groups" in user_info:
                    self._update_user_role(user, user_info["groups"])

                self._log_auth_event(
                    event_type="login",
                    event_status="success",
                    event_message="OAuth authentication successful",
                    user_id=user.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    idp_response_data={"provider": self.provider.provider_type},
                )

                return user

        except Exception as e:
            logger.error(f"OAuth authentication error: {str(e)}", exc_info=True)
            self._log_auth_event(
                event_type="login",
                event_status="error",
                event_message=f"OAuth authentication error: {str(e)}",
                ip_address=ip_address,
                user_agent=user_agent,
                error_details=str(e),
            )

        return None

    def _fetch_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Fetch user information from OAuth provider.

        Args:
            access_token: OAuth access token

        Returns:
            User information dictionary or None
        """
        try:
            import requests

            headers = {"Authorization": f"Bearer {access_token}"}

            # GitHub requires specific Accept header
            if self.provider.provider_type == "oauth2_github":
                headers["Accept"] = "application/vnd.github.v3+json"

            response = requests.get(self.userinfo_url, headers=headers)
            response.raise_for_status()

            user_info = response.json()

            # For GitHub, fetch email separately if not in profile
            if self.provider.provider_type == "oauth2_github" and not user_info.get("email"):
                email_response = requests.get(
                    "https://api.github.com/user/emails",
                    headers=headers,
                )
                if email_response.ok:
                    emails = email_response.json()
                    primary_email = next((e for e in emails if e.get("primary")), None)
                    if primary_email:
                        user_info["email"] = primary_email["email"]

            return user_info

        except Exception as e:
            logger.error(f"Failed to fetch user info: {str(e)}", exc_info=True)
            return None

    def _map_oauth_attributes(self, user_info: Dict[str, Any]) -> Dict[str, str]:
        """Map OAuth user info to user fields.

        Args:
            user_info: User info from OAuth provider

        Returns:
            Mapped user data
        """
        mappings = self.provider.attribute_mappings or {}

        user_data = {
            "email": user_info.get(mappings.get("email", self.user_email_field), ""),
            "full_name": user_info.get(mappings.get("name", self.user_name_field), ""),
        }

        # Apply additional custom mappings
        for field, attr_name in mappings.items():
            if field not in user_data and attr_name in user_info:
                user_data[field] = user_info[attr_name]

        return user_data

    def _find_or_create_user(self, user_data: Dict[str, str]) -> Optional[User]:
        """Find existing user or create new user (JIT provisioning).

        Args:
            user_data: User data from OAuth response

        Returns:
            User object or None
        """
        email = user_data.get("email")
        if not email:
            logger.error("No email found in OAuth response")
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

    def _update_user_role(self, user: User, groups: list) -> None:
        """Update user role based on OAuth group membership.

        Args:
            user: User to update
            groups: List of groups from OAuth provider
        """
        if not self.provider.role_mappings:
            return

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
