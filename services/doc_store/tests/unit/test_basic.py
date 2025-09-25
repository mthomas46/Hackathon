"""Basic tests to verify test framework is working."""

import pytest


def test_basic_assertion():
    """Test basic assertion to verify pytest is working."""
    assert 1 + 1 == 2


def test_string_operations():
    """Test basic string operations."""
    text = "hello world"
    assert "hello" in text
    assert text.upper() == "HELLO WORLD"
    assert len(text) == 11


@pytest.mark.asyncio
async def test_async_function():
    """Test async function support."""
    result = await async_add(1, 2)
    assert result == 3


async def async_add(a: int, b: int) -> int:
    """Simple async addition function."""
    return a + b


def test_fixture_usage(test_config):
    """Test using fixtures from conftest.py."""
    assert isinstance(test_config, dict)
    assert "database_url" in test_config
    assert "service_name" in test_config


def test_performance_metrics_fixture(performance_metrics):
    """Test performance metrics fixture."""
    # Test recording metrics
    performance_metrics.record("test_metric", 42)
    assert performance_metrics.get("test_metric") == 42
