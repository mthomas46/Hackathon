"""Workflow Fixtures - Specialized fixtures for workflow-related testing.

This module provides pytest fixtures for workflow data including CI/CD pipelines,
business processes, and workflow configurations for comprehensive testing.
"""

import pytest
from typing import Dict, List, Any
from data.workflows import get_sample_workflows


@pytest.fixture
def sample_workflow() -> Dict[str, Any]:
    """Sample workflow for testing."""
    workflows = get_sample_workflows()
    return workflows[0] if workflows else {
        "id": "workflow_123",
        "name": "CI Pipeline",
        "description": "Continuous integration pipeline",
        "type": "ci_cd",
        "status": "active",
        "trigger": "push",
        "steps": [
            {"name": "checkout", "action": "checkout@v3"},
            {"name": "setup-python", "action": "setup-python@v4", "with": {"python-version": "3.9"}},
            {"name": "install-deps", "run": "pip install -r requirements.txt"},
            {"name": "run-tests", "run": "pytest"}
        ],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-15T00:00:00Z"
    }


@pytest.fixture
def sample_workflows() -> List[Dict[str, Any]]:
    """Multiple sample workflows."""
    workflows = get_sample_workflows()
    return workflows[:3] if len(workflows) >= 3 else workflows


@pytest.fixture
def ci_workflow() -> Dict[str, Any]:
    """CI/CD workflow fixture."""
    return {
        "id": "workflow_ci",
        "name": "CI Pipeline",
        "description": "Automated testing and building pipeline",
        "type": "ci_cd",
        "status": "active",
        "trigger": {"push": {"branches": ["main", "develop"]}, "pull_request": {}},
        "jobs": {
            "test": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"name": "Checkout", "uses": "actions/checkout@v3"},
                    {"name": "Setup Python", "uses": "actions/setup-python@v4",
                     "with": {"python-version": "3.9"}},
                    {"name": "Install dependencies", "run": "pip install -r requirements.txt"},
                    {"name": "Run tests", "run": "pytest --cov=app --cov-report=xml"},
                    {"name": "Upload coverage", "uses": "codecov/codecov-action@v3"}
                ]
            },
            "lint": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"name": "Checkout", "uses": "actions/checkout@v3"},
                    {"name": "Setup Python", "uses": "actions/setup-python@v4",
                     "with": {"python-version": "3.9"}},
                    {"name": "Install linting tools", "run": "pip install black flake8 mypy"},
                    {"name": "Run linter", "run": "flake8 app/"},
                    {"name": "Run formatter", "run": "black --check app/"},
                    {"name": "Run type checker", "run": "mypy app/"}
                ]
            }
        },
        "permissions": {"contents": "read", "pull-requests": "write"}
    }


@pytest.fixture
def deployment_workflow() -> Dict[str, Any]:
    """Deployment workflow fixture."""
    return {
        "id": "workflow_deploy",
        "name": "Deploy to Production",
        "description": "Automated deployment to production environment",
        "type": "deployment",
        "status": "active",
        "trigger": {"release": {"types": ["published"]}},
        "environment": "production",
        "jobs": {
            "deploy": {
                "runs-on": "ubuntu-latest",
                "environment": "production",
                "steps": [
                    {"name": "Checkout", "uses": "actions/checkout@v3"},
                    {"name": "Configure AWS", "uses": "aws-actions/configure-aws-credentials@v2",
                     "with": {"aws-region": "us-east-1"}},
                    {"name": "Login to ECR", "run": "aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY"},
                    {"name": "Build and push", "run": "docker build -t app . && docker push app:latest"},
                    {"name": "Deploy to ECS", "run": "aws ecs update-service --cluster prod --service app --force-new-deployment"}
                ]
            }
        }
    }


@pytest.fixture
def security_workflow() -> Dict[str, Any]:
    """Security scanning workflow fixture."""
    return {
        "id": "workflow_security",
        "name": "Security Scan",
        "description": "Automated security vulnerability scanning",
        "type": "security",
        "status": "active",
        "trigger": {"schedule": "0 0 * * 1", "push": {"branches": ["main"]}},  # Weekly + on push
        "jobs": {
            "security-scan": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"name": "Checkout", "uses": "actions/checkout@v3"},
                    {"name": "Run Trivy", "uses": "aquasecurity/trivy-action@master",
                     "with": {"scan-type": "fs", "format": "sarif", "output": "trivy-results.sarif"}},
                    {"name": "Run Snyk", "uses": "snyk/actions/python@master",
                     "with": {"args": "--sarif-file-output=snyk-results.sarif"}},
                    {"name": "Upload results", "uses": "github/codeql-action/upload-sarif@v2",
                     "with": {"sarif_file": "trivy-results.sarif"}},
                    {"name": "Upload Snyk results", "uses": "github/codeql-action/upload-sarif@v2",
                     "with": {"sarif_file": "snyk-results.sarif"}}
                ]
            }
        }
    }


@pytest.fixture
def business_workflow() -> Dict[str, Any]:
    """Business process workflow fixture."""
    return {
        "id": "workflow_business",
        "name": "Code Review Process",
        "description": "Business workflow for code review and approval",
        "type": "business_process",
        "status": "active",
        "steps": [
            {
                "id": "submit_pr",
                "name": "Submit Pull Request",
                "type": "manual",
                "assignee": "developer",
                "description": "Developer submits pull request with changes"
            },
            {
                "id": "initial_review",
                "name": "Initial Code Review",
                "type": "approval",
                "assignee": "tech_lead",
                "description": "Technical lead performs initial code review",
                "conditions": ["tests_pass", "linting_pass"]
            },
            {
                "id": "qa_review",
                "name": "QA Review",
                "type": "approval",
                "assignee": "qa_engineer",
                "description": "QA engineer performs testing and validation",
                "conditions": ["manual_tests_pass"]
            },
            {
                "id": "merge",
                "name": "Merge to Main",
                "type": "automatic",
                "description": "Automatically merge approved changes",
                "conditions": ["all_approvals_received", "ci_pass"]
            }
        ],
        "approvals_required": 2,
        "timeout_days": 7
    }


@pytest.fixture
def failed_workflow() -> Dict[str, Any]:
    """Failed workflow fixture."""
    return {
        "id": "workflow_failed",
        "name": "Failed CI Pipeline",
        "description": "Workflow that failed during execution",
        "type": "ci_cd",
        "status": "failed",
        "conclusion": "failure",
        "trigger": "push",
        "failed_step": "run-tests",
        "error_message": "Tests failed with exit code 1",
        "failure_details": {
            "step": "run-tests",
            "exit_code": 1,
            "logs": "============================= test session starts ==============================\nFAILED test_example.py::test_functionality - AssertionError: expected 5, got 3"
        },
        "retry_count": 2,
        "max_retries": 3
    }


@pytest.fixture
def workflow_with_artifacts() -> Dict[str, Any]:
    """Workflow with build artifacts."""
    return {
        "id": "workflow_artifacts",
        "name": "Build and Package",
        "description": "Workflow that produces build artifacts",
        "type": "build",
        "status": "completed",
        "artifacts": [
            {
                "name": "build-artifacts",
                "path": "dist/",
                "size": 2048576,  # 2MB
                "files": ["app-1.0.0.tar.gz", "app-1.0.0-py3-none-any.whl"],
                "download_url": "https://github.com/company/repo/actions/runs/123/artifacts/456"
            },
            {
                "name": "test-results",
                "path": "test-results/",
                "size": 102400,  # 100KB
                "files": ["junit.xml", "coverage.xml"],
                "download_url": "https://github.com/company/repo/actions/runs/123/artifacts/789"
            }
        ],
        "retention_days": 30
    }


@pytest.fixture
def workflow_with_matrix() -> Dict[str, Any]:
    """Workflow with matrix strategy for parallel execution."""
    return {
        "id": "workflow_matrix",
        "name": "Matrix Testing",
        "description": "Test across multiple environments",
        "type": "ci_cd",
        "strategy": {
            "matrix": {
                "python-version": ["3.8", "3.9", "3.10"],
                "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
                "exclude": [
                    {"python-version": "3.8", "os": "macos-latest"},
                    {"python-version": "3.10", "os": "windows-latest"}
                ]
            }
        },
        "jobs": {
            "test": {
                "runs-on": "${{ matrix.os }}",
                "strategy": {"matrix": "${{ fromJson(needs.setup.outputs.matrix) }}"},
                "steps": [
                    {"name": "Setup Python ${{ matrix.python-version }}",
                     "uses": "actions/setup-python@v4",
                     "with": {"python-version": "${{ matrix.python-version }}"}},
                    {"name": "Run tests", "run": "pytest"}
                ]
            }
        }
    }


@pytest.fixture
def workflow_templates() -> Dict[str, List[Dict[str, Any]]]:
    """Workflow templates organized by category."""
    return {
        "ci_cd": [ci_workflow()],
        "deployment": [deployment_workflow()],
        "security": [security_workflow()],
        "business": [business_workflow()],
        "build": [workflow_with_artifacts()]
    }


@pytest.fixture
def workflow_metrics() -> Dict[str, Any]:
    """Workflow performance metrics."""
    return {
        "total_workflows": 150,
        "successful_workflows": 135,
        "failed_workflows": 15,
        "success_rate": 0.9,
        "average_duration": 180.5,  # seconds
        "median_duration": 165.0,
        "longest_workflow": 450.2,
        "shortest_workflow": 45.8,
        "most_active_hour": 14,  # 2 PM
        "most_active_day": "Tuesday"
    }
