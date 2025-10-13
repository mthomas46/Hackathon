"""pytest configuration for dashboard tests."""

import pytest


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require live API)"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (no external dependencies)"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle markers."""
    # Mark tests that don't have explicit markers
    for item in items:
        if "integration" not in item.keywords and "unit" not in item.keywords:
            # Default to unit test if not specified
            item.add_marker(pytest.mark.unit)

