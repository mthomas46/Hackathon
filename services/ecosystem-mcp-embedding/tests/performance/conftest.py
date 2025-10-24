"""
Pytest configuration for performance tests.
These tests use HTTP clients and don't require app imports.
"""

import pytest


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )

