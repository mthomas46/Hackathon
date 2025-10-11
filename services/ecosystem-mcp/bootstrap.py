#!/usr/bin/env python3
"""
Bootstrap script for Ecosystem MCP Service.

Performs comprehensive system validation and fixes issues automatically.
Then starts the service with proper error handling.
"""

import sys
import subprocess
from pathlib import Path
import time


def main():
    """Main bootstrap function."""
    service_root = Path(__file__).parent
    
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║                                                           ║")
    print("║           ECOSYSTEM MCP - BOOTSTRAP & START              ║")
    print("║                                                           ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")
    
    # Step 1: Run system validation
    print("Step 1/4: Running system validation...")
    print("─" * 80)
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "src.utils.system_validator"],
            cwd=service_root,
            timeout=300
        )
        
        if result.returncode != 0:
            print("\n❌ System validation failed")
            print("Please fix the issues above and try again")
            return 1
    except Exception as e:
        print(f"\n❌ Validation script failed: {e}")
        return 1
    
    # Step 2: Check Docker services
    print("\n\nStep 2/4: Checking Docker services...")
    print("─" * 80)
    
    try:
        result = subprocess.run(
            ["docker-compose", "ps", "--services", "--filter", "status=running"],
            cwd=service_root,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        running = result.stdout.strip()
        if "postgres" not in running or "redis" not in running:
            print("⚠️  Some Docker services not running")
            print("ℹ️  Starting Docker services...")
            
            subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=service_root,
                check=True,
                timeout=120
            )
            
            print("✅ Docker services started")
            print("⏳ Waiting 10 seconds for services to be ready...")
            time.sleep(10)
        else:
            print("✅ Docker services are running")
    except Exception as e:
        print(f"⚠️  Could not check Docker services: {e}")
        print("ℹ️  Continuing anyway...")
    
    # Step 3: Activate virtual environment and install dependencies
    print("\n\nStep 3/4: Checking Python environment...")
    print("─" * 80)
    
    venv_python = service_root / "venv" / "bin" / "python"
    if not venv_python.exists():
        print("❌ Virtual environment not found")
        print("ℹ️  Please run: python3 -m venv venv")
        return 1
    
    print("✅ Virtual environment ready")
    
    # Step 4: Start the server
    print("\n\nStep 4/4: Starting Ecosystem MCP Server...")
    print("─" * 80)
    
    print("\n🚀 Starting server on http://localhost:8000")
    print("📖 API docs will be at http://localhost:8000/docs")
    print("ℹ️  Press Ctrl+C to stop\n")
    
    try:
        # Start server using venv Python
        subprocess.run(
            [str(venv_python), "-m", "uvicorn", "src.api.app:create_app",
             "--factory", "--host", "0.0.0.0", "--port", "8000",
             "--log-level", "info"],
            cwd=service_root
        )
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped")
        return 0
    except Exception as e:
        print(f"\n\n❌ Server failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

