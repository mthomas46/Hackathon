"""
Shared fixtures for functional tests.

These fixtures provide access to the test database and real services.
"""

import pytest
import asyncio
from pathlib import Path
from typing import AsyncGenerator, Generator

# Import test database fixtures from main conftest
from tests.conftest import db_session, redis_client

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
async def clean_database(db_session):
    """
    Ensure database is clean before each test.
    
    The db_session fixture already handles rollback,
    but this provides explicit cleanup for functional tests.
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
    """
    # The redis_client fixture handles flush automatically
    yield redis_client
    # Flush happens in redis_client fixture

