"""FastAPI dependencies for authentication and database."""

from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.api.auth import decode_token, verify_api_key
from src.database.connection import db_manager
from src.database.models import APIKey, User

# Security schemes
security = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_db() -> Session:
    """Get database session dependency."""
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


async def get_current_user_from_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> User | None:
    """Get current user from JWT token (optional)."""
    if credentials is None:
        return None

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        return None

    username: str = payload.get("sub")
    token_type: str = payload.get("type")

    if username is None or token_type != "access":
        return None

    user = db.query(User).filter(User.username == username).first()

    return user


async def get_current_user_from_api_key(
    api_key: Annotated[str | None, Security(api_key_header)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    """Get current user from API key (optional)."""
    if api_key is None:
        return None

    # Query all active API keys and verify
    api_keys = db.query(APIKey).filter(APIKey.is_active == True).all()

    for key_record in api_keys:
        if verify_api_key(api_key, key_record.key_hash):
            # Update last used timestamp
            from datetime import datetime, timezone
            key_record.last_used_at = datetime.now(timezone.utc)
            db.commit()

            # Get and return the user
            user = db.query(User).filter(User.id == key_record.user_id).first()
            if user:
                return user

    return None


async def get_current_user(
    user_from_token: Annotated[User | None, Depends(get_current_user_from_token)] = None,
    user_from_api_key: Annotated[User | None, Depends(get_current_user_from_api_key)] = None,
) -> User:
    """Get current user from either JWT token or API key."""
    user = user_from_token or user_from_api_key

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return current_user


async def get_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current admin user."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
