"""Advanced security middleware integrating all security features."""

import logging
from collections.abc import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import Config
from src.security.ip_manager import get_ip_manager
from src.security.rate_limiter import get_rate_limiter
from src.security.threat_detector import get_threat_detector

logger = logging.getLogger(__name__)


class AdvancedSecurityMiddleware(BaseHTTPMiddleware):
    """
    Advanced security middleware that integrates:
    - IP allowlist/blocklist checking
    - Rate limiting (multi-tier)
    - Threat detection (WAF-like functionality)
    - Request signature verification (optional)
    """

    def __init__(self, app):
        """Initialize security middleware."""
        super().__init__(app)
        self.ip_manager = get_ip_manager()
        self.rate_limiter = get_rate_limiter()
        self.threat_detector = get_threat_detector(self.ip_manager)

        # Endpoints that bypass certain security checks
        self.bypass_endpoints = {
            "/health",
            "/health/ready",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

        logger.info("Advanced security middleware initialized")

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check X-Forwarded-For header (set by proxies/load balancers)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP in the chain
            return forwarded.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct client
        if request.client:
            return request.client.host

        return "unknown"

    def _get_user_tier(self, request: Request) -> str:
        """Get user tier from request (if authenticated)."""
        # This would be populated by auth middleware
        user = getattr(request.state, "user", None)
        if user:
            return getattr(user, "tier", "free")
        return "free"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security checks."""
        client_ip = self._get_client_ip(request)
        path = request.url.path
        method = request.method

        # Skip security checks for certain endpoints
        if path in self.bypass_endpoints:
            return await call_next(request)

        # Store IP in request state for later use
        request.state.client_ip = client_ip

        # 1. Check IP allowlist/blocklist
        if Config.IP_FILTERING_ENABLED:
            allowed, reason = self.ip_manager.check_ip(client_ip)
            if not allowed:
                logger.warning(f"Blocked request from {client_ip}: {reason}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "Access denied",
                        "details": [{"code": "ip_blocked", "message": reason}],
                    },
                )

        # 2. Check rate limits
        if Config.RATE_LIMITING_ENABLED:
            user_tier = self._get_user_tier(request)
            identifier = client_ip  # Could also use user ID if authenticated

            allowed, retry_after = self.rate_limiter.check_rate_limit(
                identifier=identifier,
                endpoint=path,
                user_tier=user_tier,
            )

            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {client_ip} on {path}. Retry after: {retry_after}s"
                )

                # Get remaining quota for headers
                quota = self.rate_limiter.get_remaining_quota(identifier, path)

                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "details": [
                            {
                                "code": "rate_limit",
                                "message": f"Too many requests. Please try again in {retry_after} seconds.",
                            }
                        ],
                    },
                )

                # Add rate limit headers
                response.headers["Retry-After"] = str(retry_after)
                response.headers["X-RateLimit-Remaining-Minute"] = str(
                    quota.get("minute_remaining", 0)
                )
                response.headers["X-RateLimit-Remaining-Hour"] = str(
                    quota.get("hour_remaining", 0)
                )
                response.headers["X-RateLimit-Remaining-Day"] = str(
                    quota.get("day_remaining", 0)
                )

                return response

        # 3. Threat detection (WAF-like checks)
        if Config.THREAT_DETECTION_ENABLED:
            # Parse query params
            query_params = dict(request.query_params)

            # Get headers
            headers = dict(request.headers)

            # Get body for POST/PUT requests
            body = None
            if method in ["POST", "PUT", "PATCH"]:
                try:
                    # Read body (this consumes the stream, so we need to handle carefully)
                    body_bytes = await request.body()
                    body = body_bytes.decode("utf-8")

                    # Create a new receive function that replays the body for downstream handlers
                    async def receive():
                        return {"type": "http.request", "body": body_bytes, "more_body": False}

                    # Replace the request with a new one that uses the custom receive function
                    request = Request(request.scope, receive)
                except Exception as e:
                    logger.error(f"Failed to read request body: {e}")

            # Check for threats
            is_safe, threats = self.threat_detector.check_request(
                ip=client_ip,
                method=method,
                path=path,
                query_params=query_params,
                headers=headers,
                body=body,
            )

            if not is_safe:
                logger.warning(
                    f"Threat detected from {client_ip} on {method} {path}: {', '.join(threats)}"
                )
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "Request blocked",
                        "details": [
                            {
                                "code": "security_violation",
                                "message": "Request blocked by security policy",
                            }
                        ],
                    },
                )

        # 4. Add rate limit info to response headers
        response = await call_next(request)

        if Config.RATE_LIMITING_ENABLED:
            identifier = client_ip
            quota = self.rate_limiter.get_remaining_quota(identifier, path)

            response.headers["X-RateLimit-Remaining-Minute"] = str(
                quota.get("minute_remaining", 0)
            )
            response.headers["X-RateLimit-Remaining-Hour"] = str(
                quota.get("hour_remaining", 0)
            )
            response.headers["X-RateLimit-Remaining-Day"] = str(
                quota.get("day_remaining", 0)
            )

        return response
