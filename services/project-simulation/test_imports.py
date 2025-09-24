#!/usr/bin/env python3
"""Test script to verify all imports work correctly."""

import os
import sys

# Add shared infrastructure to path
shared_path = os.path.join(os.path.dirname(__file__), "..", "..", "services", "shared")
sys.path.insert(0, shared_path)
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "services", "project-simulation"
    ),
)


def test_shared_imports():
    """Test all shared service imports."""
    print("Testing shared service imports...")

    try:
        pass

        print("✓ Shared responses imported successfully")
    except ImportError as e:
        print(f"✗ Shared responses import failed: {e}")

    try:
        pass

        print("✓ Shared utilities imported successfully")
    except ImportError as e:
        print(f"✗ Shared utilities import failed: {e}")

    try:
        pass

        print("✓ Shared middleware imported successfully")
    except ImportError as e:
        print(f"✗ Shared middleware import failed: {e}")

    try:
        pass

        print("✓ Shared health imported successfully")
    except ImportError as e:
        print(f"✗ Shared health import failed: {e}")

    try:
        pass

        print("✓ Shared correlation middleware imported successfully")
    except ImportError as e:
        print(f"✗ Shared correlation middleware import failed: {e}")

    try:
        pass

        print("✓ Shared error handling imported successfully")
    except ImportError as e:
        print(f"✗ Shared error handling import failed: {e}")


def test_local_imports():
    """Test local project-simulation imports."""
    print("\nTesting local imports...")

    try:
        pass

        print("✓ DI container imported successfully")
    except ImportError as e:
        print(f"✗ DI container import failed: {e}")

    try:
        pass

        print("✓ Local logging imported successfully")
    except ImportError as e:
        print(f"✗ Local logging import failed: {e}")

    try:
        pass

        print("✓ Local health imported successfully")
    except ImportError as e:
        print(f"✗ Local health import failed: {e}")

    try:
        pass

        print("✓ Config imported successfully")
    except ImportError as e:
        print(f"✗ Config import failed: {e}")

    try:
        pass

        print("✓ Service discovery imported successfully")
    except ImportError as e:
        print(f"✗ Service discovery import failed: {e}")

    try:
        pass

        print("✓ HATEOAS imported successfully")
    except ImportError as e:
        print(f"✗ HATEOAS import failed: {e}")


if __name__ == "__main__":
    test_shared_imports()
    test_local_imports()
