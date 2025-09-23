#!/usr/bin/env python3
"""
Quick startup script for testing the new LLM Documentation Ecosystem services.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import requests


def print_banner():
    """Print startup banner."""
    print("=" * 80)
    print("🚀 LLM Documentation Ecosystem - Service Startup")
    print("=" * 80)
    print()


def check_python_version():
    """Check Python version compatibility."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]}")


def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")

    # Check if virtual environment is active
    if not hasattr(sys, "real_prefix") and not (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: No virtual environment detected")

    try:
        # Install requirements
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "services/requirements.base.txt"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Install additional packages
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "rich", "click", "requests"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        print("✅ Dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)


def start_service(service_name, port, module_path):
    """Start a service in background."""
    print(f"🔄 Starting {service_name} on port {port}...")

    try:
        process = subprocess.Popen([sys.executable, module_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Wait a moment for service to start
        time.sleep(2)

        # Check if process is still running
        if process.poll() is None:
            print(f"✅ {service_name} started (PID: {process.pid})")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ {service_name} failed to start")
            print(f"Error: {stderr.decode()}")
            return None

    except Exception as e:
        print(f"❌ Failed to start {service_name}: {e}")
        return None


def check_service_health(url, service_name):
    """Check if service is healthy."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return True
        else:
            print(f"⚠️  {service_name} returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        return False


def test_services():
    """Test all services are working."""
    print("\n🩺 Testing services...")

    services = [
        ("http://localhost:5110/health", "Prompt Store"),
        ("http://localhost:5120/health", "Interpreter"),
    ]

    all_healthy = True

    for url, name in services:
        if check_service_health(url, name):
            print(f"✅ {name} is healthy")
        else:
            print(f"❌ {name} is not responding")
            all_healthy = False

    return all_healthy


def test_basic_functionality():
    """Test basic functionality of services."""
    print("\n🧪 Testing basic functionality...")

    try:
        # Test prompt store migration
        print("🔄 Testing prompt migration...")
        response = requests.post("http://localhost:5110/migrate", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Migrated {data.get('migrated', 0)} prompts")
        else:
            print(f"⚠️  Migration returned status {response.status_code}")

        # Test interpreter
        print("🔄 Testing interpreter...")
        response = requests.post("http://localhost:5120/interpret", json={"query": "analyze this document"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            intent = data.get("intent", "unknown")
            confidence = data.get("confidence", 0)
            print(f"✅ Interpreter working - Intent: {intent} ({confidence:.2f})")
        else:
            print(f"⚠️  Interpreter returned status {response.status_code}")

        # Test prompt retrieval
        print("🔄 Testing prompt retrieval...")
        response = requests.get("http://localhost:5110/prompts/search/summarization/default?content=test", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "prompt" in data:
                prompt_length = len(data["prompt"])
                print(f"✅ Prompt retrieval working - Generated {prompt_length} chars")
            else:
                print("⚠️  Prompt retrieval returned unexpected format")
        else:
            print(f"⚠️  Prompt retrieval returned status {response.status_code}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during testing: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False


def main():
    """Main startup function."""
    print_banner()

    # Check prerequisites
    check_python_version()

    # Install dependencies
    install_dependencies()

    print("\n🏁 Starting services...")

    # Start services
    processes = []

    # Start Prompt Store
    prompt_store = start_service("Prompt Store", 5110, "services/prompt-store/main.py")
    if prompt_store:
        processes.append(("Prompt Store", prompt_store))

    # Start Interpreter
    interpreter = start_service("Interpreter", 5120, "services/interpreter/main.py")
    if interpreter:
        processes.append(("Interpreter", interpreter))

    # Wait for services to fully start
    print("\n⏳ Waiting for services to initialize...")
    time.sleep(5)

    # Test services
    if test_services():
        print("\n🎉 All services started successfully!")

        # Test basic functionality
        if test_basic_functionality():
            print("\n🎯 All tests passed! Services are ready to use.")
        else:
            print("\n⚠️  Some functionality tests failed, but services are running.")
    else:
        print("\n❌ Some services failed to start properly.")
        return 1

    print("\n📋 Service URLs:")
    print("   Prompt Store: http://localhost:5110")
    print("   Interpreter:  http://localhost:5120")
    print("   CLI:          python services/cli/main.py interactive")

    print("\n💡 Quick test commands:")
    print("   curl http://localhost:5110/health")
    print("   curl http://localhost:5120/health")
    print("   python services/cli/main.py health")

    print("\n🔄 Services are running in background...")
    print("Press Ctrl+C to stop all services")

    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)

            # Check if any process died
            for name, process in processes:
                if process.poll() is not None:
                    print(f"\n❌ {name} process terminated unexpectedly")
                    return 1

    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")

        # Terminate all processes
        for name, process in processes:
            print(f"🔄 Stopping {name}...")
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"⚠️  {name} did not stop gracefully, killing...")
                process.kill()

        print("\n👋 All services stopped. Goodbye!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
