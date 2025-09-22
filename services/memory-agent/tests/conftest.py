"""Pytest configuration for Memory Agent tests."""

import pytest
from fastapi.testclient import TestClient

from services.memory_agent.main import app


@pytest.fixture
def client():
    """Create test client for memory agent."""
    return TestClient(app)


@pytest.fixture
def sample_memory_item():
    """Create a sample memory item for testing."""
    return {
        "key": "test-sample-key",
        "type": "test_type",
        "content": {
            "message": "Sample test content",
            "metadata": {"source": "test", "version": "1.0"}
        },
        "ttl": 3600
    }


@pytest.fixture
def multiple_memory_items():
    """Create multiple sample memory items for testing."""
    return [
        {
            "key": "test-item-1",
            "type": "workflow",
            "content": {"step": "start", "workflow_id": "wf-123"},
            "ttl": 3600
        },
        {
            "key": "test-item-2",
            "type": "workflow",
            "content": {"step": "process", "workflow_id": "wf-123"},
            "ttl": 3600
        },
        {
            "key": "test-item-3",
            "type": "event",
            "content": {"event": "completed", "workflow_id": "wf-456"},
            "ttl": 1800
        }
    ]
