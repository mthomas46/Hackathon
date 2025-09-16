#!/usr/bin/env python3
"""
Doc Store Service Launcher - Run the doc_store service with proper environment setup
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Launch the doc_store service with proper environment."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    docstore_dir = script_dir / 'services' / 'doc_store'

    # Set PYTHONPATH to include the project root
    env = os.environ.copy()
    env['PYTHONPATH'] = str(script_dir)

    # Set default database path if not set
    if 'DOCSTORE_DB' not in env:
        env['DOCSTORE_DB'] = 'db.sqlite3'  # Relative to service directory

    # Default port
    port = os.environ.get('PORT', '5010')

    # Set DOCSTORE_PORT environment variable
    if 'DOCSTORE_PORT' not in env:
        env['DOCSTORE_PORT'] = port

    # Run as module from project root to avoid relative import issues
    cmd = [
        sys.executable, '-m', 'services.doc_store.main'
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
