"""Basic tests to verify test framework is working."""

import pytest


def test_arithmetic_operations_produce_expected_results():
    """Test that basic arithmetic operations produce expected results."""
    assert 1 + 1 == 2


def test_string_operations_handle_case_conversion_and_length():
    """Test that string operations correctly handle case conversion and length calculation."""
    text = "hello world"
    assert "hello" in text
    assert text.upper() == "HELLO WORLD"
    assert len(text) == 11


@pytest.mark.asyncio
async def test_async_functions_execute_and_return_correct_values():
    """Test that async functions execute properly and return correct values."""
    result = await async_add(1, 2)
    assert result == 3


async def async_add(a: int, b: int) -> int:
    """Simple async addition function."""
    return a + b


def test_test_config_fixture_provides_required_configuration():
    """Test that the test_config fixture provides all required configuration values."""
    assert isinstance(test_config, dict)
    assert "database_url" in test_config
    assert "service_name" in test_config


def test_performance_metrics_fixture_records_and_retrieves_values():
    """Test that the performance metrics fixture correctly records and retrieves metric values."""
    # Test recording metrics
    performance_metrics.record("test_metric", 42)
    assert performance_metrics.get("test_metric") == 42
