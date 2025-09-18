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
os.environ.setdefault('PYTHONPATH', f"{app_root}")
os.environ.setdefault('SERVICE_NAME', 'frontend')
os.environ.setdefault('SERVICE_PORT', '3000')

# Setup Python path for proper module resolution
sys.path.insert(0, app_root)
sys.path.insert(0, str(service_dir))

print(f"Frontend Service Startup:")
print(f"- App root: {app_root}")
print(f"- Service dir: {service_dir}")
print(f"- Working dir: {os.getcwd()}")
print(f"- Python path: {sys.path[:3]}...")

# Import uvicorn first
import uvicorn

# Now try to import and run
try:
    # Import the FastAPI app from main
    from main import app
    
    if __name__ == "__main__":
        port = int(os.environ.get('SERVICE_PORT', 3000))
        print(f"Starting frontend service on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)

except ImportError as e:
    print(f"Import error in frontend service: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    sys.exit(1)
except Exception as e:
    print(f"Error starting frontend service: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
