"""Authentication Fixtures - Specialized fixtures for authentication testing.

This module provides fixtures for JWT tokens, user authentication,
and security-related test data.
"""

import pytest
from typing import Dict, List, Any
from data.users import get_authentication_tokens

# Authentication token fixtures
@pytest.fixture
def auth_tokens():
    """JWT authentication tokens for different user roles."""
    return get_authentication_tokens()

@pytest.fixture
def valid_admin_token(auth_tokens):
    """Valid admin user token."""
    return auth_tokens.get("valid_admin", "admin_token_placeholder")

@pytest.fixture
def valid_developer_token(auth_tokens):
    """Valid developer user token."""
    return auth_tokens.get("valid_developer", "dev_token_placeholder")

@pytest.fixture
def expired_token(auth_tokens):
    """Expired JWT token."""
    return auth_tokens.get("expired", "expired_token_placeholder")

@pytest.fixture
def invalid_token(auth_tokens):
    """Invalid JWT token."""
    return auth_tokens.get("invalid", "invalid_token_placeholder")

@pytest.fixture
def malformed_token(auth_tokens):
    """Malformed JWT token."""
    return auth_tokens.get("malformed", "malformed_token_placeholder")

# User authentication fixtures
@pytest.fixture
def authenticated_user():
    """Authenticated user context."""
    return {
        "user_id": "user_123",
        "username": "john.doe",
        "email": "john.doe@company.com",
        "role": "developer",
        "permissions": ["read", "write"],
        "authenticated": True,
        "session_id": "session_abc123"
    }

@pytest.fixture
def unauthenticated_user():
    """Unauthenticated user context."""
    return {
        "user_id": None,
        "username": None,
        "email": None,
        "role": None,
        "permissions": [],
        "authenticated": False,
        "session_id": None
    }

@pytest.fixture
def admin_user():
    """Admin user context."""
    return {
        "user_id": "user_admin",
        "username": "admin.user",
        "email": "admin@company.com",
        "role": "admin",
        "permissions": ["read", "write", "admin", "delete"],
        "authenticated": True,
        "session_id": "session_admin_123"
    }

@pytest.fixture
def readonly_user():
    """Read-only user context."""
    return {
        "user_id": "user_readonly",
        "username": "readonly.user",
        "email": "readonly@company.com",
        "role": "viewer",
        "permissions": ["read"],
        "authenticated": True,
        "session_id": "session_readonly_123"
    }

# Security test data fixtures
@pytest.fixture
def security_test_data():
    """Security testing data."""
    return {
        "sql_injection_payloads": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; SELECT * FROM users; --"
        ],
        "xss_payloads": [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')"
        ],
        "path_traversal_payloads": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd"
        ],
        "command_injection_payloads": [
            "; rm -rf /",
            "| cat /etc/passwd",
            "`whoami`"
        ]
    }

@pytest.fixture
def rate_limit_data():
    """Rate limiting test data."""
    return {
        "normal_requests": 100,
        "burst_requests": 1000,
        "time_window_seconds": 60,
        "rate_limit_threshold": 100,
        "burst_threshold": 200
    }
