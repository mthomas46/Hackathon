#!/usr/bin/env python3
"""
Analysis Service Startup Script
Handles the complex DDD structure and import requirements
"""
import os
import sys
from pathlib import Path

# Set up the Python path for both internal and external imports
app_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(app_root))
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables
os.environ.setdefault('PYTHONPATH', f"{app_root}:{Path(__file__).parent}")
os.environ.setdefault('SERVICE_NAME', 'analysis-service')
os.environ.setdefault('SERVICE_PORT', '5020')

# Import uvicorn first
import uvicorn

# Change to service directory for relative imports
service_dir = Path(__file__).parent
os.chdir(service_dir)

# Add service directory to Python path for relative imports
sys.path.insert(0, str(service_dir))

# Now try to import and run
try:
    # Import the FastAPI app from main_new
    from main_new import app
    
    if __name__ == "__main__":
        port = int(os.environ.get('SERVICE_PORT', 5020))
        print(f"Starting analysis service on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
        
except ImportError as e:
    print(f"Import error in analysis service: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    sys.exit(1)
except Exception as e:
    print(f"Error starting analysis service: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
