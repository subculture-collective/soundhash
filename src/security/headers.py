"""Security headers middleware for production-grade security."""

import logging
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import Config

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.

    Implements:
    - Content Security Policy (CSP)
    - HTTP Strict Transport Security (HSTS)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Content Security Policy
        if Config.CSP_ENABLED:
            response.headers["Content-Security-Policy"] = Config.CSP_POLICY

        # HTTP Strict Transport Security
        if Config.HSTS_ENABLED:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={Config.HSTS_MAX_AGE}; includeSubDomains; preload"
            )

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = Config.X_FRAME_OPTIONS

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS Protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        response.headers["Referrer-Policy"] = Config.REFERRER_POLICY

        # Permissions Policy (Feature Policy replacement)
        response.headers["Permissions-Policy"] = Config.PERMISSIONS_POLICY

        # CORS headers are already handled by CORSMiddleware

        return response
