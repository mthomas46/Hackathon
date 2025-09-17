#!/usr/bin/env python3
"""
CLI Launcher - Run the CLI service with proper environment setup
"""

import os
import sys
import subprocess

def main():
    """Launch the CLI service with proper environment."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cli_dir = os.path.join(script_dir, 'services', 'cli')

    # Set PYTHONPATH to include the project root
    env = os.environ.copy()
    env['PYTHONPATH'] = script_dir

    # Configure for local testing mode
    env['DOC_STORE_URL'] = 'local'
    env['DOCSTORE_DB'] = os.path.join(script_dir, 'services', 'doc_store', 'db.sqlite3')

    # Change to CLI directory
    os.chdir(cli_dir)

    # Run the CLI with the provided arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else ['interactive']
    cmd = [sys.executable, 'main.py'] + args

    try:
        result = subprocess.run(cmd, env=env, cwd=cli_dir)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nCLI interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error running CLI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
