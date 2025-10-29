"""Main FastAPI application."""

import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from config.logging_config import setup_logging
from config.settings import Config
from src.api.middleware import (
    add_cors_middleware,
    add_exception_handlers,
    limiter,
    request_logging_middleware,
)
from src.database.connection import db_manager

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=Config.API_TITLE,
    description=Config.API_DESCRIPTION,
    version=Config.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add middleware
add_cors_middleware(app)
app.middleware("http")(request_logging_middleware)
app.state.limiter = limiter
add_exception_handlers(app)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting SoundHash API...")
    db_manager.initialize()
    logger.info("Database connection initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down SoundHash API...")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": Config.API_TITLE,
        "version": Config.API_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from sqlalchemy import text
    
    try:
        # Check database connection
        session = db_manager.get_session()
        session.execute(text("SELECT 1"))
        session.close()
        db_healthy = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_healthy = False
    
    if db_healthy:
        return {"status": "healthy", "database": "connected"}
    else:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected"},
        )


# Import and include routers
from src.api.routes import admin, auth, channels, email, fingerprints, matches, monitoring, videos

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(videos.router, prefix="/api/v1/videos", tags=["Videos"])
app.include_router(matches.router, prefix="/api/v1/matches", tags=["Matches"])
app.include_router(channels.router, prefix="/api/v1/channels", tags=["Channels"])
app.include_router(fingerprints.router, prefix="/api/v1/fingerprints", tags=["Fingerprints"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])
app.include_router(email.router, prefix="/api/v1", tags=["Email"])


# WebSocket endpoint for real-time audio streaming
from fastapi import WebSocket, WebSocketDisconnect
from src.api.websocket import manager
from src.core.streaming_processor import cleanup_processor, process_audio_chunk


@app.websocket("/ws/stream/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time audio streaming.
    
    Clients connect with a unique client_id and stream audio data.
    The server processes the audio in real-time and sends back match results.
    """
    await manager.connect(websocket, client_id)
    await manager.send_status(client_id, "Connected to SoundHash streaming service")
    
    try:
        while True:
            # Receive audio chunk
            data = await websocket.receive_bytes()
            
            # Process audio chunk
            await process_audio_chunk(client_id, data)
            
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
        manager.disconnect(client_id)
        cleanup_processor(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)
        cleanup_processor(client_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True,
        log_config=None,  # Use our custom logging
    )
