#!/usr/bin/env python3
"""Test script for the Simulation Dashboard Service.

This script performs basic tests to verify the dashboard service
is working correctly.
"""

import sys
import asyncio
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_imports():
    """Test that all required modules can be imported."""
    print("🧪 Testing imports...")

    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Streamlit: {e}")
        return False

    try:
        import httpx
        print("✅ HTTPX imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import HTTPX: {e}")
        return False

    try:
        import websockets
        print("✅ WebSockets imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import WebSockets: {e}")
        return False

    try:
        from infrastructure.config.config import get_config
        config = get_config()
        print("✅ Configuration loaded successfully")
        print(f"   Environment: {config.environment}")
        print(f"   Port: {config.port}")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False

    try:
        from services.clients.simulation_client import SimulationClient
        print("✅ Simulation client imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import SimulationClient: {e}")
        return False

    try:
        from services.clients.websocket_client import get_websocket_manager
        print("✅ WebSocket client imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import WebSocket client: {e}")
        return False

    return True

def test_simulation_client():
    """Test the simulation client."""
    print("\n🧪 Testing Simulation Client...")

    try:
        from infrastructure.config.config import get_config
        from services.clients.simulation_client import SimulationClient

        config = get_config()
        client = SimulationClient(config.simulation_service)

        print("✅ Simulation client created successfully")
        print(f"   Base URL: {config.simulation_service.base_url}")

        return True
    except Exception as e:
        print(f"❌ Failed to create simulation client: {e}")
        return False

async def test_simulation_service_connection():
    """Test connection to simulation service."""
    print("\n🧪 Testing Simulation Service Connection...")

    try:
        from infrastructure.config.config import get_config
        from services.clients.simulation_client import SimulationClient

        config = get_config()
        client = SimulationClient(config.simulation_service)

        # Test health check
        result = await client.get_health()
        if result.get('status') == 'healthy':
            print("✅ Simulation service is healthy")
            return True
        else:
            print("⚠️  Simulation service responded but may not be fully healthy")
            return True
    except Exception as e:
        print(f"❌ Failed to connect to simulation service: {e}")
        print("   Note: This is expected if the simulation service is not running")
        return False

def test_pages():
    """Test that page modules can be imported."""
    print("\n🧪 Testing Page Modules...")

    pages = ['overview', 'create', 'monitor', 'reports', 'config', 'analytics']

    for page in pages:
        try:
            module = __import__(f'pages.{page}', fromlist=[page])
            print(f"✅ Page '{page}' imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import page '{page}': {e}")
            return False

    return True

def test_components():
    """Test that component modules can be imported."""
    print("\n🧪 Testing Component Modules...")

    components = ['sidebar', 'header', 'footer']

    for component in components:
        try:
            module = __import__(f'components.{component}', fromlist=[component])
            print(f"✅ Component '{component}' imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import component '{component}': {e}")
            return False

    return True

async def main():
    """Run all tests."""
    print("🎯 Simulation Dashboard Test Suite")
    print("=" * 50)

    results = []

    # Test imports
    results.append(test_imports())

    # Test simulation client
    results.append(test_simulation_client())

    # Test simulation service connection
    results.append(await test_simulation_service_connection())

    # Test pages
    results.append(test_pages())

    # Test components
    results.append(test_components())

    # Summary
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print("🎉 All tests passed!")
        print("✅ Dashboard is ready to run")
        print("\nTo start the dashboard:")
        print("   python run_dashboard.py")
        print("   # or")
        print("   streamlit run app.py")
        return 0
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        print("❌ Some issues were found")
        print("\nTo fix issues:")
        print("   pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
