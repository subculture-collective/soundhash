"""Middleware for CORS, logging, and rate limiting."""

import logging
import time
import uuid

from fastapi import Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config.settings import Config

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


def add_cors_middleware(app):
    """Add CORS middleware to the app."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=Config.API_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


async def request_logging_middleware(request: Request, call_next):
    """Log all requests with timing information."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={"request_id": request_id},
    )
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(
        f"Request completed: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - Time: {process_time:.3f}s",
        extra={"request_id": request_id, "status_code": response.status_code},
    )
    
    return response


def add_exception_handlers(app):
    """Add custom exception handlers to the app."""
    
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        """Handle Pydantic validation errors."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "details": exc.errors(),
                "request_id": getattr(request.state, "request_id", None),
            },
        )
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        """Handle rate limit errors."""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "details": [{"code": "rate_limit", "message": str(exc)}],
                "request_id": getattr(request.state, "request_id", None),
            },
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions."""
        logger.error(
            f"Unhandled exception: {str(exc)}",
            exc_info=True,
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "details": [{"code": "internal_error", "message": "An unexpected error occurred"}],
                "request_id": getattr(request.state, "request_id", None),
            },
        )
