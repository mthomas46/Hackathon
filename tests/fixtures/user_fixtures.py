"""User Fixtures - Specialized fixtures for user-related testing.

This module provides pytest fixtures for user data including regular users,
admin users, developers, and other user roles for comprehensive testing.
"""

import pytest
from typing import Dict, List, Any
from data.users import get_sample_users


@pytest.fixture
def sample_user() -> Dict[str, Any]:
    """Sample user for testing."""
    users = get_sample_users()
    return users[0] if users else {
        "id": "user_123",
        "username": "john.doe",
        "email": "john.doe@company.com",
        "name": "John Doe",
        "role": "developer",
        "department": "engineering",
        "status": "active"
    }


@pytest.fixture
def sample_users() -> List[Dict[str, Any]]:
    """Multiple sample users."""
    users = get_sample_users()
    return users[:5] if len(users) >= 5 else users


@pytest.fixture
def admin_user() -> Dict[str, Any]:
    """Admin user fixture."""
    return {
        "id": "user_admin",
        "username": "admin.user",
        "email": "admin@company.com",
        "name": "Admin User",
        "role": "admin",
        "department": "engineering",
        "status": "active",
        "permissions": ["read", "write", "admin", "delete"]
    }


@pytest.fixture
def developer_user() -> Dict[str, Any]:
    """Developer user fixture."""
    return {
        "id": "user_dev",
        "username": "dev.user",
        "email": "dev@company.com",
        "name": "Developer User",
        "role": "developer",
        "department": "engineering",
        "status": "active",
        "skills": ["python", "javascript", "react", "django"],
        "experience_years": 3
    }


@pytest.fixture
def manager_user() -> Dict[str, Any]:
    """Manager user fixture."""
    return {
        "id": "user_mgr",
        "username": "manager.user",
        "email": "manager@company.com",
        "name": "Manager User",
        "role": "manager",
        "department": "engineering",
        "status": "active",
        "team_size": 8,
        "budget_authority": 50000
    }


@pytest.fixture
def qa_user() -> Dict[str, Any]:
    """QA/Tester user fixture."""
    return {
        "id": "user_qa",
        "username": "qa.user",
        "email": "qa@company.com",
        "name": "QA User",
        "role": "qa",
        "department": "quality",
        "status": "active",
        "certifications": ["ISTQB", "CSM"],
        "testing_tools": ["selenium", "pytest", "jmeter"]
    }


@pytest.fixture
def inactive_user() -> Dict[str, Any]:
    """Inactive user fixture."""
    return {
        "id": "user_inactive",
        "username": "inactive.user",
        "email": "inactive@company.com",
        "name": "Inactive User",
        "role": "developer",
        "department": "engineering",
        "status": "inactive",
        "deactivation_date": "2024-01-15"
    }


@pytest.fixture
def guest_user() -> Dict[str, Any]:
    """Guest/readonly user fixture."""
    return {
        "id": "user_guest",
        "username": "guest.user",
        "email": "guest@company.com",
        "name": "Guest User",
        "role": "guest",
        "department": "external",
        "status": "active",
        "permissions": ["read"]
    }


@pytest.fixture
def user_with_profile() -> Dict[str, Any]:
    """User with complete profile information."""
    return {
        "id": "user_profile",
        "username": "profile.user",
        "email": "profile@company.com",
        "name": "Profile User",
        "role": "developer",
        "department": "engineering",
        "status": "active",
        "profile": {
            "bio": "Senior software developer with 5+ years experience",
            "location": "San Francisco, CA",
            "timezone": "PST",
            "avatar_url": "https://example.com/avatar.jpg"
        },
        "preferences": {
            "theme": "dark",
            "notifications": True,
            "language": "en"
        }
    }


@pytest.fixture
def users_by_role() -> Dict[str, List[Dict[str, Any]]]:
    """Users organized by role."""
    return {
        "admin": [admin_user()],
        "developer": [developer_user()],
        "manager": [manager_user()],
        "qa": [qa_user()],
        "guest": [guest_user()]
    }


@pytest.fixture
def users_by_department() -> Dict[str, List[Dict[str, Any]]]:
    """Users organized by department."""
    return {
        "engineering": [developer_user(), manager_user()],
        "quality": [qa_user()],
        "external": [guest_user()]
    }


@pytest.fixture
def large_user_set() -> List[Dict[str, Any]]:
    """Large set of users for performance testing."""
    base_users = get_sample_users()
    if len(base_users) >= 20:
        return base_users[:20]

    # Generate additional users if needed
    users = base_users.copy()
    roles = ["developer", "manager", "qa", "admin", "guest"]
    departments = ["engineering", "quality", "product", "design", "external"]

    for i in range(20 - len(base_users)):
        users.append({
            "id": f"user_{1000 + i}",
            "username": f"user{i}",
            "email": f"user{i}@company.com",
            "name": f"User {i}",
            "role": roles[i % len(roles)],
            "department": departments[i % len(departments)],
            "status": "active"
        })

    return users
