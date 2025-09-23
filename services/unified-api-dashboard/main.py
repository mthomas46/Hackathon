#!/usr/bin/env python3
"""
Unified API Dashboard - Main Entry Point

This is the main entry point for the Unified API Dashboard service.
It imports and runs the FastAPI application.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the application
from app import app

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("SERVICE_PORT", "8000"))
    host = os.getenv("SERVICE_HOST", "127.0.0.1")

    print("🚀 Starting Unified API Dashboard...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"📚 Docs: http://{host}:{port}/docs")
    print(f"🏥 Health: http://{host}:{port}/health")

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
