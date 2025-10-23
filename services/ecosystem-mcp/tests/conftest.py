"""
Pytest configuration and fixtures for all tests.

Provides database setup, async support, and common fixtures.
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path
from typing import AsyncGenerator

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

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


@pytest.fixture(scope="function")
async def db_session(test_database_url: str) -> AsyncGenerator:
    """
    Provide a database session for tests.
    
    Automatically rolls back after each test to ensure isolation.
    """
    try:
        from src.storage.database import init_database, close_database, get_database
        
        # Initialize database
        await init_database()
        
        # Get session
        async with get_database() as session:
            yield session
            
            # Rollback after test
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
def clean_database(test_database_url: str):
    """
    Clean all tables in the test database.
    
    Use this fixture for tests that need a completely clean slate.
    """
    import subprocess
    
    # Truncate all tables
    subprocess.run([
        "docker", "exec", "-i", "ecosystem-mcp-postgres-test",
        "psql", "-U", "test_user", "-d", "ecosystem_mcp_test",
        "-c", """
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END $$;
        """
    ], check=False)


@pytest.fixture(scope="session")
def check_test_database():
    """
    Check that test database is running before running tests.
    
    Fails fast if database is not available.
    """
    import subprocess
    
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=ecosystem-mcp-postgres-test", "--filter", "health=healthy"],
        capture_output=True,
        text=True
    )
    
    if "ecosystem-mcp-postgres-test" not in result.stdout:
        pytest.fail(
            "\n❌ Test database is not running!\n"
            "   Start it with: ./scripts/test-db.sh start\n"
            "   Or run: docker-compose -f docker-compose.test.yml up -d\n"
        )
    
    print("✅ Test database is running")
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
    
    # Check if database is running
    import subprocess
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=ecosystem-mcp-postgres-test"],
        capture_output=True,
        text=True
    )
    
    if "ecosystem-mcp-postgres-test" not in result.stdout:
        skip_db = pytest.mark.skip(reason="Test database not running (use ./scripts/test-db.sh start)")
        for item in items:
            if "integration" in item.keywords or "e2e" in item.keywords:
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
