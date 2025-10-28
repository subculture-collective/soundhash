"""Authentication utilities for JWT tokens and password hashing."""

import secrets
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import Config

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=Config.API_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, Config.API_SECRET_KEY, algorithm=Config.API_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=Config.API_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, Config.API_SECRET_KEY, algorithm=Config.API_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict | None:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, Config.API_SECRET_KEY, algorithms=[Config.API_ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_api_key() -> str:
    """Generate a random API key."""
    return f"sk_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return pwd_context.hash(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return pwd_context.verify(plain_key, hashed_key)


def get_api_key_prefix(api_key: str) -> str:
    """Get the prefix of an API key for display."""
    return api_key[:8] if len(api_key) > 8 else api_key
