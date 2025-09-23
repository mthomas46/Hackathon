"""Jira Fixtures - Specialized fixtures for Jira-related testing.

This module provides pytest fixtures for Jira data including issues, epics,
projects, and workflow states for comprehensive testing.
"""

import pytest
from typing import Dict, List, Any


@pytest.fixture
def sample_jira_ticket() -> Dict[str, Any]:
    """Sample Jira ticket fixture."""
    return {
        "id": "ISSUE-123",
        "key": "PROJ-123",
        "fields": {
            "summary": "Implement user authentication feature",
            "description": "As a user, I want to be able to log in to the system using my credentials.",
            "issuetype": {"name": "Story", "id": "10001"},
            "priority": {"name": "Medium", "id": "3"},
            "status": {"name": "In Progress", "id": "3"},
            "assignee": {
                "displayName": "John Doe",
                "name": "john.doe",
                "emailAddress": "john.doe@company.com"
            },
            "reporter": {
                "displayName": "Jane Smith",
                "name": "jane.smith",
                "emailAddress": "jane.smith@company.com"
            },
            "created": "2024-01-10T09:00:00.000Z",
            "updated": "2024-01-15T14:30:00.000Z",
            "labels": ["authentication", "frontend", "backend"],
            "components": [{"name": "Web Application", "id": "10000"}],
            "fixVersions": [{"name": "v2.1.0", "id": "10001"}],
            "comment": {
                "comments": [
                    {
                        "author": {"displayName": "John Doe"},
                        "body": "Started working on the authentication module.",
                        "created": "2024-01-12T10:00:00.000Z"
                    }
                ]
            }
        }
    }


@pytest.fixture
def sample_jira_epic() -> Dict[str, Any]:
    """Sample Jira epic fixture."""
    return {
        "id": "EPIC-456",
        "key": "PROJ-456",
        "fields": {
            "summary": "User Management System Overhaul",
            "description": "Complete redesign and implementation of the user management system.",
            "issuetype": {"name": "Epic", "id": "10000"},
            "priority": {"name": "High", "id": "2"},
            "status": {"name": "In Progress", "id": "3"},
            "assignee": {
                "displayName": "Project Manager",
                "name": "pm.user",
                "emailAddress": "pm@company.com"
            },
            "epicName": "User Management Overhaul",
            "epicColor": "blue",
            "issuesInEpic": [
                {"key": "PROJ-123", "summary": "Implement authentication"},
                {"key": "PROJ-124", "summary": "User profile management"},
                {"key": "PROJ-125", "summary": "Password reset functionality"}
            ],
            "created": "2024-01-01T00:00:00.000Z",
            "updated": "2024-01-15T12:00:00.000Z",
            "labels": ["epic", "user-management", "major-feature"],
            "storyPoints": 21
        }
    }


@pytest.fixture
def jira_bug_ticket() -> Dict[str, Any]:
    """Jira bug ticket fixture."""
    return {
        "id": "BUG-789",
        "key": "PROJ-789",
        "fields": {
            "summary": "Login button not responding on mobile devices",
            "description": """Steps to reproduce:
1. Open the app on mobile browser
2. Navigate to login page
3. Click login button
4. Button appears unresponsive

Expected: Login form should submit
Actual: Nothing happens

Environment: iOS Safari 16.0, Android Chrome 110.0""",
            "issuetype": {"name": "Bug", "id": "10004"},
            "priority": {"name": "High", "id": "2"},
            "status": {"name": "Open", "id": "1"},
            "assignee": None,  # Unassigned
            "labels": ["bug", "mobile", "ui", "regression"],
            "environment": "Mobile browsers (iOS Safari, Android Chrome)",
            "affectedVersions": [{"name": "v2.0.0", "id": "10000"}],
            "components": [{"name": "Frontend", "id": "10001"}]
        }
    }


@pytest.fixture
def jira_task_ticket() -> Dict[str, Any]:
    """Jira task ticket fixture."""
    return {
        "id": "TASK-101",
        "key": "PROJ-101",
        "fields": {
            "summary": "Update API documentation",
            "description": "Update the API documentation to reflect recent changes in the authentication endpoints.",
            "issuetype": {"name": "Task", "id": "10002"},
            "priority": {"name": "Low", "id": "4"},
            "status": {"name": "To Do", "id": "10000"},
            "assignee": {
                "displayName": "Technical Writer",
                "name": "tech.writer",
                "emailAddress": "writer@company.com"
            },
            "labels": ["documentation", "api", "maintenance"],
            "timeEstimate": 14400,  # 4 hours in seconds
            "timeSpent": 0,
            "worklog": []
        }
    }


@pytest.fixture
def jira_project() -> Dict[str, Any]:
    """Jira project fixture."""
    return {
        "id": "10000",
        "key": "PROJ",
        "name": "Product Development",
        "description": "Main product development project",
        "projectTypeKey": "software",
        "lead": {
            "displayName": "Project Lead",
            "name": "project.lead",
            "emailAddress": "lead@company.com"
        },
        "components": [
            {"name": "Frontend", "id": "10001"},
            {"name": "Backend", "id": "10002"},
            {"name": "Database", "id": "10003"}
        ],
        "versions": [
            {"name": "v1.0.0", "id": "10000", "released": True},
            {"name": "v2.0.0", "id": "10001", "released": True},
            {"name": "v2.1.0", "id": "10002", "released": False}
        ],
        "issueTypes": [
            {"name": "Epic", "id": "10000"},
            {"name": "Story", "id": "10001"},
            {"name": "Bug", "id": "10004"},
            {"name": "Task", "id": "10002"}
        ]
    }


@pytest.fixture
def jira_sprint() -> Dict[str, Any]:
    """Jira sprint fixture."""
    return {
        "id": 123,
        "name": "Sprint 15 - January 2024",
        "state": "active",
        "startDate": "2024-01-08T00:00:00.000Z",
        "endDate": "2024-01-21T23:59:59.000Z",
        "completeDate": None,
        "issues": [
            {"key": "PROJ-123", "summary": "Implement authentication", "status": "In Progress"},
            {"key": "PROJ-124", "summary": "User profile management", "status": "To Do"},
            {"key": "PROJ-125", "summary": "Password reset", "status": "Done"}
        ],
        "goal": "Complete user authentication features",
        "boardId": 1
    }


@pytest.fixture
def jira_workflow_states() -> List[Dict[str, Any]]:
    """Jira workflow states fixture."""
    return [
        {
            "id": "1",
            "name": "Open",
            "description": "Issue has been created",
            "statusCategory": {"name": "To Do", "colorName": "blue-gray"}
        },
        {
            "id": "3",
            "name": "In Progress",
            "description": "Work is actively being done",
            "statusCategory": {"name": "In Progress", "colorName": "yellow"}
        },
        {
            "id": "6",
            "name": "Resolved",
            "description": "Issue has been resolved",
            "statusCategory": {"name": "Done", "colorName": "green"}
        },
        {
            "id": "10000",
            "name": "Closed",
            "description": "Issue has been closed",
            "statusCategory": {"name": "Done", "colorName": "green"}
        }
    ]


@pytest.fixture
def jira_transition() -> Dict[str, Any]:
    """Jira workflow transition fixture."""
    return {
        "id": "21",
        "name": "Start Progress",
        "from": {"id": "1", "name": "Open"},
        "to": {"id": "3", "name": "In Progress"},
        "screen": {"id": "10000", "name": "Default Screen"},
        "rules": {
            "conditions": [
                {"type": "PermissionCondition", "permission": "WORK_ON_ISSUES"}
            ],
            "validators": [],
            "postFunctions": [
                {"type": "UpdateIssueStatusFunction"},
                {"type": "AssignToCurrentUserFunction"}
            ]
        }
    }


@pytest.fixture
def jira_comment() -> Dict[str, Any]:
    """Jira comment fixture."""
    return {
        "id": "10001",
        "author": {
            "displayName": "John Doe",
            "name": "john.doe",
            "emailAddress": "john.doe@company.com"
        },
        "body": """I've started working on this issue. Here's my progress:

✅ Completed authentication module setup
🔄 Working on user validation logic
❌ Need to implement password hashing

Will update again when I have more progress.""",
        "created": "2024-01-12T10:00:00.000Z",
        "updated": "2024-01-12T10:00:00.000Z",
        "visibility": None  # Public comment
    }


@pytest.fixture
def jira_attachment() -> Dict[str, Any]:
    """Jira attachment fixture."""
    return {
        "id": "10002",
        "filename": "error_screenshot.png",
        "author": {
            "displayName": "Jane Smith",
            "name": "jane.smith"
        },
        "created": "2024-01-12T11:30:00.000Z",
        "size": 2048576,  # 2MB
        "mimeType": "image/png",
        "content": "https://company.atlassian.net/secure/attachment/10002/error_screenshot.png",
        "thumbnail": "https://company.atlassian.net/secure/thumbnail/10002/error_screenshot.png"
    }


@pytest.fixture
def jira_search_results() -> List[Dict[str, Any]]:
    """Jira search results fixture."""
    return [
        {
            "key": "PROJ-123",
            "fields": {
                "summary": "Implement user authentication",
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "John Doe"},
                "priority": {"name": "Medium"},
                "issuetype": {"name": "Story"}
            }
        },
        {
            "key": "PROJ-456",
            "fields": {
                "summary": "Fix database connection issue",
                "status": {"name": "Open"},
                "assignee": None,
                "priority": {"name": "High"},
                "issuetype": {"name": "Bug"}
            }
        }
    ]


@pytest.fixture
def jira_board() -> Dict[str, Any]:
    """Jira board fixture."""
    return {
        "id": 1,
        "name": "Development Board",
        "type": "scrum",
        "project": {"key": "PROJ", "name": "Product Development"},
        "columns": [
            {"name": "To Do", "statuses": [{"id": "1"}]},
            {"name": "In Progress", "statuses": [{"id": "3"}]},
            {"name": "Done", "statuses": [{"id": "6"}, {"id": "10000"}]}
        ],
        "location": {"projectKey": "PROJ"},
        "filter": {"id": "10000", "name": "All Issues"}
    }
