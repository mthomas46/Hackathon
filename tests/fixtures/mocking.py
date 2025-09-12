"""Mocking Fixtures - Specialized fixtures for mocking external dependencies.

This module provides fixtures for mocking HTTP clients, databases, caches,
and other external dependencies for isolated testing.
"""

import pytest
import tempfile
import os
from typing import Dict, List, Any
from unittest.mock import Mock, MagicMock
from pathlib import Path

# HTTP client mocks
@pytest.fixture
def mock_http_client():
    """Mock HTTP client for external API calls."""
    mock = Mock()
    mock.get.return_value.status_code = 200
    mock.get.return_value.json.return_value = {"status": "success"}
    mock.post.return_value.status_code = 201
    mock.post.return_value.json.return_value = {"id": "123", "created": True}
    mock.put.return_value.status_code = 200
    mock.put.return_value.json.return_value = {"updated": True}
    mock.delete.return_value.status_code = 204
    return mock

@pytest.fixture
def mock_http_client_error():
    """Mock HTTP client that returns errors."""
    mock = Mock()
    mock.get.return_value.status_code = 404
    mock.get.return_value.json.return_value = {"error": "Not found"}
    mock.post.return_value.status_code = 400
    mock.post.return_value.json.return_value = {"error": "Bad request"}
    return mock

# Database mocks
@pytest.fixture
def mock_database():
    """Mock database connection."""
    mock = Mock()
    mock.cursor.return_value.fetchall.return_value = []
    mock.cursor.return_value.fetchone.return_value = None
    mock.cursor.return_value.rowcount = 0
    mock.commit.return_value = None
    mock.rollback.return_value = None
    return mock

@pytest.fixture
def mock_database_with_data():
    """Mock database with sample data."""
    mock = Mock()
    mock.cursor.return_value.fetchall.return_value = [
        {"id": 1, "name": "Test User", "email": "test@example.com"},
        {"id": 2, "name": "Another User", "email": "another@example.com"}
    ]
    mock.cursor.return_value.fetchone.return_value = {"id": 1, "name": "Test User"}
    mock.cursor.return_value.rowcount = 2
    return mock

# Cache mocks
@pytest.fixture
def mock_cache():
    """Mock cache system."""
    cache_data = {}

    def get(key):
        return cache_data.get(key)

    def set(key, value, ttl=None):
        cache_data[key] = value
        return True

    def delete(key):
        return cache_data.pop(key, None) is not None

    def clear():
        cache_data.clear()
        return True

    mock = Mock()
    mock.get.side_effect = get
    mock.set.side_effect = set
    mock.delete.side_effect = delete
    mock.clear.side_effect = clear
    return mock

# File system mocks
@pytest.fixture
def mock_file_system():
    """Mock file system operations."""
    mock = Mock()
    mock.exists.return_value = True
    mock.isfile.return_value = True
    mock.isdir.return_value = False
    mock.read_text.return_value = "mock file content"
    mock.write_text.return_value = None
    mock.unlink.return_value = None
    return mock

# Environment variable mocks
@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    original_env = os.environ.copy()

    def set_env(key, value):
        os.environ[key] = value

    def get_env(key, default=None):
        return os.environ.get(key, default)

    def clear_env():
        os.environ.clear()
        os.environ.update(original_env)

    mock = Mock()
    mock.set.side_effect = set_env
    mock.get.side_effect = get_env
    mock.clear.side_effect = clear_env
    return mock

# Temporary directory fixture (enhanced)
@pytest.fixture
def temp_directory():
    """Enhanced temporary directory fixture."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some sample files
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Hello, World!")

        config_file = Path(tmpdir) / "config.json"
        config_file.write_text('{"setting": "value"}')

        yield tmpdir

# Temporary file fixture
@pytest.fixture
def temp_file():
    """Temporary file fixture."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Temporary file content")
        temp_path = f.name

    yield temp_path

    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass

# Timer fixture (enhanced)
@pytest.fixture
def timer():
    """Performance timer fixture."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0

        def reset(self):
            self.start_time = None
            self.end_time = None

    return Timer()

# Mock service fixtures
@pytest.fixture
def mock_external_service():
    """Mock external service."""
    mock = Mock()
    mock.process.return_value = {"result": "success", "data": []}
    mock.health_check.return_value = {"status": "healthy"}
    mock.get_status.return_value = "running"
    return mock

@pytest.fixture
def mock_message_queue():
    """Mock message queue."""
    messages = []

    def send(message):
        messages.append(message)
        return True

    def receive():
        return messages.pop(0) if messages else None

    def clear():
        messages.clear()

    mock = Mock()
    mock.send.side_effect = send
    mock.receive.side_effect = receive
    mock.clear.side_effect = clear
    return mock
