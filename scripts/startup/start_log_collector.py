#!/usr/bin/env python3
"""
Startup script for Log Collector service
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def main():
    """Start Log Collector service."""
    print("🚀 Starting Log Collector Service...")

    # Get project root
    project_root = Path(__file__).parent.parent

    # Change to project directory
    os.chdir(project_root)

    # Set PYTHONPATH
    pythonpath = str(project_root)
    env = os.environ.copy()
    env['PYTHONPATH'] = pythonpath

    # Start service
    try:
        cmd = [
            sys.executable,
            "-m", "services.log_collector.main"
        ]

        print(f"🔄 Command: {' '.join(cmd)}")
        print(f"📁 Working directory: {os.getcwd()}")
        print(f"🐍 PYTHONPATH: {pythonpath}")

        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        print(f"✅ Log Collector started (PID: {process.pid}) on http://localhost:5080")

        # Wait a moment for startup
        time.sleep(3)

        # Check if still running
        if process.poll() is None:
            print("🩺 Service appears healthy")
            print("📋 Endpoints:")
            print("   Health: http://localhost:5080/health")
            print("   Docs:   http://localhost:5080/docs")
            print("")
            print("Press Ctrl+C to stop...")

            try:
                while True:
                    time.sleep(1)
                    if process.poll() is not None:
                        print("❌ Service terminated unexpectedly")
                        return 1
            except KeyboardInterrupt:
                print("\n🛑 Stopping Log Collector...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                    print("✅ Log Collector stopped")
                except subprocess.TimeoutExpired:
                    print("⚠️  Force killing...")
                    process.kill()
                return 0
        else:
            stdout, _ = process.communicate()
            print("❌ Service failed to start:")
            print(stdout)
            return 1

    except Exception as e:
        print(f"❌ Error starting Log Collector: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
