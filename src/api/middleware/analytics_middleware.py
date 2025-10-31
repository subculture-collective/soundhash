"""Middleware for tracking API usage analytics."""

import logging
import time
from datetime import UTC, datetime

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from src.database.connection import db_manager
from src.database.models import APIUsageLog

logger = logging.getLogger(__name__)


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Middleware to track API usage for analytics."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Track API request and response metrics."""
        # Skip tracking for certain paths
        skip_paths = ["/health", "/health/ready", "/docs", "/redoc", "/openapi.json"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # Capture request start time
        start_time = time.time()
        
        # Get request metadata
        user_id = None
        tenant_id = None
        api_key_id = None
        
        # Try to get user info from request state (set by auth middleware)
        if hasattr(request.state, "user"):
            user = request.state.user
            user_id = user.id if user else None
            tenant_id = user.tenant_id if user else None
        
        if hasattr(request.state, "api_key"):
            api_key = request.state.api_key
            api_key_id = api_key.id if api_key else None
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Get response size
        response_size_bytes = 0
        if hasattr(response, "body"):
            response_size_bytes = len(response.body)
        
        # Extract path params and query params
        path_params = dict(request.path_params) if hasattr(request, "path_params") else {}
        query_params = dict(request.query_params)
        
        # Log API usage
        # TODO: Consider using async database operations or background task queue
        # to avoid blocking the request-response cycle
        try:
            session = db_manager.get_session()
            
            api_log = APIUsageLog(
                tenant_id=tenant_id,
                user_id=user_id,
                api_key_id=api_key_id,
                endpoint=request.url.path,
                method=request.method,
                path_params=path_params if path_params else None,
                query_params=query_params if query_params else None,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                response_size_bytes=response_size_bytes,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                timestamp=datetime.now(UTC),
            )
            
            session.add(api_log)
            session.commit()
            session.close()
        except Exception as e:
            # Don't let analytics errors break the API
            logger.error(f"Failed to log API usage: {e}")
        
        return response
