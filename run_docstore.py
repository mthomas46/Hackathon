#!/usr/bin/env python3
"""
Doc Store Service Launcher - Run the doc-store service with proper environment setup
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Launch the doc-store service with proper environment."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    docstore_dir = script_dir / 'services' / 'doc-store'

    # Set PYTHONPATH to include the project root
    env = os.environ.copy()
    env['PYTHONPATH'] = str(script_dir)

    # Set default database path if not set
    if 'DOCSTORE_DB' not in env:
        env['DOCSTORE_DB'] = str(docstore_dir / 'db.sqlite3')

    # Default port
    port = os.environ.get('PORT', '5010')

    # Change to doc-store directory and run main.py directly
    os.chdir(str(docstore_dir))

    # Run main.py with uvicorn
    cmd = [
        sys.executable, 'main.py'
    ]

    try:
        print(f"🚀 Starting Doc Store service on port {port}...")
        print(f"   Database: {env['DOCSTORE_DB']}")
        print(f"   Working directory: {docstore_dir}")
        result = subprocess.run(cmd, env=env, cwd=str(docstore_dir))
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nDoc Store service interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error running Doc Store service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
