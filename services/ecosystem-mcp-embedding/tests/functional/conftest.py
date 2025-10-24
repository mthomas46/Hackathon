"""
Pytest configuration for functional tests.
These tests use HTTP clients and don't require app imports.
"""

import pytest


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "functional: marks tests as functional tests"
    )

