"""Integration tests for SQLite persistence and expertise features."""

import pytest
import os
from httpx import AsyncClient

from ..test_utils import get_test_client


@pytest.mark.asyncio
class TestSQLitePersistenceAndExpertise:
    """Test SQLite database persistence and expertise inference."""

    @pytest.fixture(autouse=True)
    async def cleanup_db(self):
        """Clean up test database before each test."""
        db_path = "data/user_store.db"
        if os.path.exists(db_path):
            os.remove(db_path)
        yield
        if os.path.exists(db_path):
            os.remove(db_path)

    async def test_user_persistence(self, client):
        """Test that users are persisted to SQLite database."""
        # Create a user
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "display_name": "Test User"
        }

        response = await client.post("/users", json=user_data)
        assert response.status_code == 200

        user_id = response.json()["id"]

        # Retrieve the user
        response = await client.get(f"/users/{user_id}")
        assert response.status_code == 200

        retrieved_user = response.json()
        assert retrieved_user["email"] == user_data["email"]
        assert retrieved_user["username"] == user_data["username"]

    async def test_expertise_inference_from_document(self, client):
        """Test that user expertise is inferred from document processing."""
        # Create a user
        user_response = await client.post("/users", json={
            "email": "expert@example.com",
            "username": "ml_expert",
            "display_name": "ML Expert"
        })
        user_id = user_response.json()["id"]

        # Process documents with machine learning tags
        documents = [
            {
                "id": "doc1",
                "content": "Created by ml_expert",
                "tags": '["machine-learning", "python", "tensorflow"]'
            },
            {
                "id": "doc2",
                "content": "Updated by ml_expert",
                "tags": '["machine-learning", "neural-networks", "python"]'
            },
            {
                "id": "doc3",
                "content": "Reviewed by ml_expert",
                "tags": '["machine-learning", "deep-learning", "tensorflow"]'
            }
        ]

        # Process each document
        for doc in documents:
            response = await client.post(
                f"/documents/{doc['id']}/process-relationships",
                data={
                    "content": doc["content"],
                    "metadata": "{}",
                    "source_type": "github",
                    "document_tags": doc["tags"]
                }
            )
            assert response.status_code == 200

        # Check user expertise profile
        response = await client.get(f"/users/{user_id}/expertise")
        assert response.status_code == 200

        profile = response.json()
        assert "machine-learning" in profile["expertise_tags"]
        assert "python" in profile["expertise_tags"]
        assert profile["total_relationships"] >= 3

    async def test_find_users_by_expertise(self, client):
        """Test finding users by expertise topic."""
        # Create multiple users
        users = [
            {"email": "ml1@example.com", "username": "ml_user1", "display_name": "ML User 1"},
            {"email": "ml2@example.com", "username": "ml_user2", "display_name": "ML User 2"},
            {"email": "web@example.com", "username": "web_user", "display_name": "Web User"}
        ]

        user_ids = []
        for user_data in users:
            response = await client.post("/users", json=user_data)
            user_ids.append(response.json()["id"])

        # Create documents with different tags
        docs_data = [
            (user_ids[0], "doc_ml1", '["machine-learning", "python"]'),
            (user_ids[0], "doc_ml2", '["machine-learning", "tensorflow"]'),
            (user_ids[1], "doc_ml3", '["machine-learning", "pytorch"]'),
            (user_ids[2], "doc_web", '["javascript", "react"]')
        ]

        for user_id, doc_id, tags in docs_data:
            response = await client.post(
                f"/documents/{doc_id}/process-relationships",
                data={
                    "content": f"Created by user {user_id}",
                    "metadata": "{}",
                    "source_type": "github",
                    "document_tags": tags
                }
            )
            assert response.status_code == 200

        # Find users with machine learning expertise
        response = await client.get("/users/expertise/machine-learning")
        assert response.status_code == 200

        result = response.json()
        assert result["topic"] == "machine-learning"
        assert result["total"] >= 2  # At least 2 users should have ML expertise

        # Check that ML users are in results
        usernames = [user["username"] for user in result["users"]]
        assert "ml_user1" in usernames
        assert "ml_user2" in usernames

    async def test_contact_information_management(self, client):
        """Test user contact information management."""
        # Create a user
        user_response = await client.post("/users", json={
            "email": "contact@example.com",
            "username": "contact_user",
            "display_name": "Contact User"
        })
        user_id = user_response.json()["id"]

        # Update contact information
        contact_data = {
            "contact_email": "notifications@example.com",
            "contact_webhook": "https://hooks.slack.com/services/123/456/789",
            "contact_slack": "#dev-notifications"
        }

        response = await client.put(f"/users/{user_id}/contact", json=contact_data)
        assert response.status_code == 200

        # Retrieve contact information
        response = await client.get(f"/users/{user_id}/contacts")
        assert response.status_code == 200

        contacts = response.json()
        assert contacts["contacts"]["email"] == "notifications@example.com"
        assert contacts["contacts"]["webhook"] == contact_data["contact_webhook"]
        assert contacts["contacts"]["slack"] == contact_data["contact_slack"]

    async def test_relationship_persistence(self, client):
        """Test that document relationships are persisted."""
        # Create a user
        user_response = await client.post("/users", json={
            "email": "persist@example.com",
            "username": "persist_user",
            "display_name": "Persist User"
        })
        user_id = user_response.json()["id"]

        # Process a document
        doc_id = "persist_doc_123"
        response = await client.post(
            f"/documents/{doc_id}/process-relationships",
            data={
                "content": "Created by persist_user",
                "metadata": "{}",
                "source_type": "github",
                "document_tags": '["persistence", "testing"]'
            }
        )
        assert response.status_code == 200

        # Check document users
        response = await client.get(f"/documents/{doc_id}/users")
        assert response.status_code == 200

        result = response.json()
        assert result["total"] >= 1
        assert any(user["username"] == "persist_user" for user in result["users"])

        # Check user documents
        response = await client.get(f"/users/{user_id}/documents")
        assert response.status_code == 200

        documents = response.json()
        assert len(documents["documents"]) > 0
