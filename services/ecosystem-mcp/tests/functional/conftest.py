"""
Shared fixtures for functional tests.

These fixtures provide access to the test database and real services.
All test data is automatically marked for isolation safety.
"""

import pytest
import asyncio
from pathlib import Path
from typing import AsyncGenerator, Generator
import uuid

# Import test database fixtures from main conftest
from tests.conftest import db_session, redis_client

# Import test data helpers
from tests.utils.test_helpers import (
    create_test_document,
    create_test_timeline,
    create_test_commit,
    verify_test_data_marked
)
from src.utils.test_data_marker import TestDataMarker, create_test_session_id


# Add service-level fixtures for functional tests
@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Return the path to test data directory."""
    return Path(__file__).parent.parent.parent  # services/ecosystem-mcp/


@pytest.fixture(scope="session")
def ecosystem_mcp_src_dir(test_data_dir) -> Path:
    """Return the path to ecosystem-mcp source directory for ingestion."""
    src_dir = test_data_dir / "src"
    assert src_dir.exists(), f"Source directory not found: {src_dir}"
    return src_dir


@pytest.fixture
def test_session_id() -> str:
    """
    Generate a unique test session ID.
    
    This ID is used to mark all test data created in a test,
    enabling tracking and cleanup.
    """
    return create_test_session_id()


@pytest.fixture
async def clean_database(db_session):
    """
    Ensure database is clean before each test.
    
    The db_session fixture already handles rollback,
    but this provides explicit cleanup for functional tests.
    
    All data created through this fixture is automatically
    rolled back after the test completes.
    """
    # The db_session fixture handles rollback automatically
    yield db_session
    # Rollback happens in db_session fixture


@pytest.fixture
async def clean_redis(redis_client):
    """
    Ensure Redis is clean before each test.
    
    The redis_client fixture already handles flush,
    but this provides explicit cleanup for functional tests.
    
    All cached data is automatically flushed after the test completes.
    """
    # The redis_client fixture handles flush automatically
    yield redis_client
    # Flush happens in redis_client fixture

