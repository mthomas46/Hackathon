"""
Pytest configuration and fixtures for all tests.

Provides database setup, async support, and common fixtures.
"""

import os
import sys
import pytest
import asyncio
import logging
from pathlib import Path
from typing import AsyncGenerator

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Set up logger
logger = logging.getLogger(__name__)

# Load test environment
from dotenv import load_dotenv
env_test_path = Path(__file__).parent.parent / ".env.test"
if env_test_path.exists():
    load_dotenv(env_test_path, override=True)
    print(f"✅ Loaded test environment from {env_test_path}")


# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (require database)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (full workflow)"
    )
    config.addinivalue_line(
        "markers", "smoke: Smoke tests (basic functionality)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (skip by default)"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_database_url() -> str:
    """Provide test database URL."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://test_user:test_password@localhost:5433/ecosystem_mcp_test"
    )


@pytest.fixture(scope="session")
async def test_redis_url() -> str:
    """Provide test Redis URL."""
    return os.getenv("REDIS_URL", "redis://localhost:6380/0")


# Global flag to track if tables have been created
_tables_created = False


@pytest.fixture(scope="function")
async def db_session(test_database_url: str) -> AsyncGenerator:
    """
    Provide a database session for tests.
    
    Automatically rolls back after each test to ensure isolation.
    Creates tables on first run.
    """
    global _tables_created
    from src.storage.database import init_database, close_database, get_database
    
    try:
        # Initialize database
        await init_database()
        
        # Create tables once
        if not _tables_created:
            db = get_database()
            await db.create_tables()
            _tables_created = True
            logger.info("✅ Test database tables created")
        
        # Get database instance and create session
        db = get_database()
        async with db.session() as session:
            try:
                yield session
            finally:
                # Rollback after test to ensure isolation
                await session.rollback()
    finally:
        await close_database()


@pytest.fixture(scope="function")
async def redis_client(test_redis_url: str):
    """Provide a Redis client for tests."""
    try:
        from src.utils.redis_client import get_redis_client, init_redis, close_redis
        
        await init_redis()
        client = get_redis_client()
        
        yield client
        
        # Clean up
        await client.flushdb()
    finally:
        await close_redis()


@pytest.fixture(scope="function")
async def clean_database(db_session):
    """
    Provide a clean database session for functional tests.
    
    Returns the db_session which automatically rolls back after each test.
    This ensures test isolation without needing to truncate tables.
    """
    # Simply return the db_session which handles rollback automatically
    return db_session


@pytest.fixture(scope="session")
def check_test_database():
    """
    Check that test database is running before running tests.
    
    Fails fast if database is not available.
    """
    import subprocess
    
    # Check if PostgreSQL is accessible (works with local or Docker)
    result = subprocess.run(
        ["pg_isready", "-h", "localhost", "-p", "5432"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        pytest.fail(
            "\n❌ PostgreSQL database is not running!\n"
            "   Start local PostgreSQL: brew services start postgresql@14\n"
            "   Or use Docker: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16\n"
        )
    
    print("✅ PostgreSQL database is running")
    return True


# Skip integration tests if database is not available
def pytest_collection_modifyitems(config, items):
    """Skip integration tests if test database is not running."""
    if config.getoption("--no-integration"):
        skip_integration = pytest.mark.skip(reason="--no-integration flag used")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
        return
    
    # Check if PostgreSQL is running (works with local or Docker)
    import subprocess
    result = subprocess.run(
        ["pg_isready", "-h", "localhost", "-p", "5432"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        skip_db = pytest.mark.skip(reason="PostgreSQL not running (start with: brew services start postgresql@14)")
        for item in items:
            if "integration" in item.keywords or "e2e" in item.keywords or "functional" in item.keywords:
                item.add_marker(skip_db)


def pytest_addoption(parser):
    """Add custom command-line options."""
    parser.addoption(
        "--no-integration",
        action="store_true",
        default=False,
        help="Skip integration tests"
    )
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests"
    )
