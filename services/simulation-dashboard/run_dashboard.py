#!/usr/bin/env python3
"""Run script for the Simulation Dashboard Service.

This script provides an easy way to start the dashboard service
locally for development and testing.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import streamlit
        print("✅ Streamlit is installed")
    except ImportError:
        print("❌ Streamlit is not installed")
        print("Run: pip install streamlit")
        return False

    try:
        import httpx
        print("✅ HTTPX is installed")
    except ImportError:
        print("❌ HTTPX is not installed")
        print("Run: pip install httpx")
        return False

    try:
        import websockets
        print("✅ WebSockets is installed")
    except ImportError:
        print("❌ WebSockets is not installed")
        print("Run: pip install websockets")
        return False

    return True

def check_simulation_service():
    """Check if simulation service is running."""
    try:
        import httpx
        import asyncio

        async def check_service():
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:5075/health", timeout=5.0)
                return response.status_code == 200

        result = asyncio.run(check_service())
        if result:
            print("✅ Simulation service is running on http://localhost:5075")
            return True
        else:
            print("❌ Simulation service is not responding")
            return False
    except Exception:
        print("❌ Cannot connect to simulation service at http://localhost:5075")
        print("   Make sure the simulation service is running first")
        return False

def start_dashboard(port: int = 8501):
    """Start the dashboard service."""
    print("🚀 Starting Simulation Dashboard Service...")
    print(f"📊 Dashboard will be available at: http://localhost:{port}")
    print(f"🎯 Simulation Service: http://localhost:5075")
    print()

    # Set environment variables
    env = os.environ.copy()
    env.update({
        'STREAMLIT_SERVER_PORT': str(port),
        'STREAMLIT_SERVER_ADDRESS': '0.0.0.0',
        'STREAMLIT_BROWSER_GATHER_USAGE_STATS': 'false',
        'STREAMLIT_THEME_BASE': 'light',
    })

    # Start Streamlit
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port', str(port),
        '--server.address', '0.0.0.0',
        '--browser.gatherUsageStats', 'false'
    ]

    try:
        subprocess.run(cmd, cwd=current_dir, env=env)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting dashboard: {e}")
        return False

    return True

def main():
    """Main entry point."""
    print("🎯 Simulation Dashboard Service Launcher")
    print("=" * 50)

    # Check dependencies
    print("\n📦 Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Missing dependencies. Please install them first:")
        print("   pip install -r requirements.txt")
        return 1

    # Check simulation service
    print("\n🔗 Checking simulation service...")
    if not check_simulation_service():
        print("\n⚠️  Simulation service is not running.")
        print("   The dashboard will start but some features may not work.")
        print("   To start the simulation service:")
        print("   cd ../project-simulation && python main.py")
        print()

        response = input("Continue anyway? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            return 0

    # Get port from environment or use default
    port = int(os.environ.get('DASHBOARD_PORT', 8501))

    # Start dashboard
    success = start_dashboard(port)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
