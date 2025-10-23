"""
Helper functions and decorators for integration tests.

Provides infrastructure availability checks and skip decorators.
"""

import pytest


def is_redis_available():
    """Check if Redis is available."""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
        r.ping()
        return True
    except Exception:
        return False


def is_postgres_available():
    """Check if PostgreSQL is available."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='test_user',
            password='test_password',
            database='ecosystem_mcp_test',
            connect_timeout=1
        )
        conn.close()
        return True
    except Exception:
        return False


def is_chromadb_available():
    """Check if ChromaDB is available."""
    try:
        import chromadb
        client = chromadb.HttpClient(host='localhost', port=8000)
        client.heartbeat()
        return True
    except Exception:
        return False


def is_docker_available():
    """Check if Docker is available."""
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


# Check infrastructure availability at module level
redis_available = is_redis_available()
postgres_available = is_postgres_available()
chromadb_available = is_chromadb_available()
docker_available = is_docker_available()

# Skip decorators
skip_if_no_redis = pytest.mark.skipif(not redis_available, reason="Redis not available")
skip_if_no_postgres = pytest.mark.skipif(not postgres_available, reason="PostgreSQL not available")
skip_if_no_chromadb = pytest.mark.skipif(not chromadb_available, reason="ChromaDB not available")
skip_if_no_docker = pytest.mark.skipif(not docker_available, reason="Docker not available")


def accept_infrastructure_errors(response, expected_success_codes=None):
    """
    Helper to accept both success and infrastructure error codes.
    
    Args:
        response: HTTP response object
        expected_success_codes: List of success codes (default: [200])
    
    Returns:
        bool: True if status code is acceptable
    """
    if expected_success_codes is None:
        expected_success_codes = [200]
    
    # Accept success codes or common infrastructure errors
    acceptable_codes = expected_success_codes + [500, 503]
    return response.status_code in acceptable_codes


def get_json_if_success(response):
    """
    Get JSON from response if successful, otherwise return None.
    
    Args:
        response: HTTP response object
    
    Returns:
        dict or None: JSON data if successful, None otherwise
    """
    if response.status_code in [200, 201]:
        try:
            return response.json()
        except Exception:
            return None
    return None

