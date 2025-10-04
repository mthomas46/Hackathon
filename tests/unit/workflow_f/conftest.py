"""
Pytest configuration and fixtures for Workflow F unit tests.
"""

import pytest
from typing import Dict, List, Any
from datetime import datetime


@pytest.fixture
def sample_github_pr() -> Dict[str, Any]:
    """Sample GitHub PR for testing user extraction."""
    return {
        "pr_number": "PR-123",
        "title": "Add Python backend API endpoints",
        "description": "Implements new REST API endpoints for user management. @john.doe please review the authentication logic. @sarah.chen can you check the database queries?",
        "author": "marcus.johnson",
        "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
        "created_at": "2025-01-01T10:00:00Z"
    }


@pytest.fixture
def sample_github_pr_no_mentions() -> Dict[str, Any]:
    """GitHub PR without any mentions."""
    return {
        "pr_number": "PR-456",
        "title": "Update documentation",
        "description": "Updated README with deployment instructions",
        "author": "emily.wu",
        "tech_stack": ["Markdown"],
        "created_at": "2025-01-02T14:00:00Z"
    }


@pytest.fixture
def sample_jira_ticket() -> Dict[str, Any]:
    """Sample Jira ticket for testing user extraction."""
    return {
        "key": "PROJ-789",
        "summary": "Implement React dashboard component",
        "description": "Need to create a new dashboard component. @david.kim has the designs. @alex.rivera can help with state management.",
        "assignee": "priya.patel",
        "tech_stack": ["React", "TypeScript", "Redux"],
        "priority": "High",
        "created_at": "2025-01-03T09:00:00Z"
    }


@pytest.fixture
def sample_confluence_doc() -> Dict[str, Any]:
    """Sample Confluence document for testing user extraction."""
    return {
        "doc_id": "CONF-101",
        "title": "Backend Architecture Guide",
        "content": {
            "text": "This guide covers our backend architecture. Contact @sarah.chen for questions about the API layer. @marcus.johnson maintains the database schemas."
        },
        "author": "jordan.lee",
        "tags": ["Architecture", "Backend", "Python", "Microservices"],
        "created_at": "2025-01-04T11:00:00Z"
    }


@pytest.fixture
def sample_documents_batch() -> List[Dict[str, Any]]:
    """Batch of documents for testing workflow execution."""
    return [
        {
            "type": "github_pr",
            "data": {
                "pr_number": "PR-100",
                "title": "Add authentication",
                "description": "@alice.cooper to review security",
                "author": "bob.martin",
                "tech_stack": ["Python", "JWT"]
            }
        },
        {
            "type": "jira",
            "data": {
                "key": "PROJ-200",
                "summary": "Fix bug in login",
                "description": "Bug reported by @charlie.davis",
                "assignee": "alice.cooper",
                "tech_stack": ["Python", "Flask"]
            }
        },
        {
            "type": "confluence",
            "data": {
                "doc_id": "CONF-300",
                "title": "API Documentation",
                "content": {"text": "Maintained by @bob.martin"},
                "author": "charlie.davis",
                "tags": ["API", "Python"]
            }
        }
    ]


@pytest.fixture
def sample_team_members() -> List[str]:
    """Sample team member names for testing."""
    return [
        "Sarah Chen",
        "Marcus Johnson",
        "Priya Patel",
        "Emily Wu",
        "David Kim",
        "Alex Rivera"
    ]


@pytest.fixture
def expected_user_extraction() -> Dict[str, Any]:
    """Expected user extraction result structure."""
    return {
        "username": "john.doe",
        "display_name": "John Doe",
        "documents_created": ["github_pr_PR-123"],
        "documents_updated": [],
        "documents_commented": [],
        "topics": ["Python", "FastAPI"],
        "services": [],
        "skills": [],
        "collaborators": ["sarah.chen", "marcus.johnson"],
        "total_interactions": 1,
        "expertise_score": 0.0
    }


@pytest.fixture
def sample_user_extractions() -> Dict[str, Any]:
    """Sample user extractions for SME testing."""
    return {
        "sarah.chen": {
            "username": "sarah.chen",
            "display_name": "Sarah Chen",
            "documents_created": ["doc1", "doc2", "doc3", "doc4", "doc5"],
            "documents_commented": ["doc6", "doc7"],
            "topics": ["Python", "Backend", "APIs", "Microservices"],
            "services": ["user-service", "auth-service"],
            "skills": ["Python Backend Development"],
            "total_interactions": 7,
            "expertise_score": 0.0
        },
        "john.doe": {
            "username": "john.doe",
            "display_name": "John Doe",
            "documents_created": ["doc8"],
            "documents_commented": ["doc9"],
            "topics": ["React", "Frontend"],
            "services": ["web-app"],
            "skills": ["React Development"],
            "total_interactions": 2,
            "expertise_score": 0.0
        },
        "marcus.johnson": {
            "username": "marcus.johnson",
            "display_name": "Marcus Johnson",
            "documents_created": ["doc10", "doc11", "doc12"],
            "documents_commented": [],
            "topics": ["Python", "Backend", "Database"],
            "services": ["database-service"],
            "skills": ["Database Design"],
            "total_interactions": 3,
            "expertise_score": 0.0
        }
    }


@pytest.fixture
def mock_workflow_f_result():
    """Mock WorkflowFResult for testing."""
    from services.project_planning_service.domain.services.workflow_f_user_intelligence import (
        WorkflowFResult, UserExtraction, SubjectMatterExpert
    )
    
    return WorkflowFResult(
        extracted_users={
            "user1": UserExtraction(username="user1", display_name="User One"),
            "user2": UserExtraction(username="user2", display_name="User Two")
        },
        subject_matter_experts=[
            SubjectMatterExpert(
                username="user1",
                display_name="User One",
                area_of_expertise="Python Backend",
                confidence=0.9,
                evidence=["10 documents", "Expert tag"],
                contact_priority="high"
            )
        ],
        potential_contacts={"Python": ["user1"], "Backend": ["user1", "user2"]},
        collaboration_graph={"user1": ["user2"], "user2": ["user1"]},
        expertise_map={"Python": ["user1"], "Backend": ["user1", "user2"]},
        total_users_extracted=2,
        total_documents_analyzed=10,
        execution_time=0.5
    )

