"""Basic tests to demonstrate test execution capabilities."""

import pytest


def test_basic_assertion():
    """Test basic assertion functionality."""
    assert 1 + 1 == 2
    assert "test".upper() == "TEST"


def test_list_operations():
    """Test list operations."""
    test_list = [1, 2, 3, 4, 5]
    assert len(test_list) == 5
    assert sum(test_list) == 15
    assert max(test_list) == 5


def test_string_operations():
    """Test string operations."""
    test_string = "hello world"
    assert test_string.startswith("hello")
    assert "world" in test_string
    assert len(test_string.split()) == 2


def test_dictionary_operations():
    """Test dictionary operations."""
    test_dict = {"key1": "value1", "key2": "value2"}
    assert test_dict["key1"] == "value1"
    assert "key2" in test_dict
    assert len(test_dict) == 2


@pytest.mark.asyncio
async def test_async_functionality():
    """Test async functionality."""
    async def async_add(x, y):
        return x + y

    result = await async_add(3, 4)
    assert result == 7


def test_exception_handling():
    """Test exception handling."""
    with pytest.raises(ValueError):
        raise ValueError("Test exception")

    with pytest.raises(ZeroDivisionError):
        1 / 0


def test_fixture_usage(sample_document_data):
    """Test fixture usage."""
    assert sample_document_data["id"] == "test-doc-001"
    assert sample_document_data["title"] == "Test Document"
    assert "content" in sample_document_data


def test_mock_usage(mock_document_repository):
    """Test mock usage."""
    mock_document_repository.save.assert_not_called()
    mock_document_repository.find_by_id.assert_not_called()


class TestAnalysisService:
    """Test class for analysis service testing patterns."""

    def test_class_based_test(self):
        """Test class-based test structure."""
        assert True

    def test_another_class_method(self, sample_analysis_data):
        """Test another class method with fixture."""
        assert sample_analysis_data["id"] == "test-analysis-001"
        assert sample_analysis_data["status"] == "completed"


@pytest.mark.parametrize("input_value,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_parametrized(input_value, expected):
    """Test parametrized testing."""
    assert input_value * 2 == expected


@pytest.mark.parametrize("test_input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("pytest", "PYTEST"),
])
def test_string_upper_parametrized(test_input, expected):
    """Test parametrized string operations."""
    assert test_input.upper() == expected
