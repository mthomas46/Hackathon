"""Test configuration and fixtures for prompt_store domain tests.

Provides shared fixtures and configuration for domain-driven testing.
"""

import os
import pytest
import tempfile
import sqlite3
from pathlib import Path

from services.prompt_store.db.schema import init_database
from services.prompt_store.db.connection import get_prompt_store_connection


@pytest.fixture(scope="function")
def temp_db_path():
    """Create a temporary database path for each test to ensure isolation."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name

    # Set environment variable for this test
    original_db = os.environ.get("PROMPT_STORE_DB")
    os.environ["PROMPT_STORE_DB"] = temp_path

    yield temp_path

    # Cleanup
    if original_db:
        os.environ["PROMPT_STORE_DB"] = original_db
    else:
        os.environ.pop("PROMPT_STORE_DB", None)

    # Remove temp file
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture(scope="function")
def prompt_store_db(temp_db_path):
    """Initialize the prompt_store database for each test."""
    # Drop existing tables to ensure clean schema
    conn = get_prompt_store_connection()
    cursor = conn.cursor()

    # Drop tables if they exist (for clean schema updates)
    tables_to_drop = [
        'cost_optimization_metrics', 'prompt_evolution_metrics', 'prompt_optimization_suggestions',
        'user_satisfaction_scores', 'prompt_performance_metrics', 'prompt_testing_results',
        'bias_detection_results', 'notifications', 'webhook_deliveries', 'webhooks',
        'bulk_operations', 'prompt_relationships', 'prompt_usage', 'ab_test_results',
        'ab_tests', 'prompt_versions', 'prompts', 'prompts_fts'
    ]

    for table in tables_to_drop:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        except Exception:
            pass  # Table might not exist

    conn.commit()
    conn.close()

    # Initialize database schema
    init_database()

    # Verify database is working
    conn = get_prompt_store_connection()
    cursor = conn.cursor()

    # Check that tables were created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    expected_tables = [
        'prompts', 'prompt_versions', 'ab_tests', 'ab_test_results',
        'prompt_usage', 'prompt_relationships', 'bulk_operations',
        'webhooks', 'webhook_deliveries', 'notifications'
    ]

    for table in expected_tables:
        assert table in tables, f"Table {table} was not created"

    conn.close()

    yield temp_db_path


@pytest.fixture
def clean_db(prompt_store_db):
    """Ensure clean database state for each test."""
    conn = get_prompt_store_connection()
    cursor = conn.cursor()

    # Clear all data from tables
    tables_to_clear = [
        'notifications', 'webhook_deliveries', 'webhooks',
        'bulk_operations', 'prompt_relationships', 'prompt_usage',
        'ab_test_results', 'ab_tests', 'prompt_versions', 'prompts'
    ]

    for table in tables_to_clear:
        try:
            cursor.execute(f"DELETE FROM {table}")
        except sqlite3.Error:
            pass  # Table might not exist or be empty

    conn.commit()
    conn.close()

    yield


@pytest.fixture
def sample_prompt_data():
    """Provide sample prompt data for testing."""
    return {
        "name": "sample_prompt",
        "category": "test",
        "description": "A sample prompt for testing",
        "content": "This is a sample prompt with {{variable}} placeholders.",
        "variables": ["variable"],
        "tags": ["sample", "test"],
        "is_template": True,
        "created_by": "test_user"
    }


@pytest.fixture
def sample_webhook_data():
    """Provide sample webhook data for testing."""
    return {
        "name": "test_webhook",
        "url": "https://httpbin.org/post",
        "events": ["prompt.created", "prompt.updated"],
        "secret": "test_webhook_secret",
        "is_active": True,
        "retry_count": 3,
        "timeout_seconds": 30,
        "created_by": "test_user"
    }


@pytest.fixture
def sample_ab_test_data():
    """Provide sample A/B test data for testing."""
    return {
        "name": "sample_ab_test",
        "description": "A/B test for prompt performance",
        "prompt_a_id": "prompt_a_123",
        "prompt_b_id": "prompt_b_456",
        "traffic_percentage": 50,
        "status": "active",
        "created_by": "test_user"
    }


# Test configuration
def pytest_configure(config):
    """Configure pytest for prompt_store domain testing."""
    # Add custom markers
    config.addinivalue_line("markers", "prompt_store: tests for prompt store domain")
    config.addinivalue_line("markers", "integration: tests that verify cross-domain workflows")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Add prompt_store marker to all tests in this directory
        item.add_marker(pytest.mark.prompt_store)
