#!/usr/bin/env python3
"""
Start the SoundHash REST API server.

This script starts the FastAPI application server with uvicorn.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn

from config.settings import Config

if __name__ == "__main__":
    print(f"🚀 Starting {Config.API_TITLE} v{Config.API_VERSION}")
    print(f"📝 API Documentation: http://{Config.API_HOST}:{Config.API_PORT}/docs")
    print(f"🔗 API Base URL: http://{Config.API_HOST}:{Config.API_PORT}")
    print()
    
    uvicorn.run(
        "src.api.main:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True,
        log_level="info",
    )
