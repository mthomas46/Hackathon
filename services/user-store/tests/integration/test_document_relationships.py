"""Integration tests for document relationship processing."""

import pytest
from httpx import AsyncClient

from ..test_utils import get_test_client


@pytest.mark.asyncio
class TestDocumentRelationships:
    """Test automatic document relationship creation."""

    async def test_process_github_pr_relationships(self, client):
        """Test processing a GitHub PR and creating user relationships."""
        document_id = "github:pr:123"
        content = """
        This is a GitHub PR created by @octocat.
        Reviewed by @reviewer and assigned to @assignee.
        Also mentions @contributor in the discussion.
        """

        metadata = {
            "user": {"login": "octocat", "email": "octocat@github.com"},
            "assignees": [{"login": "assignee"}],
            "reviews": [{"user": {"login": "reviewer"}}]
        }

        response = await client.post(
            f"/documents/{document_id}/process-relationships",
            data={
                "content": content,
                "metadata": str(metadata).replace("'", '"'),
                "source_type": "github",
                "auto_create_users": True
            }
        )

        assert response.status_code == 200
        result = response.json()

        assert result["document_id"] == document_id
        assert result["source_type"] == "github"
        assert result["relationships_created"] > 0
        assert "octocat" in str(result["user_relationships"])

    async def test_process_jira_issue_relationships(self, client):
        """Test processing a Jira issue and creating user relationships."""
        document_id = "jira:issue:PROJ-123"
        content = """
        This issue was created by john.doe@example.com.
        Assigned to jane.smith@example.com for review.
        Comments from bob.wilson@example.com.
        """

        metadata = {
            "reporter": {"emailAddress": "john.doe@example.com", "displayName": "John Doe"},
            "assignee": {"emailAddress": "jane.smith@example.com", "displayName": "Jane Smith"},
            "comments": [
                {"author": {"emailAddress": "bob.wilson@example.com"}}
            ]
        }

        response = await client.post(
            f"/documents/{document_id}/process-relationships",
            data={
                "content": content,
                "metadata": str(metadata).replace("'", '"'),
                "source_type": "jira",
                "auto_create_users": True
            }
        )

        assert response.status_code == 200
        result = response.json()

        assert result["document_id"] == document_id
        assert result["relationships_created"] >= 3  # reporter, assignee, commenter

    async def test_query_document_users(self, client):
        """Test querying users related to a document."""
        # First create some relationships
        document_id = "test:doc:123"
        content = "Created by testuser@example.com"

        response = await client.post(
            f"/documents/{document_id}/process-relationships",
            data={
                "content": content,
                "metadata": "{}",
                "source_type": "common",
                "auto_create_users": True
            }
        )

        # Now query the users
        response = await client.get(f"/documents/{document_id}/users")
        assert response.status_code == 200

        result = response.json()
        assert result["document_id"] == document_id
        assert result["total"] >= 1

    async def test_query_user_documents(self, client):
        """Test querying documents related to a user."""
        # First create a user and relationship
        user_response = await client.post("/users", json={
            "email": "test@example.com",
            "username": "testuser",
            "display_name": "Test User"
        })
        user_id = user_response.json()["id"]

        # Create relationship manually for testing
        await client.post(f"/users/{user_id}/relationships", json={
            "document_id": "test:doc:456",
            "relationship_type": "owner",
            "access_level": "write"
        })

        # Query user's documents
        response = await client.get(f"/users/{user_id}/documents")
        assert response.status_code == 200

        result = response.json()
        assert result["user_id"] == user_id
        assert len(result["documents"]) > 0
