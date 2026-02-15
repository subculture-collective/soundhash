"""LDAP/Active Directory authentication provider implementation."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.database.sso_models import SSOProvider, SSOAuditLog
from src.database.models import User

logger = logging.getLogger(__name__)

# Try to import LDAP library
try:
    import ldap
    from ldap.filter import escape_filter_chars

    LDAP_AVAILABLE = True
except ImportError:
    LDAP_AVAILABLE = False
    logger.warning(
        "python-ldap not available. LDAP authentication will not work. "
        "Install with: pip install python-ldap (requires system dependencies)"
    )


class LDAPProvider:
    """LDAP/Active Directory authentication provider."""

    def __init__(self, provider_config: SSOProvider, db: Session):
        """Initialize LDAP provider with configuration.

        Args:
            provider_config: SSO provider configuration from database
            db: Database session
        """
        if not LDAP_AVAILABLE:
            raise RuntimeError(
                "LDAP support not available. Install python-ldap library and dependencies."
            )

        self.provider = provider_config
        self.db = db

        # Validate required LDAP configuration
        if not all(
            [
                provider_config.ldap_server_url,
                provider_config.ldap_bind_dn,
                provider_config.ldap_bind_password,
                provider_config.ldap_base_dn,
            ]
        ):
            raise ValueError("LDAP provider missing required configuration")

    def authenticate(
        self,
        username: str,
        password: str,
        ip_address: str,
        user_agent: str,
    ) -> Optional[User]:
        """Authenticate user against LDAP directory.

        Args:
            username: Username to authenticate
            password: User's password
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Authenticated User object or None if authentication failed
        """
        try:
            # Connect to LDAP server
            conn = ldap.initialize(self.provider.ldap_server_url)

            # Set LDAP protocol version
            conn.protocol_version = ldap.VERSION3

            # Set LDAP options for security
            if self.provider.ldap_server_url.startswith("ldaps://"):
                conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

            # Bind with service account
            try:
                conn.simple_bind_s(
                    self.provider.ldap_bind_dn,
                    self.provider.ldap_bind_password,
                )
            except ldap.INVALID_CREDENTIALS:
                logger.error("LDAP bind failed: Invalid service account credentials")
                return None

            # Search for user
            search_filter = self.provider.ldap_user_search_filter or "(uid={username})"
            search_filter = search_filter.format(username=escape_filter_chars(username))

            result = conn.search_s(
                self.provider.ldap_base_dn,
                ldap.SCOPE_SUBTREE,
                search_filter,
                [
                    self.provider.ldap_user_email_attribute or "mail",
                    self.provider.ldap_user_name_attribute or "cn",
                    "memberOf",  # For group membership
                ],
            )

            if not result:
                logger.warning(f"User not found in LDAP: {username}")
                self._log_auth_event(
                    event_type="login",
                    event_status="failure",
                    event_message=f"User not found: {username}",
                    username_attempted=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                return None

            # Get user DN and attributes
            user_dn, user_attrs = result[0]

            # Try to bind as the user to verify password
            try:
                user_conn = ldap.initialize(self.provider.ldap_server_url)
                user_conn.protocol_version = ldap.VERSION3
                if self.provider.ldap_server_url.startswith("ldaps://"):
                    user_conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
                user_conn.simple_bind_s(user_dn, password)
                user_conn.unbind_s()
            except ldap.INVALID_CREDENTIALS:
                logger.warning(f"Invalid password for LDAP user: {username}")
                self._log_auth_event(
                    event_type="login",
                    event_status="failure",
                    event_message="Invalid password",
                    username_attempted=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                return None

            # Extract user data
            email_attr = self.provider.ldap_user_email_attribute or "mail"
            name_attr = self.provider.ldap_user_name_attribute or "cn"

            email = self._get_ldap_attr(user_attrs, email_attr)
            full_name = self._get_ldap_attr(user_attrs, name_attr)
            groups = self._get_ldap_attr_list(user_attrs, "memberOf")

            if not email:
                logger.error(f"No email found for LDAP user: {username}")
                self._log_auth_event(
                    event_type="login",
                    event_status="error",
                    event_message="No email attribute found in LDAP",
                    username_attempted=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                return None

            user_data = {
                "email": email,
                "full_name": full_name or username,
                "username": username,
            }

            # Find or create user (JIT provisioning)
            user = self._find_or_create_user(user_data)

            if user:
                # Update role based on LDAP groups if role mapping is enabled
                if self.provider.enable_role_mapping and groups:
                    self._update_user_role(user, groups)

                self._log_auth_event(
                    event_type="login",
                    event_status="success",
                    event_message=f"LDAP authentication successful for {username}",
                    user_id=user.id,
                    username_attempted=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )

                return user

            # Unbind
            conn.unbind_s()

        except ldap.SERVER_DOWN:
            logger.error("LDAP server is down or unreachable")
            self._log_auth_event(
                event_type="login",
                event_status="error",
                event_message="LDAP server unavailable",
                username_attempted=username,
                ip_address=ip_address,
                user_agent=user_agent,
                error_details="Server down or unreachable",
            )
        except Exception as e:
            logger.error(f"LDAP authentication error: {str(e)}", exc_info=True)
            self._log_auth_event(
                event_type="login",
                event_status="error",
                event_message=f"LDAP authentication error: {str(e)}",
                username_attempted=username,
                ip_address=ip_address,
                user_agent=user_agent,
                error_details=str(e),
            )

        return None

    def search_users(
        self,
        search_query: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search for users in LDAP directory.

        Args:
            search_query: Search query (username or email)
            limit: Maximum number of results

        Returns:
            List of user dictionaries
        """
        if not LDAP_AVAILABLE:
            return []

        try:
            conn = ldap.initialize(self.provider.ldap_server_url)
            conn.protocol_version = ldap.VERSION3

            # Bind with service account
            conn.simple_bind_s(
                self.provider.ldap_bind_dn,
                self.provider.ldap_bind_password,
            )

            # Search for users matching query
            email_attr = self.provider.ldap_user_email_attribute or "mail"
            name_attr = self.provider.ldap_user_name_attribute or "cn"

            search_filter = f"(|({email_attr}=*{escape_filter_chars(search_query)}*)"
            search_filter += f"({name_attr}=*{escape_filter_chars(search_query)}*))"

            results = conn.search_s(
                self.provider.ldap_base_dn,
                ldap.SCOPE_SUBTREE,
                search_filter,
                [email_attr, name_attr],
            )

            users = []
            for user_dn, user_attrs in results[:limit]:
                users.append(
                    {
                        "email": self._get_ldap_attr(user_attrs, email_attr),
                        "full_name": self._get_ldap_attr(user_attrs, name_attr),
                        "dn": user_dn,
                    }
                )

            conn.unbind_s()
            return users

        except Exception as e:
            logger.error(f"LDAP search error: {str(e)}", exc_info=True)
            return []

    def get_user_groups(self, username: str) -> List[str]:
        """Get groups for a user.

        Args:
            username: Username to look up

        Returns:
            List of group DNs
        """
        if not LDAP_AVAILABLE:
            return []

        try:
            conn = ldap.initialize(self.provider.ldap_server_url)
            conn.protocol_version = ldap.VERSION3

            # Bind with service account
            conn.simple_bind_s(
                self.provider.ldap_bind_dn,
                self.provider.ldap_bind_password,
            )

            # Search for user
            search_filter = self.provider.ldap_user_search_filter or "(uid={username})"
            search_filter = search_filter.format(username=escape_filter_chars(username))

            result = conn.search_s(
                self.provider.ldap_base_dn,
                ldap.SCOPE_SUBTREE,
                search_filter,
                ["memberOf"],
            )

            if result:
                _, user_attrs = result[0]
                groups = self._get_ldap_attr_list(user_attrs, "memberOf")
                conn.unbind_s()
                return groups

            conn.unbind_s()

        except Exception as e:
            logger.error(f"LDAP group lookup error: {str(e)}", exc_info=True)

        return []

    def _get_ldap_attr(self, attrs: Dict[str, List[bytes]], attr_name: str) -> str:
        """Get a single LDAP attribute value.

        Args:
            attrs: LDAP attributes dictionary
            attr_name: Attribute name

        Returns:
            Attribute value as string
        """
        if attr_name in attrs and attrs[attr_name]:
            return attrs[attr_name][0].decode("utf-8")
        return ""

    def _get_ldap_attr_list(self, attrs: Dict[str, List[bytes]], attr_name: str) -> List[str]:
        """Get LDAP attribute as list of values.

        Args:
            attrs: LDAP attributes dictionary
            attr_name: Attribute name

        Returns:
            List of attribute values
        """
        if attr_name in attrs:
            return [val.decode("utf-8") for val in attrs[attr_name]]
        return []

    def _find_or_create_user(self, user_data: Dict[str, str]) -> Optional[User]:
        """Find existing user or create new user (JIT provisioning).

        Args:
            user_data: User data from LDAP

        Returns:
            User object or None
        """
        email = user_data.get("email")
        if not email:
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
            username = user_data.get("username", email.split("@")[0])

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
                hashed_password="",  # LDAP users don't have local passwords
                tenant_id=self.provider.tenant_id,
                role=self.provider.default_role or "member",
                is_active=True,
                is_verified=True,  # LDAP users are pre-verified
            )

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            logger.info(f"Created new user via LDAP JIT provisioning: {email}")
            return user

        return None

    def _update_user_role(self, user: User, groups: List[str]) -> None:
        """Update user role based on LDAP group membership.

        Args:
            user: User to update
            groups: List of group DNs from LDAP
        """
        if not self.provider.role_mappings:
            return

        # Extract group names from DNs
        group_names = []
        for group_dn in groups:
            # Extract CN from DN (e.g., "CN=Admins,OU=Groups,DC=company,DC=com" -> "Admins")
            parts = group_dn.split(",")
            for part in parts:
                if part.startswith("CN="):
                    group_names.append(part[3:])
                    break

        # Check role mappings
        for group_name in group_names:
            if group_name in self.provider.role_mappings:
                new_role = self.provider.role_mappings[group_name]
                if new_role != user.role:
                    logger.info(
                        f"Updating user {user.email} role from {user.role} to {new_role} "
                        f"based on LDAP group {group_name}"
                    )
                    user.role = new_role
                    self.db.commit()
                    break

    def _log_auth_event(
        self,
        event_type: str,
        event_status: str,
        event_message: str,
        user_id: Optional[int] = None,
        username_attempted: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_details: Optional[str] = None,
    ) -> None:
        """Log authentication event to audit log.

        Args:
            event_type: Type of event
            event_status: Status of event
            event_message: Human-readable message
            user_id: User ID if available
            username_attempted: Username attempted
            ip_address: Client IP address
            user_agent: Client user agent
            error_details: Error details if applicable
        """
        audit_log = SSOAuditLog(
            tenant_id=self.provider.tenant_id,
            user_id=user_id,
            provider_id=self.provider.id,
            event_type=event_type,
            event_status=event_status,
            event_message=event_message,
            username_attempted=username_attempted,
            ip_address=ip_address,
            user_agent=user_agent,
            error_details=error_details,
        )

        self.db.add(audit_log)
        self.db.commit()
