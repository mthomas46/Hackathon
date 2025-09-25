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


def test_basic_arithmetic_operations_produce_expected_results():
    """Test basic arithmetic operations."""
    assert 2 + 2 == 4
    assert 3 * 3 == 9
    assert 10 - 5 == 5
    assert 20 / 4 == 5


def test_string_operations_handle_case_conversion_and_length():
    """Test string operations."""
    test_string = "Hello World"
    assert test_string.upper() == "HELLO WORLD"
    assert test_string.lower() == "hello world"
    assert len(test_string) == 11


@pytest.mark.asyncio
async def test_async_functions_execute_and_return_correct_values():
    """Test async function execution."""
    async def add_async(a, b):
        return a + b

    result = await add_async(5, 3)
    assert result == 8
