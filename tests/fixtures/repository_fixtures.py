"""Repository Fixtures - Specialized fixtures for repository-related testing.

This module provides pytest fixtures for repository data including Git repositories,
CI/CD configurations, and repository metadata for comprehensive testing.
"""

import pytest
from typing import Dict, List, Any
from data.repositories import get_sample_repositories


@pytest.fixture
def sample_repository() -> Dict[str, Any]:
    """Sample repository for testing."""
    repos = get_sample_repositories()
    return repos[0] if repos else {
        "id": "repo_123",
        "name": "sample-repo",
        "full_name": "company/sample-repo",
        "description": "Sample repository for testing",
        "owner": {
            "login": "company",
            "type": "Organization"
        },
        "private": False,
        "html_url": "https://github.com/company/sample-repo",
        "language": "Python",
        "forks_count": 5,
        "stargazers_count": 25,
        "watchers_count": 25,
        "size": 1024,
        "default_branch": "main",
        "created_at": "2023-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
    }


@pytest.fixture
def sample_repositories() -> List[Dict[str, Any]]:
    """Multiple sample repositories."""
    repos = get_sample_repositories()
    return repos[:3] if len(repos) >= 3 else repos


@pytest.fixture
def python_repository() -> Dict[str, Any]:
    """Python repository fixture."""
    return {
        "id": "repo_python",
        "name": "python-api",
        "full_name": "company/python-api",
        "description": "REST API built with Python and FastAPI",
        "language": "Python",
        "topics": ["api", "python", "fastapi", "rest"],
        "size": 2048,
        "forks_count": 12,
        "stargazers_count": 45,
        "open_issues_count": 3,
        "license": {"name": "MIT"},
        "has_issues": True,
        "has_projects": True,
        "has_wiki": True,
        "has_pages": False,
        "has_downloads": True
    }


@pytest.fixture
def javascript_repository() -> Dict[str, Any]:
    """JavaScript/TypeScript repository fixture."""
    return {
        "id": "repo_js",
        "name": "frontend-app",
        "full_name": "company/frontend-app",
        "description": "Modern React application with TypeScript",
        "language": "TypeScript",
        "topics": ["react", "typescript", "frontend", "spa"],
        "size": 5120,
        "forks_count": 8,
        "stargazers_count": 67,
        "open_issues_count": 7,
        "license": {"name": "MIT"},
        "has_issues": True,
        "has_projects": False,
        "has_wiki": False,
        "has_pages": True,
        "has_downloads": False
    }


@pytest.fixture
def private_repository() -> Dict[str, Any]:
    """Private repository fixture."""
    return {
        "id": "repo_private",
        "name": "internal-tools",
        "full_name": "company/internal-tools",
        "description": "Internal development tools and scripts",
        "private": True,
        "language": "Python",
        "size": 256,
        "forks_count": 0,
        "stargazers_count": 0,
        "watchers_count": 5,
        "permissions": {
            "admin": False,
            "push": True,
            "pull": True
        }
    }


@pytest.fixture
def repository_with_ci() -> Dict[str, Any]:
    """Repository with CI/CD configuration."""
    return {
        "id": "repo_ci",
        "name": "ci-enabled-repo",
        "full_name": "company/ci-enabled-repo",
        "description": "Repository with comprehensive CI/CD setup",
        "language": "Python",
        "ci_config": {
            "github_actions": True,
            "workflows": ["ci.yml", "deploy.yml"],
            "branches": ["main", "develop"],
            "python_versions": ["3.8", "3.9", "3.10"],
            "os": ["ubuntu-latest", "windows-latest"]
        },
        "branches": [
            {"name": "main", "protected": True},
            {"name": "develop", "protected": False},
            {"name": "feature/auth", "protected": False}
        ],
        "environments": ["staging", "production"]
    }


@pytest.fixture
def repository_with_issues() -> Dict[str, Any]:
    """Repository with issue tracking data."""
    return {
        "id": "repo_issues",
        "name": "issue-tracker",
        "full_name": "company/issue-tracker",
        "description": "Repository with active issue tracking",
        "open_issues_count": 15,
        "closed_issues_count": 89,
        "issues": [
            {
                "number": 1,
                "title": "Implement user authentication",
                "state": "open",
                "labels": ["enhancement", "high-priority"],
                "assignees": ["dev1", "dev2"]
            },
            {
                "number": 2,
                "title": "Fix database connection timeout",
                "state": "closed",
                "labels": ["bug", "database"],
                "assignees": ["dev3"]
            }
        ]
    }


@pytest.fixture
def repository_with_contributors() -> Dict[str, Any]:
    """Repository with contributor information."""
    return {
        "id": "repo_contrib",
        "name": "contributor-repo",
        "full_name": "company/contributor-repo",
        "description": "Repository with diverse contributor base",
        "contributors": [
            {
                "login": "lead-dev",
                "contributions": 150,
                "type": "User",
                "role": "Maintainer"
            },
            {
                "login": "dev1",
                "contributions": 89,
                "type": "User",
                "role": "Developer"
            },
            {
                "login": "dev2",
                "contributions": 67,
                "type": "User",
                "role": "Developer"
            }
        ],
        "contributors_count": 8,
        "commit_activity": [
            {"week": "2024-01-01", "commits": 12},
            {"week": "2024-01-08", "commits": 8},
            {"week": "2024-01-15", "commits": 15}
        ]
    }


@pytest.fixture
def repository_with_releases() -> Dict[str, Any]:
    """Repository with release information."""
    return {
        "id": "repo_releases",
        "name": "release-repo",
        "full_name": "company/release-repo",
        "description": "Repository with regular releases",
        "releases": [
            {
                "tag_name": "v2.1.0",
                "name": "Version 2.1.0",
                "body": "New features and bug fixes",
                "published_at": "2024-01-15T10:00:00Z",
                "author": {"login": "release-manager"}
            },
            {
                "tag_name": "v2.0.0",
                "name": "Version 2.0.0",
                "body": "Major release with breaking changes",
                "published_at": "2024-01-01T10:00:00Z",
                "author": {"login": "release-manager"}
            }
        ],
        "latest_release": "v2.1.0",
        "release_frequency": "monthly"
    }


@pytest.fixture
def repository_with_dependencies() -> Dict[str, Any]:
    """Repository with dependency information."""
    return {
        "id": "repo_deps",
        "name": "dependency-repo",
        "full_name": "company/dependency-repo",
        "description": "Repository with complex dependency structure",
        "language": "Python",
        "dependencies": {
            "runtime": ["requests==2.28.0", "fastapi==0.95.0", "sqlalchemy==2.0.0"],
            "development": ["pytest==7.2.0", "black==23.1.0", "mypy==1.0.0"],
            "optional": ["pandas==1.5.0", "numpy==1.24.0"]
        },
        "vulnerabilities": [
            {
                "package": "requests",
                "version": "2.28.0",
                "severity": "medium",
                "description": "Potential security issue"
            }
        ],
        "dependency_graph": {
            "nodes": ["app", "requests", "fastapi", "sqlalchemy"],
            "edges": [
                {"from": "app", "to": "requests"},
                {"from": "app", "to": "fastapi"},
                {"from": "app", "to": "sqlalchemy"}
            ]
        }
    }


@pytest.fixture
def repositories_by_language() -> Dict[str, List[Dict[str, Any]]]:
    """Repositories organized by programming language."""
    return {
        "python": [python_repository()],
        "javascript": [javascript_repository()],
        "mixed": [sample_repository()]
    }


@pytest.fixture
def repositories_by_visibility() -> Dict[str, List[Dict[str, Any]]]:
    """Repositories organized by visibility."""
    return {
        "public": [sample_repository(), python_repository(), javascript_repository()],
        "private": [private_repository()]
    }
