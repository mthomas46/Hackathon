#!/usr/bin/env python3
"""Launcher script for Prompt Store service.

Provides easy startup with proper configuration and environment setup.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import configuration utilities
from services.shared.config import get_config_value


def setup_environment():
    """Set up environment variables for the service."""
    # Set default database path if not set
    if 'PROMPT_STORE_DB' not in os.environ:
        os.environ['PROMPT_STORE_DB'] = 'services/prompt_store/prompt_store.db'

    # Set port from config or default
    if 'PROMPT_STORE_PORT' not in os.environ:
        port = get_config_value("port", 5110, section="server", env_key="PROMPT_STORE_PORT")
        os.environ['PROMPT_STORE_PORT'] = str(port)

    # Set other common environment variables
    env_vars = {
        'PYTHONPATH': str(project_root),
        'PROMPT_STORE_ENV': os.environ.get('PROMPT_STORE_ENV', 'development'),
    }

    for key, value in env_vars.items():
        os.environ[key] = value

    return os.environ


def run_service():
    """Run the Prompt Store service."""
    print("🚀 Starting Prompt Store Service...")
    print(f"   📁 Database: {os.environ.get('PROMPT_STORE_DB')}")
    print(f"   🔌 Port: {os.environ.get('PROMPT_STORE_PORT')}")
    print(f"   🌍 Environment: {os.environ.get('PROMPT_STORE_ENV')}")

    # Run as module from project root to avoid relative import issues
    cmd = [
        sys.executable, '-m', 'services.prompt_store.main'
    ]

    try:
        subprocess.run(cmd, cwd=project_root, check=True)
    except KeyboardInterrupt:
        print("\n👋 Prompt Store service stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Service failed with exit code {e.returncode}")
        sys.exit(e.returncode)


def run_with_reload():
    """Run with auto-reload for development."""
    try:
        import uvicorn
    except ImportError:
        print("❌ uvicorn not installed. Install with: pip install uvicorn")
        sys.exit(1)

    print("🔄 Starting Prompt Store Service with auto-reload...")
    print(f"   📁 Database: {os.environ.get('PROMPT_STORE_DB')}")
    print(f"   🔌 Port: {os.environ.get('PROMPT_STORE_PORT')}")

    port = int(os.environ.get('PROMPT_STORE_PORT', 5110))

    uvicorn.run(
        "services.prompt_store.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        reload_dirs=[str(project_root / "services" / "prompt_store")],
        log_level="info"
    )


def show_help():
    """Show help information."""
    help_text = """
Prompt Store Service Launcher

USAGE:
    python run_promptstore.py [OPTIONS]

OPTIONS:
    --reload, -r    Run with auto-reload for development
    --help, -h      Show this help message

ENVIRONMENT VARIABLES:
    PROMPT_STORE_DB         SQLite database path (default: services/prompt_store/prompt_store.db)
    PROMPT_STORE_PORT       Service port (default: 5110)
    PROMPT_STORE_ENV        Environment (default: development)

EXAMPLES:
    # Run in production mode
    python run_promptstore.py

    # Run with auto-reload for development
    python run_promptstore.py --reload

    # Run on custom port
    PROMPT_STORE_PORT=5120 python run_promptstore.py

DATABASE SETUP:
    # Initialize database schema
    python -c "from services.prompt_store.db.schema import init_database; init_database()"

    # Populate with test data
    python scripts/populate_promptstore_test_data.py --seed

API ENDPOINTS:
    Health:     http://localhost:5110/health
    Docs:       http://localhost:5110/docs
    Prompts:    http://localhost:5110/api/v1/prompts
    Analytics:  http://localhost:5110/api/v1/analytics
    A/B Tests:  http://localhost:5110/api/v1/ab-tests
"""
    print(help_text)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Prompt Store Service Launcher")
    parser.add_argument("--reload", "-r", action="store_true", help="Run with auto-reload")
    parser.add_argument("--help", "-h", action="store_true", help="Show help")

    args = parser.parse_args()

    if args.help:
        show_help()
        return

    # Set up environment
    setup_environment()

    # Run service
    if args.reload:
        run_with_reload()
    else:
        run_service()


if __name__ == "__main__":
    main()
