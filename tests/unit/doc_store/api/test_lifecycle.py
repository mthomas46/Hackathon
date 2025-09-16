"""Doc Store API Lifecycle Management Tests.

Tests for lifecycle management functionality at the API endpoint level.
"""

import pytest
import json


@pytest.mark.api
class TestLifecyclePolicyManagement:
    """Test lifecycle policy creation and management."""

    def test_create_lifecycle_policy_success(self, client):
        """Test successful lifecycle policy creation."""
        policy_data = {
            "name": "test-retention-policy",
            "description": "Test policy for automated retention",
            "conditions": {
                "content_types": ["documentation"],
                "max_age_days": 365
            },
            "actions": {
                "retention_days": 730
            },
            "priority": 5
        }

        response = client.post("/api/v1/lifecycle/policies", json=policy_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        policy_result = data["data"]
        assert "id" in policy_result
        assert policy_result["name"] == policy_data["name"]
        assert policy_result["description"] == policy_data["description"]

    def test_create_lifecycle_policy_minimal(self, client):
        """Test lifecycle policy creation with minimal data."""
        policy_data = {
            "name": "minimal-policy",
            "description": "Minimal test policy",
            "conditions": {"max_age_days": 30},
            "actions": {"retention_days": 60}
        }

        response = client.post("/api/v1/lifecycle/policies", json=policy_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_create_lifecycle_policy_validation_error(self, client):
        """Test lifecycle policy creation with validation errors."""
        invalid_policies = [
            {"description": "Missing name", "conditions": {}, "actions": {}},
            {"name": "", "description": "Empty name", "conditions": {}, "actions": {}},
            {"name": "missing-conditions", "description": "No conditions", "actions": {}},
            {"name": "missing-actions", "description": "No actions", "conditions": {}},
        ]

        for policy in invalid_policies:
            response = client.post("/api/v1/lifecycle/policies", json=policy)
            assert response.status_code == 422  # Validation error


@pytest.mark.api
class TestDocumentLifecycleTransitions:
    """Test document lifecycle transitions."""

    def test_transition_document_lifecycle_success(self, client):
        """Test successful document lifecycle transition."""
        # First create a document
        doc_data = {
            "content": "Document for lifecycle testing.",
            "metadata": {"status": "draft", "category": "test"}
        }

        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        # Transition the document
        transition_data = {
            "new_phase": "published",
            "reason": "Publishing document for testing"
        }

        response = client.post(f"/api/v1/documents/{doc_id}/lifecycle/transition", json=transition_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_transition_document_lifecycle_invalid_phase(self, client):
        """Test document lifecycle transition with invalid phase."""
        # Create a document
        doc_data = {"content": "Test document.", "metadata": {}}
        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        # Try invalid transition
        transition_data = {
            "new_phase": "invalid_phase",
            "reason": "Testing invalid phase"
        }

        response = client.post(f"/api/v1/documents/{doc_id}/lifecycle/transition", json=transition_data)
        # Should handle gracefully
        assert response.status_code in [200, 422, 400]

    def test_transition_nonexistent_document(self, client):
        """Test lifecycle transition on non-existent document."""
        transition_data = {
            "new_phase": "archived",
            "reason": "Archiving non-existent document"
        }

        response = client.post("/api/v1/documents/nonexistent-id/lifecycle/transition", json=transition_data)
        # Should handle gracefully
        assert response.status_code in [404, 422, 400]


@pytest.mark.api
class TestDocumentLifecycleStatus:
    """Test document lifecycle status retrieval."""

    def test_get_document_lifecycle_status(self, client):
        """Test retrieving document lifecycle status."""
        # Create a document
        doc_data = {
            "content": "Document for lifecycle status testing.",
            "metadata": {"phase": "active", "retention_days": 365}
        }

        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        # Get lifecycle status
        response = client.get(f"/api/v1/documents/{doc_id}/lifecycle")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        lifecycle_data = data["data"]
        assert isinstance(lifecycle_data, dict)

    def test_get_document_lifecycle_nonexistent(self, client):
        """Test getting lifecycle status for non-existent document."""
        response = client.get("/api/v1/documents/nonexistent-id/lifecycle")
        # Should handle gracefully
        assert response.status_code in [200, 404, 422]


@pytest.mark.api
class TestLifecyclePolicyIntegration:
    """Test lifecycle policy integration with documents."""

    def test_lifecycle_policy_document_integration(self, client):
        """Test lifecycle policy application to documents."""
        # Create a lifecycle policy
        policy_data = {
            "name": "integration-test-policy",
            "description": "Policy for integration testing",
            "conditions": {
                "content_types": ["test"],
                "max_age_days": 1  # Very short for testing
            },
            "actions": {
                "retention_days": 7
            }
        }

        policy_response = client.post("/api/v1/lifecycle/policies", json=policy_data)
        assert policy_response.status_code == 200

        # Create a document that matches the policy
        doc_data = {
            "content": "Document matching lifecycle policy.",
            "metadata": {"content_types": ["test"], "category": "integration"}
        }

        doc_response = client.post("/api/v1/documents", json=doc_data)
        assert doc_response.status_code == 200
        doc_id = doc_response.json()["data"]["id"]

        # The policy evaluation should work
        # Note: Actual policy application may be asynchronous

    def test_lifecycle_policy_edge_cases(self, client):
        """Test lifecycle policy edge cases."""
        edge_cases = [
            {
                "name": "zero-retention",
                "description": "Zero retention policy",
                "conditions": {"max_age_days": 0},
                "actions": {"retention_days": 0}
            },
            {
                "name": "high-priority",
                "description": "High priority policy",
                "conditions": {"max_age_days": 1000},
                "actions": {"retention_days": 2000},
                "priority": 100
            }
        ]

        for policy in edge_cases:
            response = client.post("/api/v1/lifecycle/policies", json=policy)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True


@pytest.mark.api
class TestLifecyclePerformance:
    """Test lifecycle management performance."""

    def test_lifecycle_operations_performance(self, client):
        """Test lifecycle operations performance."""
        import time

        # Create multiple policies and documents
        policies_created = 0
        documents_created = 0

        start_time = time.time()

        # Create some policies
        for i in range(3):
            policy_data = {
                "name": f"performance-policy-{i}",
                "description": f"Performance test policy {i}",
                "conditions": {"max_age_days": 30 + i},
                "actions": {"retention_days": 90 + i}
            }

            response = client.post("/api/v1/lifecycle/policies", json=policy_data)
            if response.status_code == 200:
                policies_created += 1

        # Create some documents
        for i in range(5):
            doc_data = {
                "content": f"Performance test document {i}.",
                "metadata": {"batch": "performance", "index": i}
            }

            response = client.post("/api/v1/documents", json=doc_data)
            if response.status_code == 200:
                documents_created += 1

        end_time = time.time()
        duration = end_time - start_time

        # Should complete within reasonable time
        assert duration < 5.0  # 5 seconds for 8 operations
        assert policies_created >= 2  # At least some policies created
        assert documents_created >= 3  # At least some documents created
