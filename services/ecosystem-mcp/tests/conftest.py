"""
Pytest configuration and shared fixtures.
"""

import pytest
import asyncio
from pathlib import Path

# Configure asyncio event loop for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_data_dir():
    """Return path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_markdown():
    """Sample markdown content for testing."""
    return """# Test Document

This is a test document for validating the ingestion pipeline.

## Section 1

Content here.

## Section 2

More content.
"""


@pytest.fixture
def sample_python():
    """Sample Python content for testing."""
    return """\"\"\"Sample Python module.\"\"\"

def hello_world():
    \"\"\"Say hello.\"\"\"
    return "Hello, World!"


class SampleClass:
    \"\"\"Sample class.\"\"\"
    
    def __init__(self, name: str):
        self.name = name
    
    def greet(self) -> str:
        \"\"\"Return greeting.\"\"\"
        return f"Hello, {self.name}!"
"""


@pytest.fixture
def sample_yaml():
    """Sample YAML content for testing."""
    return """service: test-service
version: 1.0.0
config:
  port: 8000
  host: localhost
  debug: true
"""


@pytest.fixture
def sample_json():
    """Sample JSON content for testing."""
    return """{
  "name": "test",
  "version": "1.0.0",
  "description": "Test data",
  "features": ["feature1", "feature2"]
}
"""

