#!/usr/bin/env python3
"""Data Services Dashboard Runner.

This script runs the Data Services Dashboard, a unified interface for managing
Memory Agent, Prompt Store, and Document Store services.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


def install_dependencies():
    """Install required dependencies."""
    try:
        import subprocess

        requirements = ["streamlit", "httpx", "plotly", "pandas", "pydantic", "pydantic-settings"]

        print("📦 Installing dependencies...")
        for package in requirements:
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--break-system-packages", "--user", package],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print(f"  ✅ {package}")
            except subprocess.CalledProcessError:
                print(f"  ⚠️  {package} (already installed or failed)")

        print("📦 Dependencies ready!")

    except Exception as e:
        print(f"⚠️  Dependency installation failed: {e}")
        print("   You may need to install dependencies manually.")


def main():
    """Run the Data Services Dashboard."""
    print("🚀 Starting Data Services Dashboard...")
    print("=" * 60)

    # Install dependencies
    install_dependencies()

    # Import and run the dashboard
    try:
        from app import main as run_app

        print("🎯 Dashboard starting...")
        run_app()

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all required modules are available.")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
        sys.exit(0)

    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
