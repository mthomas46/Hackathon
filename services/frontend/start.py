#!/usr/bin/env python3
"""
Frontend Service Startup Script
Handles the frontend service startup with proper import resolution
"""

import os
import sys
from pathlib import Path

# Set up the Python path for frontend imports
app_root = "/app"
service_dir = Path(__file__).parent

# Set environment variables
os.environ.setdefault("PYTHONPATH", f"{app_root}")
os.environ.setdefault("SERVICE_NAME", "frontend")
os.environ.setdefault("SERVICE_PORT", "3000")

# Setup Python path for proper module resolution
sys.path.insert(0, app_root)
sys.path.insert(0, str(service_dir))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Frontend Service Startup:")
logger.info(f"- App root: {app_root}")
logger.info(f"- Service dir: {service_dir}")
logger.info(f"- Working dir: {os.getcwd()}")
logger.info(f"- Python path: {sys.path[:3]}...")

# Import uvicorn first
import uvicorn

# Now try to import and run
try:
    # Import the FastAPI app from main
    from main import app

    if __name__ == "__main__":
        host = os.environ.get("FRONTEND_SERVICE_HOST", "127.0.0.1")
        port = int(os.environ.get("SERVICE_PORT", 3000))
        logger.info(f"Starting frontend service on {host}:{port}")
        uvicorn.run(app, host=host, port=port)

except ImportError as e:
    logger.error(f"Import error in frontend service: {e}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Error starting frontend service: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
