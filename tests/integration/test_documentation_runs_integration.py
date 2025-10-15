"""
Integration Tests for Documentation Run Management System

Tests the full stack: API endpoints, service layer, and database.
"""

import pytest
import httpx
import json
import time
from uuid import UUID
from datetime import datetime


# API base URL
API_URL = "http://localhost:8000"


class TestDocumentationRunsAPI:
    """Integration tests for Documentation Runs API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create an httpx client."""
        return httpx.Client(base_url=API_URL, timeout=30.0)
    
    @pytest.fixture
    async def test_run_id(self, client):
        """Create a test run and return its ID."""
        response = client.post(
            "/api/v1/documentation/runs",
            json={
                "name": "Integration Test Run",
                "description": "Test run for integration tests",
                "source_directory": "/app/tests",
                "output_format": "markdown",
                "response_size": "M",
                "tier": "docker",
                "num_passes": 2,
                "questions_per_pass": 3,
                "created_by": "integration_test"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        run_id = data["run_id"]
        
        yield run_id
        
        # Cleanup: Delete the test run
        try:
            client.delete(f"/api/v1/documentation/runs/{run_id}")
        except:
            pass
    
    def test_create_run(self, client):
        """Test creating a documentation run via API."""
        response = client.post(
            "/api/v1/documentation/runs",
            json={
                "name": "API Test Run",
                "description": "Testing API creation",
                "source_directory": "/app/src",
                "num_passes": 3,
                "questions_per_pass": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "run_id" in data
        assert data["name"] == "API Test Run"
        assert data["status"] == "pending"
        assert "message" in data
        
        # Cleanup
        run_id = data["run_id"]
        client.delete(f"/api/v1/documentation/runs/{run_id}")
    
    def test_create_run_validation(self, client):
        """Test run creation validation."""
        # Missing required fields
        response = client.post(
            "/api/v1/documentation/runs",
            json={
                "name": "Test"
                # Missing source_directory
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_list_runs(self, client, test_run_id):
        """Test listing documentation runs."""
        response = client.get("/api/v1/documentation/runs")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check that our test run is in the list
        run_ids = [run["id"] for run in data]
        assert test_run_id in run_ids
    
    def test_list_runs_with_filters(self, client):
        """Test listing runs with status filter."""
        response = client.get(
            "/api/v1/documentation/runs",
            params={"status": "completed", "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # All returned runs should be completed
        for run in data:
            assert run["status"] == "completed"
    
    def test_get_run_details(self, client, test_run_id):
        """Test getting run details."""
        response = client.get(f"/api/v1/documentation/runs/{test_run_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_run_id
        assert data["name"] == "Integration Test Run"
        assert data["status"] == "pending"
        assert data["num_passes"] == 2
        assert data["questions_per_pass"] == 3
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_get_run_not_found(self, client):
        """Test getting non-existent run."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/documentation/runs/{fake_id}")
        
        assert response.status_code == 404
    
    def test_get_run_invalid_id(self, client):
        """Test getting run with invalid UUID."""
        response = client.get("/api/v1/documentation/runs/invalid-uuid")
        
        assert response.status_code == 400
    
    def test_get_run_progress(self, client, test_run_id):
        """Test getting run progress."""
        response = client.get(f"/api/v1/documentation/runs/{test_run_id}/progress")
        
        assert response.status_code == 200
        # For a new run, progress might be None
        data = response.json()
        # Either None or a valid progress object
        assert data is None or "progress_percentage" in data
    
    def test_get_run_documents(self, client, test_run_id):
        """Test getting run documents."""
        response = client.get(f"/api/v1/documentation/runs/{test_run_id}/documents")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # New run should have no documents
        assert len(data) == 0
    
    def test_delete_run(self, client):
        """Test deleting a run."""
        # Create a run
        response = client.post(
            "/api/v1/documentation/runs",
            json={
                "name": "Run to Delete",
                "source_directory": "/app/src",
                "num_passes": 1,
                "questions_per_pass": 1
            }
        )
        
        assert response.status_code == 200
        run_id = response.json()["run_id"]
        
        # Delete the run
        response = client.delete(f"/api/v1/documentation/runs/{run_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert run_id in data["run_id"]
        
        # Verify it's deleted
        response = client.get(f"/api/v1/documentation/runs/{run_id}")
        assert response.status_code == 404
    
    def test_delete_run_not_found(self, client):
        """Test deleting non-existent run."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/api/v1/documentation/runs/{fake_id}")
        
        assert response.status_code == 404


class TestDocumentOperations:
    """Integration tests for document operations."""
    
    @pytest.fixture
    def client(self):
        """Create an httpx client."""
        return httpx.Client(base_url=API_URL, timeout=30.0)
    
    @pytest.fixture
    async def test_run_with_document(self, client):
        """Create a test run with a document."""
        # Note: This would require direct database access or a helper endpoint
        # For now, we'll test with existing data or mock
        pass
    
    def test_get_document_content(self, client):
        """Test getting document content."""
        # First, get a run with documents
        response = client.get("/api/v1/documentation/runs")
        
        if response.status_code == 200:
            runs = response.json()
            
            # Find a run with documents
            for run in runs:
                if run["total_documents"] > 0:
                    # Get documents from this run
                    doc_response = client.get(
                        f"/api/v1/documentation/runs/{run['id']}/documents"
                    )
                    
                    if doc_response.status_code == 200:
                        documents = doc_response.json()
                        
                        if documents:
                            # Get the first document's content
                            doc_id = documents[0]["id"]
                            content_response = client.get(
                                f"/api/v1/documentation/documents/{doc_id}"
                            )
                            
                            assert content_response.status_code == 200
                            doc_data = content_response.json()
                            
                            assert "content" in doc_data
                            assert "title" in doc_data
                            assert "filename" in doc_data
                            return
        
        # If no documents found, skip test
        pytest.skip("No documents available for testing")
    
    def test_get_document_not_found(self, client):
        """Test getting non-existent document."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/documentation/documents/{fake_id}")
        
        assert response.status_code == 404


class TestExportOperations:
    """Integration tests for export operations."""
    
    @pytest.fixture
    def client(self):
        """Create an httpx client."""
        return httpx.Client(base_url=API_URL, timeout=120.0)
    
    def test_export_run_as_zip(self, client):
        """Test exporting a run as ZIP."""
        # First, find a completed run with documents
        response = client.get(
            "/api/v1/documentation/runs",
            params={"status": "completed"}
        )
        
        if response.status_code == 200:
            runs = response.json()
            
            # Find a run with documents
            for run in runs:
                if run["total_documents"] > 0:
                    run_id = run["id"]
                    
                    # Export as ZIP
                    export_response = client.get(
                        f"/api/v1/documentation/runs/{run_id}/export/zip"
                    )
                    
                    assert export_response.status_code == 200
                    assert export_response.headers["content-type"] == "application/zip"
                    assert "content-disposition" in export_response.headers
                    assert len(export_response.content) > 0
                    return
        
        # If no completed runs with documents, skip test
        pytest.skip("No completed runs with documents available for testing")
    
    def test_export_run_not_found(self, client):
        """Test exporting non-existent run."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/documentation/runs/{fake_id}/export/zip")
        
        assert response.status_code == 404


class TestCompleteWorkflow:
    """Integration tests for complete workflows."""
    
    @pytest.fixture
    def client(self):
        """Create an httpx client."""
        return httpx.Client(base_url=API_URL, timeout=30.0)
    
    def test_full_run_lifecycle(self, client):
        """Test complete run lifecycle: create, update, complete, delete."""
        # 1. Create run
        create_response = client.post(
            "/api/v1/documentation/runs",
            json={
                "name": "Lifecycle Test Run",
                "description": "Testing full lifecycle",
                "source_directory": "/app/src",
                "num_passes": 2,
                "questions_per_pass": 2,
                "created_by": "lifecycle_test"
            }
        )
        
        assert create_response.status_code == 200
        run_id = create_response.json()["run_id"]
        
        # 2. Verify run exists
        get_response = client.get(f"/api/v1/documentation/runs/{run_id}")
        assert get_response.status_code == 200
        run_data = get_response.json()
        assert run_data["status"] == "pending"
        
        # 3. List runs and verify it appears
        list_response = client.get("/api/v1/documentation/runs")
        assert list_response.status_code == 200
        run_ids = [r["id"] for r in list_response.json()]
        assert run_id in run_ids
        
        # 4. Delete run
        delete_response = client.delete(f"/api/v1/documentation/runs/{run_id}")
        assert delete_response.status_code == 200
        
        # 5. Verify run is deleted
        verify_response = client.get(f"/api/v1/documentation/runs/{run_id}")
        assert verify_response.status_code == 404
    
    def test_pagination(self, client):
        """Test pagination of run listings."""
        # Get first page
        response1 = client.get(
            "/api/v1/documentation/runs",
            params={"limit": 5, "offset": 0}
        )
        
        assert response1.status_code == 200
        page1 = response1.json()
        
        # Get second page
        response2 = client.get(
            "/api/v1/documentation/runs",
            params={"limit": 5, "offset": 5}
        )
        
        assert response2.status_code == 200
        page2 = response2.json()
        
        # Pages should be different (if enough runs exist)
        if page1 and page2:
            page1_ids = {r["id"] for r in page1}
            page2_ids = {r["id"] for r in page2}
            assert page1_ids != page2_ids


class TestErrorHandling:
    """Integration tests for error handling."""
    
    @pytest.fixture
    def client(self):
        """Create an httpx client."""
        return httpx.Client(base_url=API_URL, timeout=30.0)
    
    def test_invalid_json(self, client):
        """Test API handles invalid JSON."""
        response = client.post(
            "/api/v1/documentation/runs",
            content="invalid json{",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code in [400, 422]
    
    def test_invalid_uuid_format(self, client):
        """Test API handles invalid UUID format."""
        response = client.get("/api/v1/documentation/runs/not-a-uuid")
        
        assert response.status_code == 400
    
    def test_missing_required_fields(self, client):
        """Test API validates required fields."""
        response = client.post(
            "/api/v1/documentation/runs",
            json={"name": "Test"}  # Missing source_directory
        )
        
        assert response.status_code == 422
    
    def test_invalid_field_values(self, client):
        """Test API validates field values."""
        response = client.post(
            "/api/v1/documentation/runs",
            json={
                "name": "Test",
                "source_directory": "/app",
                "num_passes": 0,  # Invalid: must be >= 1
                "questions_per_pass": 5
            }
        )
        
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

