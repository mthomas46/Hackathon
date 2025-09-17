"""Integration test configuration for Prompt Store service.

Provides fixtures for testing the full service stack.
"""

import pytest
import asyncio
import os
import tempfile
import sqlite3
from pathlib import Path
from typing import Generator
from fastapi.testclient import TestClient
from unittest.mock import patch

# Import the service app and database setup
from services.prompt_store.main import app
from services.prompt_store.db.schema import init_database


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def temp_db_path():
    """Create a temporary database path for integration testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name

    # Set environment variable for the test session
    original_db = os.environ.get("PROMPT_STORE_DB")
    os.environ["PROMPT_STORE_DB"] = temp_path

    yield temp_path

    # Cleanup
    if original_db:
        os.environ["PROMPT_STORE_DB"] = original_db
    else:
        os.environ.pop("PROMPT_STORE_DB", None)

    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture(scope="session")
def prompt_store_db(temp_db_path):
    """Initialize the prompt_store database for integration testing."""
    # Initialize database schema
    init_database()

    yield temp_db_path


@pytest.fixture(autouse=True)
def clean_integration_db(prompt_store_db):
    """Clean up database between integration tests."""
    from services.prompt_store.db.connection import get_prompt_store_connection

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
        except Exception:
            pass  # Table might not exist or be empty

    conn.commit()
    conn.close()


@pytest.fixture
def prompt_store_service(prompt_store_db, clean_integration_db) -> Generator[TestClient, None, None]:
    """Provide a test client for the Prompt Store service.

    This fixture sets up the full FastAPI application with all routes
    and middleware for integration testing.
    """
    # Create test client
    client = TestClient(app)

    yield client


@pytest.fixture
def mock_llm_service():
    """Mock the LLM service for integration tests."""
    with patch('services.prompt_store.domain.refinement.service.ServiceClients') as mock_clients:
        mock_instance = mock_clients.return_value
        mock_instance.call_interpreter.return_value = {
            "refined_content": "This is a refined version of the prompt with improvements."
        }
        mock_instance.call_bedrock.return_value = {
            "refined_content": "AWS Bedrock refined version of the prompt."
        }
        yield mock_instance


@pytest.fixture
def mock_doc_store():
    """Mock the document store service for integration tests."""
    with patch('services.prompt_store.domain.refinement.service.DocumentService') as mock_doc:
        mock_instance = mock_doc.return_value
        mock_instance.create_entity.return_value = type('MockDoc', (), {
            'id': 'mock_doc_123',
            'content': 'Mock stored refinement result'
        })()
        yield mock_instance


@pytest.fixture
def sample_integration_data():
    """Provide comprehensive sample data for integration tests."""
    return {
        "prompts": [
            {
                "name": "integration_base_prompt",
                "category": "integration",
                "content": "Base prompt for integration testing",
                "variables": ["input"],
                "is_template": True
            },
            {
                "name": "integration_variant_a",
                "category": "integration",
                "content": "Variant A of integration prompt"
            },
            {
                "name": "integration_variant_b",
                "category": "integration",
                "content": "Variant B of integration prompt"
            }
        ],
        "webhook": {
            "name": "integration_test_webhook",
            "url": "https://httpbin.org/post",
            "events": ["prompt.created", "prompt.updated", "prompt.lifecycle_changed"],
            "secret": "integration_secret",
            "is_active": True
        },
        "ab_test": {
            "name": "integration_ab_test",
            "description": "A/B test for integration testing",
            "traffic_percentage": 50
        },
        "bulk_operation": {
            "operation_type": "update_prompts",
            "total_items": 5,
            "metadata": {"test_batch": "integration"}
        }
    }
